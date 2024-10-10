import asyncio
import cfscrape
import json
from codetiming import Timer
from datetime import datetime

from utils.functions import fahrenheit_to_celsius, find, parse_domain_name, kelvin_to_celsius
from utils.consts import WEATHERAPI, WEATHERBIT, TOMORROW, VISUALCROSSING, OPENMETEO, XWEATHER, OPENWEATHERMAP, FORECA, METEOSOURCE, METEOBLUE
from utils.consts import urls, date_pattern, today_date
from email_sender import send_email


# Функція для обчислення середніх значень параметрів погоди
def calculate_averages(data):
    sums = {"avgtemp_c": 0, "avghumidity": 0, "wind_mph": 0, "uv": 0}
    counts = {"avgtemp_c": 0, "avghumidity": 0, "wind_mph": 0, "uv": 0}

    for values in data.values():
        for key in sums.keys():
            value = values.get(key)
            if value is not None:
                sums[key] += value
                counts[key] += 1

    return {
        key: (round(sums[key] / counts[key], 2) if counts[key] > 0 else None)
        for key in sums.keys()
    }


# Основна функція для аналізу даних
def data_analytics(data):
    forecast_values = {
        "avgtemp_c": None,
        "avghumidity": None,
        "wind_mph": None,
        "uv": None
    }

    forecasts = {
        api: forecast_values.copy()
        for api in [
            WEATHERAPI, WEATHERBIT, TOMORROW, VISUALCROSSING, OPENMETEO,
            XWEATHER, OPENWEATHERMAP, FORECA, METEOSOURCE, METEOBLUE
        ]
    }

    # Отримання поточних даних з WEATHERAPI
    weatherapi = data.get(WEATHERAPI, {}).get("current", {})

    if weatherapi:
        forecasts[WEATHERAPI] = {
            "avgtemp_c": weatherapi["temp_c"],
            "avghumidity": weatherapi["humidity"],
            "wind_mph": weatherapi["wind_mph"],
            "uv": weatherapi["uv"],
        }

    # Отримання поточних даних з WEATHERBIT
    weatherbit = find(lambda d: today_date in d["datetime"],
                      data.get(WEATHERBIT, {}).get("data", []))
    if weatherbit:
        forecasts[WEATHERBIT] = {
            "avgtemp_c": weatherbit["temp"],
            "avghumidity": weatherbit["rh"],
            "wind_mph": weatherbit["wind_spd"],
            "uv": weatherbit["uv"]
        }

    # Отримання поточних даних з TOMORROW
    tomio = data.get(TOMORROW, {}).get("data", {}).get("values", [])

    if tomio:
        forecasts[TOMORROW] = {
            "avgtemp_c": tomio["temperature"],
            "avghumidity": tomio["humidity"],
            "wind_mph": tomio["windSpeed"],
            "uv": tomio["uvIndex"]
        }

    # Отримання поточних даних з VISUALCROSSING
    visualcrossing = data.get(VISUALCROSSING, {}).get("currentConditions", {})
    if visualcrossing:
        forecasts[VISUALCROSSING] = {
            "avgtemp_c": fahrenheit_to_celsius(visualcrossing["temp"]),
            "avghumidity": visualcrossing["humidity"],
            "wind_mph": visualcrossing["windspeed"],
            "uv": visualcrossing["uvindex"]
        }

    # Отримання поточних даних з OPENMETEO
    openmeteo = data.get(OPENMETEO, {}).get("current", {})
    if openmeteo:
        forecasts[OPENMETEO] = {
            "avgtemp_c": openmeteo["temperature_2m"],
            "avghumidity": openmeteo["relative_humidity_2m"],
            "wind_mph": openmeteo["wind_speed_10m"],
            "uv": openmeteo["uv_index"],
        }

    # Отримання поточних даних з XWEATHER
    xweather = find(
        lambda p: today_date in p["dateTimeISO"],
        data.get(XWEATHER, {}).get("response", [{}])[0].get("periods", []))
    if xweather:
        forecasts[XWEATHER] = {
            "avgtemp_c": xweather["temp"]["avgC"],
            "avghumidity": xweather["humidity"]["avg"],
            "wind_mph": xweather["windSpeed"]["avgMPH"],
            "uv": xweather["uvi"]["avg"]
        }

    # Отримання поточних даних з OPENWEATHERMAP
    openweathermap = data.get(OPENWEATHERMAP, {})

    if openweathermap:
        forecasts[OPENWEATHERMAP] = {
            "avgtemp_c": kelvin_to_celsius(openweathermap["main"]["temp"]),
            "avghumidity": openweathermap["main"]["humidity"],
            "wind_mph": openweathermap["wind"]["speed"],
            "uv": None,
        }

    # Отримання поточних даних з FORECA
    foreca = data.get(FORECA, {}).get("current", [])

    if foreca:
        forecasts[FORECA] = {
            "avgtemp_c": foreca["temperature"],
            "avghumidity": foreca["relHumidity"],
            "wind_mph": foreca["windSpeed"],
            "uv": foreca["uvIndex"]
        }

    # Отримання поточних даних з METEOSOURCE
    meteosource = find(
        lambda v: v["day"] == today_date,
        data.get(METEOSOURCE, {}).get("daily", {}).get("data", []))
    if meteosource:
        forecasts[METEOSOURCE] = {
            "avgtemp_c": meteosource["all_day"]["temperature"],
            "avghumidity": None,
            "wind_mph": meteosource["all_day"]["wind"]["speed"],
            "uv": None
        }

    # Отримання поточних даних з METEOBLUE
    meteoblue = data.get(METEOBLUE, {}).get("data_day", {})
    if meteoblue:
        meteoblue_idx = meteoblue["time"].index(
            find(lambda t: t == today_date, meteoblue["time"]))
        if meteoblue_idx is not None:
            forecasts[METEOBLUE] = {
                "avgtemp_c": meteoblue["temperature_instant"][meteoblue_idx],
                "avghumidity":
                meteoblue["relativehumidity_mean"][meteoblue_idx],
                "wind_mph": meteoblue["windspeed_mean"][meteoblue_idx],
                "uv": meteoblue["uvindex"][meteoblue_idx]
            }

    return {
        "created_at": datetime.now().strftime(f"{date_pattern} %H:%M"),
        "forecast_date": today_date,
        "forecasts": forecasts,
        "averages": calculate_averages(forecasts)
    }


