from fastapi import APIRouter

router = APIRouter()


@router.get("/health", status_code=200)
async def health_check():
    """
    Health check endpoint to verify service operational status.
    """
    return {"status": "healthy"}
