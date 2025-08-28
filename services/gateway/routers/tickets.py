from fastapi import APIRouter, Request, HTTPException, Response
import httpx
import os
from typing import Iterable
import logging

router = APIRouter(prefix="/tickets", tags=["tickets"])

logger = logging.getLogger(__name__)

TICKET_URL = os.getenv("TICKET_URL", "http://ticket:8000")

# Hop-by-hop headers that must not be forwarded per RFC 7230
_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
}

# Reusable async client (will live for process lifetime; could be improved with lifespan event)
_http_client = httpx.AsyncClient(timeout=10.0)


def _filter_outgoing_headers(in_headers: Iterable[tuple[str, str]]) -> dict:
    """Allow-list / strip hop-by-hop headers. Forward only necessary ones."""
    allowed = {}
    for k, v in in_headers:
        kl = k.lower()
        if kl in _HOP_BY_HOP:
            continue
        # Minimal forward set; extend if needed
        if kl in {"authorization", "content-type", "accept", "accept-encoding"}:
            allowed[k] = v
    return allowed


def _filter_response_headers(in_headers: httpx.Headers) -> dict:
    filtered = {}
    for k, v in in_headers.items():
        kl = k.lower()
        if kl in _HOP_BY_HOP or kl == "content-length":
            continue
        filtered[k] = v
    return filtered


async def _proxy_request(request: Request, target_url: str) -> Response:
    method = request.method.upper()
    headers = _filter_outgoing_headers(request.headers.items())
    auth_present = 'Authorization' in headers or 'authorization' in headers
    auth_hdr = headers.get('Authorization') or headers.get('authorization')
    if auth_hdr:
        logger.debug("Proxy %s %s -> %s (auth len=%d prefix=%s)", method, request.url.path, target_url, len(auth_hdr), auth_hdr[:20])
    else:
        logger.debug("Proxy %s %s -> %s (no auth header)", method, request.url.path, target_url)

    kwargs = {}
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        body = await request.body()
        if body:
            kwargs["content"] = body
    try:
        resp = await _http_client.request(method=method, url=target_url, headers=headers, **kwargs)
    except httpx.RequestError as e:
        logger.error("Ticket service request error: %s", e)
        raise HTTPException(status_code=503, detail=f"Ticket service unavailable: {e}")

    if resp.status_code in (401, 403):
        # Log body for debugging auth issues (avoid logging secrets)
        logger.warning(
            "Upstream ticket service returned %s for %s %s. Response body: %s",
            resp.status_code, method, target_url, resp.text[:300]
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_response_headers(resp.headers),
        media_type=resp.headers.get("content-type")
    )

# --- Specific routes MUST be declared before the catch-all to avoid being shadowed ---
@router.get("/my")
async def get_my_tickets(request: Request):
    """Get current user's tickets (maps to ticket service /my-tickets)."""
    target_url = f"{TICKET_URL}/my-tickets"
    if request.url.query:
        target_url += f"?{request.url.query}"
    return await _proxy_request(request, target_url)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@router.api_route("", methods=["GET", "POST"])
async def proxy_to_ticket_service(request: Request, path: str = ""):
    """Proxy all /tickets requests to ticket service (sanitized)."""
    # Path rewrite safeguards
    rewritten_path = path
    if path == "my":  # Should already be handled above, but safety net
        rewritten_path = "my-tickets"

    if rewritten_path:
        target_url = f"{TICKET_URL}/tickets/{rewritten_path}" if rewritten_path not in {"my-tickets"} else f"{TICKET_URL}/{rewritten_path}"
    else:
        target_url = f"{TICKET_URL}/tickets"

    # Add query parameters
    if request.url.query:
        target_url += f"?{request.url.query}"

    return await _proxy_request(request, target_url)