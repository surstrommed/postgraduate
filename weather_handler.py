import asyncio
import aiohttp
import json
from codetiming import Timer
from urllib.parse import urlparse
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge

# Встановлення констант з URL API сервісів
(WEATHERAPI, WEATHERBIT, TOMORROW, VISUALCROSSING, OPENMETEO, XWEATHER,
 OPENWEATHERMAP, FORECA, METEOSOURCE,
 METEOBLUE) = ("api.weatherapi.com", "api.weatherbit.io", "api.tomorrow.io",
               "weather.visualcrossing.com", "api.open-meteo.com",
               "data.api.xweather.com", "api.openweathermap.org",
               "pfa.foreca.com", "www.meteosource.com", "my.meteoblue.com")


# Функція для знаходження першого елементу в ітераторі, що задовольняє умову pred
def find(pred, iter):
    return next(filter(pred, iter), None)


# Функція для отримання доменного імені з URL
def parse_domain_name(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


# Функція для обчислення середніх значень параметрів погоди
def calculate_averages(data):
    sums = {"temp_c": 0, "humidity": 0, "pressure": 0, "wind_speed": 0}
    counts = {"temp_c": 0, "humidity": 0, "pressure": 0, "wind_speed": 0}

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


# Функція для перетворення Кельвінів в Цельсії
def kelvin_to_celsius(k):
    return round(k - 273.15, 2)


# Основна функція для аналізу даних
def data_analytics(data):
    date_format = "%Y-%m-%d"
    offset = int(datetime.now().astimezone().utcoffset().seconds /
                 3600)  # Визначення зсуву часової зони
    today = datetime.today()
    tomorrow = today + timedelta(1)
    str_tom = tomorrow.strftime(date_format)  # Завтрашня дата в форматі рядка
    iso_tom_1 = f"{today.strftime(date_format)}T{24 - offset}:00:00Z"  # Формат ISO для завтрашнього дня
    iso_tom_2 = f"{tomorrow.strftime(date_format)}T00:00"  # Альтернативний формат ISO
    forecast_timestamp = int(
        datetime.strptime(
            str_tom,
            date_format).timestamp())  # Тимчасова мітка для завтрашнього дня

    # Шаблон для зберігання значень прогнозу
    forecast_values = {
        "temp_c": None,
        "humidity": None,
        "pressure": None,
        "wind_speed": None
    }

    # Створення словника для зберігання прогнозів з різних API
    forecasts = {
        api: forecast_values.copy()
        for api in [
            WEATHERAPI, WEATHERBIT, TOMORROW, VISUALCROSSING, OPENMETEO,
            XWEATHER, OPENWEATHERMAP, FORECA, METEOSOURCE, METEOBLUE
        ]
    }

    # Отримання прогнозу з WEATHERAPI
    weatherapi = find(
        lambda d: d["date"] == str_tom,
        data.get(WEATHERAPI, {}).get("forecast", {}).get("forecastday", []))
    if weatherapi:
        weatherapi_hour = find(lambda h: h["time_epoch"] == forecast_timestamp,
                               weatherapi["hour"])
        if weatherapi_hour:
            forecasts[WEATHERAPI] = {
                "temp_c": weatherapi_hour["temp_c"],
                "humidity": weatherapi_hour["humidity"],
                "pressure": weatherapi_hour["pressure_mb"],
                "wind_speed": weatherapi_hour["wind_mph"]
            }

    # Отримання прогнозу з WEATHERBIT
    weatherbit = find(lambda d: d["ts"] == forecast_timestamp,
                      data.get(WEATHERBIT, {}).get("data", []))
    if weatherbit:
        forecasts[WEATHERBIT] = {
            "temp_c": weatherbit["temp"],
            "humidity": weatherbit["rh"],
            "pressure": weatherbit["pres"],
            "wind_speed": weatherbit["wind_spd"]
        }

    # Отримання прогнозу з TOMORROW
    tomio = find(lambda d: d["time"] == iso_tom_1,
                 data.get(TOMORROW, {}).get("timelines", {}).get("hourly", []))
    if tomio:
        forecasts[TOMORROW] = {
            "temp_c": tomio["values"]["temperature"],
            "humidity": tomio["values"]["humidity"],
            "pressure": tomio["values"]["pressureSurfaceLevel"],
            "wind_speed": tomio["values"]["windSpeed"]
        }

    # Отримання прогнозу з VISUALCROSSING
    visualcrossing_day = find(
        lambda d: d["datetimeEpoch"] == forecast_timestamp,
        data.get(VISUALCROSSING, {}).get("days", []))
    if visualcrossing_day:
        visualcrossing = find(
            lambda h: h["datetimeEpoch"] == forecast_timestamp,
            visualcrossing_day["hours"])
        if visualcrossing:
            forecasts[VISUALCROSSING] = {
                "temp_c": visualcrossing["temp"],
                "humidity": visualcrossing["humidity"],
                "pressure": visualcrossing["pressure"],
                "wind_speed": visualcrossing["windspeed"]
            }

    # Отримання прогнозу з OPENMETEO
    openmeteo = data.get(OPENMETEO, {}).get("hourly", {})
    if openmeteo:
        openmeteo_idx = openmeteo["time"].index(
            find(lambda d: d == iso_tom_2, openmeteo["time"]))
        if openmeteo_idx is not None:
            forecasts[OPENMETEO] = {
                "temp_c": openmeteo["temperature_2m"][openmeteo_idx],
                "humidity": openmeteo["relative_humidity_2m"][openmeteo_idx],
                "pressure": openmeteo["pressure_msl"][openmeteo_idx],
                "wind_speed": openmeteo["wind_speed_10m"][openmeteo_idx]
            }

    # Отримання прогнозу з XWEATHER
    xweather = find(
        lambda p: p["timestamp"] == forecast_timestamp,
        data.get(XWEATHER, {}).get("response", [{}])[0].get("periods", []))
    if xweather:
        forecasts[XWEATHER] = {
            "temp_c": xweather["tempC"],
            "humidity": xweather["humidity"],
            "pressure": xweather["pressureMB"],
            "wind_speed": xweather["windSpeedKPH"]
        }

    # Отримання прогнозу з OPENWEATHERMAP
    openweathermap = find(lambda v: v["dt"] == forecast_timestamp,
                          data.get(OPENWEATHERMAP, {}).get("list", []))
    if openweathermap:
        forecasts[OPENWEATHERMAP] = {
            "temp_c": kelvin_to_celsius(openweathermap["main"]["temp"]),
            "humidity": openweathermap["main"]["humidity"],
            "pressure": openweathermap["main"]["pressure"],
            "wind_speed": openweathermap["wind"]["speed"]
        }

    # Отримання прогнозу з FORECA
    foreca = find(lambda f: iso_tom_2 in f["time"],
                  data.get(FORECA, {}).get("forecast", []))
    if foreca:
        forecasts[FORECA] = {
            "temp_c": foreca["temperature"],
            "wind_speed": foreca["windSpeed"]
        }

    # Отримання прогнозу з METEOSOURCE
    meteosource = find(
        lambda v: v["date"] == f"{iso_tom_2}:00",
        data.get(METEOSOURCE, {}).get("hourly", {}).get("data", []))
    if meteosource:
        forecasts[METEOSOURCE] = {
            "temp_c": meteosource["temperature"],
            "wind_speed": meteosource["wind"]["speed"]
        }

    # Отримання прогнозу з METEOBLUE
    meteoblue = data.get(METEOBLUE, {}).get("data_1h", {})
    if meteoblue:
        meteoblue_idx = meteoblue["time"].index(
            find(lambda t: t == iso_tom_2.replace("T", " "),
                 meteoblue["time"]))
        if meteoblue_idx is not None:
            forecasts[METEOBLUE] = {
                "temp_c": meteoblue["temperature"][meteoblue_idx],
                "humidity": meteoblue["relativehumidity"][meteoblue_idx],
                "pressure": meteoblue["sealevelpressure"][meteoblue_idx],
                "wind_speed": meteoblue["windspeed"][meteoblue_idx]
            }

    return {
        "created_at": datetime.now().strftime(f"{date_format} %H:%M"),
        "forecast_date": f"{tomorrow.strftime(date_format)} 00:00",
        "forecasts": forecasts,
        "averages": calculate_averages(forecasts)
    }  # Повернення зібраних прогнозів


# Функція для завантаження даних з API асинхронно
async def fetch_weather_data(session, url):
    try:
        async with session.get(url) as response:
            return await response.json()  # Повернення JSON відповіді
    except aiohttp.ClientError as e:
        print(f"Error fetching data from {url}: {e}"
              )  # Оброблення помилки в разі невдалого з'єднання
        return None


# Функція для виконання завдання з черги
async def task(name, work_queue, weather_data):
    async with aiohttp.ClientSession() as session:  # Створення HTTP сесії
        while not work_queue.empty():  # Поки черга не порожня
            url = await work_queue.get()  # Отримання URL з черги
            domain = parse_domain_name(url)  # Отримання доменного імені
            print(f"Task {name} getting resource: {domain}")
            try:
                data = await fetch_weather_data(session,
                                                url)  # Завантаження даних
                if data is not None:
                    weather_data[domain] = data
            except Exception as e:
                print(f"Task {name} encountered an error: {e}")


# Функція для тестування моделі на історичних даних
def backtest(weather, model, predictors, start=3650, step=90):
    all_predictions = []  # Список для зберігання всіх прогнозів

    for i in range(start, weather.shape[0], step):
        train = weather.iloc[:i, :]  # Тренувальні дані
        test = weather.iloc[i:(i + step), :]  # Тестові дані

        model.fit(train[predictors], train["target"])  # Тренування моделі

        preds = model.predict(test[predictors])  # Прогнози
        preds = pd.Series(preds, index=test.index)
        combined = pd.concat([test["target"], preds], axis=1)

        combined.columns = [
            "actual", "prediction"
        ]  # Колонки для відображення фактичного та пронгозованого значень

        combined["diff"] = (combined["prediction"] - combined["actual"]).abs(
        )  # Колонка різниці між фактичним та прогнозованим прогнозами

        all_predictions.append(combined)  # Додавання прогнозів до списку

    return pd.concat(all_predictions)


# Функція для обчислення процентної різниці між двома значеннями
def pct_diff(old, new):
    return (new - old) / old


# Функція для обчислення ковзного середнього
def compute_rolling(weather, horizon, col):
    label = f"rolling_{horizon}_{col}"

    weather[label] = weather[col].rolling(horizon).mean()  # Ковзне середнє
    weather[f"{label}_pct"] = pct_diff(weather[label],
                                       weather[col])  # Зміщення середнього

    return weather


# Функція для обчислення розширеного середнього
def expand_mean(df):
    return df.expanding(1).mean()


# Функція для аналізу історичних даних
def historical_analytics():
    wh = pd.read_csv(
        "historical_data.csv",
        index_col="DATE")  # Зчитування даних з файлу з історичними даними

    null_pct = wh.apply(pd.isnull).sum() / wh.shape[
        0]  # Розрахунок відсотка пропущених значень для кожного стовпця

    valid_columns = wh.columns[
        null_pct
        < .05]  # Вибір стовпців, де відсоток пропущених значень менше 5%

    wh = wh[valid_columns].copy()  # Копіювання даних з обраними стовпцями

    wh.columns = wh.columns.str.lower(
    )  # Перетворення назв стовпців на нижній регістр

    wh = wh.ffill()  # Заповнення пропущених значень попередніми значеннями
    wh.apply(pd.isnull).sum()  # Перевірка наявності пропущених значень

    wh.index = pd.to_datetime(wh.index)  # Перетворення індексу на datetime
    wh.index.year.value_counts().sort_index(
    )  # Підрахунок кількості записів по роках

    wh["target"] = wh.shift(
        -1
    )["tmax"]  # Додавання стовпця 'target', що містить значення 'tmax' зсунуто на один день назад
    wh = wh.ffill()  # Заповнення пропущених значень

    rr = Ridge(alpha=.1,
               random_state=42)  # Ініціалізація моделі Ridge регресії

    predictors = wh.columns[~wh.columns.isin([
        "target", "name", "station"
    ])]  # Визначення предикторів (виключаючи 'target', 'name', 'station')

    predictions = backtest(
        wh, rr, predictors)  # Проведення тестування на історичних даних

    # Додавання ковзних середніх для вибраних горизонтів
    rolling_horizons = [3, 14]
    for horizon in rolling_horizons:
        for col in ["tmax", "tmin", "prcp"]:
            wh = compute_rolling(wh, horizon, col)

    # Видалення перших 14 рядків для уникнення впливу початкових значень ковзних середніх
    wh = wh.iloc[14:, :]
    wh = wh.fillna(0)  # Заповнення залишкових пропущених значень нулями

    # Додавання середніх значень за місяцями та днями року для вибраних стовпців
    for col in ["tmax", "tmin", "prcp"]:
        wh[f"month_avg_{col}"] = wh[col].groupby(
            wh.index.month, group_keys=False).apply(expand_mean)
        wh[f"day_avg_{col}"] = wh[col].groupby(
            wh.index.day_of_year, group_keys=False).apply(expand_mean)

    # Повторне визначення предикторів та проведення тестування
    predictors = wh.columns[~wh.columns.isin(["target", "name", "station"])]
    predictors = backtest(wh, rr, predictors)

    # Побудова гістограми різниць між фактичними та передбаченими значеннями
    diff_counts = predictions["diff"].round().value_counts().sort_index()
    diff_counts.plot(kind="bar")

    plt.xlabel("Difference")
    plt.ylabel("Count")
    plt.title("Distribution of prediction differences")
    plt.show()

    return predictions


async def main():
    # Місцеположення для прогнозування даних
    latitude = "40.6446"
    longitude = "-73.7822"
    city_name = "NY"

    # Описання API ключів
    api_keys = {
        WEATHERAPI: "b9d01894e3734279ac2115841241606",
        WEATHERBIT: "3310924f07094f37a030c9e90b7bf4f2",
        TOMORROW: "LYQ3tiHE7M2xn3j3yHYwPCajBH0rrK5V",
        VISUALCROSSING: "CYRJGNZWBHP58ALG4KXLTYP6Z",
        XWEATHER:
        "a3vnGSNKLiVOewXw2ViNX:KqFgnhNWL1xvcPP6WM2yUArm7G8kdFhYhyCeMzLM",
        OPENWEATHERMAP: "c19bb0f5051b216d8460183a8dc7e8c9",
        FORECA:
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOlwvXC9wZmEuZm9yZWNhLmNvbVwvYXV0aG9yaXplXC90b2tlbiIsImlhdCI6MTcxODU0MTY4MiwiZXhwIjo5OTk5OTk5OTk5LCJuYmYiOjE3MTg1NDE2ODIsImp0aSI6ImM4NzU0M2U5ZmJmMGFhNjciLCJzdWIiOiJwb2pvaGE5Mzg5IiwiZm10IjoiWERjT2hqQzQwK0FMamxZVHRqYk9pQT09In0.j6m_NM8dRHbaBeiomTBURTtJ9JNKBXmrLLF_sfhRbfE",
        METEOSOURCE: "e8g5wrd30khvo5abpkuh3po8zn8eehfl05ol1vyc",
        METEOBLUE: "m04826tObTJzrLnU"
    }

    # Описання API посилань
    urls = [
        f"https://{WEATHERAPI}/v1/forecast.json?key={api_keys[WEATHERAPI]}&q={city_name}&aqi=no&days=2",
        f"https://{WEATHERBIT}/v2.0/forecast/hourly?key={api_keys[WEATHERBIT]}&lat={latitude}&lon={longitude}",
        f"https://{TOMORROW}/v4/weather/forecast?location={latitude},{longitude}&timesteps=1h&apikey={api_keys[TOMORROW]}",
        f"https://{VISUALCROSSING}/VisualCrossingWebServices/rest/services/timeline/{city_name}?unitGroup=metric&key={api_keys[VISUALCROSSING]}&contentType=json",
        f"https://{OPENMETEO}/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_speed_80m",
        f"https://{XWEATHER}/forecasts?p={latitude},{longitude}&filter=1h&from=now&to=+1day&client_id={api_keys[XWEATHER].split(':')[0]}&client_secret={api_keys[XWEATHER].split(':')[1]}",
        f"https://{OPENWEATHERMAP}/data/2.5/forecast?lat={latitude}&lon={longitude}&cnt=7&mode=json&appid={api_keys[OPENWEATHERMAP]}",
        f"https://{FORECA}/api/v1/forecast/hourly/{longitude},{latitude}?windunit=MS&lang=en&token={api_keys[FORECA]}",
        f"https://{METEOSOURCE}/api/v1/free/point?lat={latitude}&lon={longitude}&units=metric&sections=hourly&key={api_keys[METEOSOURCE]}",
        f"https://{METEOBLUE}/packages/basic-1h_basic-day?apikey={api_keys[METEOBLUE]}&lat={latitude}&lon={longitude}&asl=279&format=json"
    ]

    work_queue = asyncio.Queue()  # Створення черги

    for url in urls:
        await work_queue.put(url)  # Додавання URL до черги

    weather_data = {}  # Словник для зберігання даних погоди

    # Виконання асинхронних завдань для отримання метеоданих з таймером
    with Timer(text="\nTotal elapsed time: {:.1f}"):
        await asyncio.gather(
            task("1", work_queue, weather_data),
            task("2", work_queue, weather_data),
            task("3", work_queue, weather_data),
        )

    # Збереження даних погоди у json файл
    with open("weather_data.json", "w") as json_file:
        json.dump(weather_data, json_file, indent=4)

    # Збереження отриманної аналітики по погодним даним у json файл
    with open("weather_analytics.json", "w") as json_file:
        json.dump(data_analytics(weather_data), json_file, indent=4)

    # Виконання функції для отримання прогнозу погодних умов з історичних даних
    predictions = historical_analytics()
    print(predictions)  # Виведення прогнозованих даних


# Запуск виконання програми
if __name__ == "__main__":
    asyncio.run(main())
