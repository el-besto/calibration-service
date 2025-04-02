from fastapi import APIRouter, status

router = APIRouter()


@router.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}
