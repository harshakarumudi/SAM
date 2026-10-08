from fastapi import APIRouter, Depends

from backend.app.core.security import get_current_user
from backend.app.models import User
from backend.app.schemas import WeatherResponse
from backend.app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", response_model=WeatherResponse)
async def get_farm_weather(
    current_user: User = Depends(get_current_user)
):
    """Retrieve farm local weather and forecast telemetry"""
    return await WeatherService.get_current_weather()
