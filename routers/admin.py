from fastapi import APIRouter, Depends, Header, HTTPException, status, Body
from typing import Annotated
from config.settings import settings
from models.selectors import SelectorConfig

router = APIRouter(prefix="/admin", tags=["Admin"])

# --- Security Dependency ---
async def verify_admin_key(x_api_key: Annotated[str, Header()]):
    """Checks if the X-API-Key header matches our secret key."""
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid Admin API Key"
        )
    return True

# --- Admin Endpoints ---
@router.get(
    "/selectors", 
    response_model=SelectorConfig,
    dependencies=[Depends(verify_admin_key)]
)
async def get_selectors():
    """
    Fetches the current selector configuration from the database.
    If none exists, it returns the default values.
    """
    config = await SelectorConfig.find_one()
    if config is None:
        return SelectorConfig() # Return a new instance with defaults
    return config

@router.post(
    "/selectors", 
    response_model=SelectorConfig,
    dependencies=[Depends(verify_admin_key)]
)
async def update_selectors(selectors: SelectorConfig = Body(...)):
    """
    Updates (or creates) the selector configuration in the database.
    We assume there is only one config document.
    """
    # Find the existing config, or create a new one if it's the first time
    existing_config = await SelectorConfig.find_one()
    
    if existing_config is None:
        # No config exists, create a new one
        new_config = SelectorConfig(**selectors.model_dump())
        await new_config.insert()
        return new_config
    else:
        # Config exists, update it
        # We use model_update to apply the changes from the request body
        existing_config.model_update(selectors)
        await existing_config.save()
        return existing_config