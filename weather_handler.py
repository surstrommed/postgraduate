import asyncio
import aiohttp
import json
from codetiming import Timer
from urllib.parse import urlparse


def parse_domain_name(url):
    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc
    return domain_name


async def fetch_weather_data(session, url):
    async with session.get(url) as response:
        return await response.json()


async def task(name, work_queue, weather_data):
    async with aiohttp.ClientSession() as session:
        while not work_queue.empty():
            url = await work_queue.get()
            print(f"Task {name} getting resource: {parse_domain_name(url)}")
            weather_data[parse_domain_name(url)] = await fetch_weather_data(
                session, url)


async def main():
    work_queue = asyncio.Queue()

    latitude = "49.9914"
    longitude = "36.2354"
    city_name = "Kharkiv"

    for url in [
            f"https://api.weatherapi.com/v1/forecast.json?key=2557b57e1f404363adb214756241405&q={city_name}&aqi=no&days=2",  # Free trial 14 days
            f"https://api.weatherbit.io/v2.0/forecast/hourly?key=7a5ea7fa4cfb47638cdbd98ce9ccd003&lat={latitude}&lon={longitude}",  # Free trial 21 days with limits
            f"https://api.tomorrow.io/v4/weather/forecast?location={latitude},{longitude}&timesteps=1h&apikey=LYQ3tiHE7M2xn3j3yHYwPCajBH0rrK5V",  # Free permanent with limits
            f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city_name}?unitGroup=metric&key=CYRJGNZWBHP58ALG4KXLTYP6Z&contentType=json",  # Free trial 30 days
            f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_speed_80m",  # Free permanent
            f"https://data.api.xweather.com/forecasts?p={latitude},{longitude}&filter=1h&from=now&to=+1day&client_id=INUkq48ylUrRZ7heT4Ich&client_secret=GnCQTrSRHLedo91xQ25WeSudctsh1djrbf1v2Gl5",  # Free trial 30 days with limits
            f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&cnt=7&mode=json&appid=c19bb0f5051b216d8460183a8dc7e8c9",  # Free permanent with limits
            f"https://pfa.foreca.com/api/v1/forecast/daily/{longitude},{latitude}?windunit=MS&lang=en&token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOlwvXC9wZmEuZm9yZWNhLmNvbVwvYXV0aG9yaXplXC90b2tlbiIsImlhdCI6MTcxNTc4NjY2NSwiZXhwIjo5OTk5OTk5OTk5LCJuYmYiOjE3MTU3ODY2NjUsImp0aSI6IjVlN2ZmM2QzNTIzMGEyNTAiLCJzdWIiOiJjcm5nMjEyMSIsImZtdCI6IlhEY09oakM0MCtBTGpsWVR0amJPaUE9PSJ9.VHFuKTbxWyIPDVVeh3gEHcnt3M5wSLnQYm-Kbkf6C34",  # Free trial 30 days with limits
            f"https://www.meteosource.com/api/v1/free/point?lat={latitude}&lon={longitude}&units=metric&sections=daily&key=e8g5wrd30khvo5abpkuh3po8zn8eehfl05ol1vyc",  # Free permanent with limits
            f"https://my.meteoblue.com/packages/basic-1h_basic-day?apikey=m04826tObTJzrLnU&lat={latitude}&lon={longitude}&asl=279&format=json"  # Free permanent
    ]:
        await work_queue.put(url)

    weather_data = {}

    with Timer(text="\nTotal elapsed time: {:.1f}"):
        await asyncio.gather(
            task("1", work_queue, weather_data),
            task("2", work_queue, weather_data),
            task("3", work_queue, weather_data),
        )

    with open("weather_data.json", "w") as json_file:
        json.dump(weather_data, json_file, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
