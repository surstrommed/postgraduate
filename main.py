import asyncio

from current_weather_handler import get_current_data

if __name__ == "__main__":
    asyncio.run(get_current_data())
