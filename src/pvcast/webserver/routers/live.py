"""Contains the FastAPI router for the /live endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/{test}")
async def test_function():
    """Test function to check if the server is running."""
    return {"foo": "bar"}
