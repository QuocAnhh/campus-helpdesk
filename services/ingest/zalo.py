from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import os
import hmac
import hashlib
import logging

app = FastAPI(title="Zalo Ingest")
logger = logging.getLogger(__name__)

# TODO: Define a proper Interaction model
class Interaction(BaseModel):
    user_id: str
    text: str

@app.post("/webhook/zalo")
async def zalo_webhook(interaction: Interaction, x_zalo_signature: str = Header(None)):
    zalo_secret = os.getenv("ZALO_SECRET")
    if zalo_secret:
        # Verify signature
        body_str = interaction.model_dump_json(exclude_unset=True)
        signature = hmac.new(
            key=zalo_secret.encode(),
            msg=body_str.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, x_zalo_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # TODO: Normalize to internal Interaction model and publish to NATS
    logger.info("Received interaction from Zalo user_id=%s", interaction.user_id)
    return {"status": "ok"}