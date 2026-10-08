import datetime
import math

import httpx

from backend.app.core.config import settings
from backend.app.schemas import WeatherResponse


class WeatherService:
    @staticmethod
    async def get_current_weather(location: str = None) -> WeatherResponse:
        loc = location or settings.WEATHER_LOCATION

        # If external API key is set, try querying live API
        if settings.WEATHER_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(
                        "https://api.openweathermap.org/data/2.5/weather",
                        params={
                            "q": loc,
                            "appid": settings.WEATHER_API_KEY,
                            "units": "metric"
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return WeatherResponse(
                            location=loc,
                            temperature=float(data["main"]["temp"]),
                            humidity=float(data["main"]["humidity"]),
                            condition=str(data["weather"][0]["main"]),
                            wind_speed_kmh=float(data["wind"]["speed"] * 3.6),
                            rainfall_probability=float(data.get("clouds", {}).get("all", 20.0)),
                            solar_radiation_w_m2=650.0,
                            timestamp=datetime.datetime.utcnow(),
                            is_simulated=False
                        )
            except Exception:
                # Fail safely to simulated model if network or API key fails
                pass

        # High-Fidelity Physics-based Environmental Weather Simulation
        now = datetime.datetime.utcnow()
        hour = now.hour + now.minute / 60.0

        # Diurnal temperature cycle: lowest at 05:00, peak at 14:00
        # Sinusoidal oscillation between 18°C and 31°C
        temp_cycle = 24.5 + 6.5 * math.sin((hour - 8.0) * math.pi / 12.0)
        temp_cycle = round(temp_cycle, 1)

        # Humidity is inversely related to temperature (typically 45% - 85%)
        humidity_cycle = 65.0 - 18.0 * math.sin((hour - 8.0) * math.pi / 12.0)
        humidity_cycle = round(max(30.0, min(95.0, humidity_cycle)), 1)

        # Solar radiation model (0 at night, up to 900 W/m2 at noon)
        if 6.0 <= hour <= 18.0:
            solar_rad = round(850.0 * math.sin((hour - 6.0) * math.pi / 12.0), 1)
        else:
            solar_rad = 0.0

        condition = "Sunny" if (6.0 <= hour <= 18.0 and humidity_cycle < 70) else ("Partly Cloudy" if humidity_cycle < 80 else "Overcast")
        rain_prob = 15.0 if condition == "Sunny" else (35.0 if condition == "Partly Cloudy" else 65.0)

        return WeatherResponse(
            location=loc,
            temperature=temp_cycle,
            humidity=humidity_cycle,
            condition=condition,
            wind_speed_kmh=12.4,
            rainfall_probability=rain_prob,
            solar_radiation_w_m2=solar_rad,
            timestamp=now,
            is_simulated=True
        )
