from fastapi import APIRouter, Depends
import sys
sys.path.append('/app')

import schemas
import security

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(security.get_current_user)):
    """
    Get the details of the currently authenticated user.
    """
    return current_user 