def fetch_weather_data_cfscrape(url):
    try:
        scraper = cfscrape.create_scraper()
        response = scraper.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")
        send_email(
            "Weather API Failed",
            f"Failed to retrieve data from the API: {url}.\nDetails: {e}")
        return None


async def task(name, work_queue, weather_data):
    loop = asyncio.get_event_loop()
    while not work_queue.empty():
        url = await work_queue.get()
        domain = parse_domain_name(url)
        print(f"Task {name} getting resource: {domain}")
        try:
            data = await loop.run_in_executor(None,
                                              fetch_weather_data_cfscrape, url)
            if data is not None:
                weather_data[domain] = data
        except Exception as e:
            print(f"Task {name} encountered an error: {e}")


async def get_current_data():
    work_queue = asyncio.Queue()

    for url in urls:
        await work_queue.put(url)

    weather_data = {}

    with Timer(text="\nTotal elapsed time: {:.1f}"):
        await asyncio.gather(
            task("1", work_queue, weather_data),
            task("2", work_queue, weather_data),
            task("3", work_queue, weather_data),
        )

    with open("current_weather_data.json", "w") as json_file:
        json.dump(weather_data, json_file, indent=4)

    with open("current_weather_result.json", "w") as json_file:
        json.dump(data_analytics(weather_data), json_file, indent=4)
