from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# initialize FastMCP server
server = FastMCP("weather")

NWS_API_URL = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def get_nws_data(url: str) -> dict[str, Any] | None:
    """ call nws api """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, headers=headers, timeout=30.0)
            res.raise_for_status()
            return res.json()
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            return None
        
def format_alert(feature: dict) -> str:
    """ format alert """
    props = feature["properties"]
    return f"""

            Event: {props.get('event', 'N/A')}
            Area: {props.get('areaDesc', 'N/A')}
            Severity: {props.get('severity', 'N/A')}
            Description: {props.get('description', 'N/A')}
            Instructions: {props.get('instruction', 'N/A')}
        """

@server.tool()
async def get_alerts(state: str) -> str:
    """ get weather alerts for a US state
    
    Args:
        state: Two-letter state code (e.g. CA, NY, TX)
    """

    url = f"{NWS_API_URL}/alerts/active/area/{state}"
    data = await get_nws_data(url)
    if not data or "features" not in data:
        return "No alerts found or invalid state code."
    
    if not data["features"]:
        return "No active alerts for your state"
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n".join(alerts)

@server.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """ get weather forecast for a location
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """

    points_url = f"{NWS_API_URL}/points/{latitude},{longitude}"
    points_data = await get_nws_data(points_url)
    if not points_data:
        return "Unable to fetch forecast data for this location."
    
    # get forecast url from points data
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await get_nws_data(forecast_url)
    if not forecast_data:
        return "Unable to fetch forecast data for this location."
    
    # format the periods into readable forecast
    periods = forecast_data["properties"]["periods"]
    forecast = []
    for period in periods[:3]:
        forecast.append(f"""
            Name: {period["name"]}
            Temperature: {period["temperature"]} {period["temperatureUnit"]}
            Wind: {period["windSpeed"]} {period["windDirection"]}
            Short Forecast: {period["shortForecast"]}
            Detailed Forecast: {period["detailedForecast"]}
        """)
    return "\n".join(forecast)

if __name__ == "__main__":
    server.run(transport='stdio')