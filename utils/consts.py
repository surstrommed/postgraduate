from datetime import datetime

(WEATHERAPI, WEATHERBIT, TOMORROW, VISUALCROSSING, OPENMETEO, XWEATHER,
 OPENWEATHERMAP, FORECA, METEOSOURCE,
 METEOBLUE) = ("api.weatherapi.com", "api.weatherbit.io", "api.tomorrow.io",
               "weather.visualcrossing.com", "api.open-meteo.com",
               "data.api.xweather.com", "api.openweathermap.org",
               "pfa.foreca.com", "www.meteosource.com", "my.meteoblue.com")

latitude = "49.9937757"
longitude = "36.2305267"
city_name = "Kharkiv"
date_pattern = "%Y-%m-%d"
today_date = (datetime.now()).strftime(date_pattern)

api_keys = {
    WEATHERAPI: "dd2d72258d944cd08e795814230512",
    WEATHERBIT: "9e8408390995414196d1eae79fafaffa",
    TOMORROW: "LYQ3tiHE7M2xn3j3yHYwPCajBH0rrK5V",
    VISUALCROSSING: "CYRJGNZWBHP58ALG4KXLTYP6Z",
    XWEATHER: "brQkc764mJqvFGKrQXrMp:lhraSAxY9UzqZuxAUrsLqjIXeDh02ghIIjrTJtFB",
    OPENWEATHERMAP: "c19bb0f5051b216d8460183a8dc7e8c9",
    FORECA:
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOlwvXC9wZmEuZm9yZWNhLmNvbVwvYXV0aG9yaXplXC90b2tlbiIsImlhdCI6MTcyODIxMzYxNCwiZXhwIjo5OTk5OTk5OTk5LCJuYmYiOjE3MjgyMTM2MTQsImp0aSI6IjUyZjI0Zjg2NTk2OTg3NDMiLCJzdWIiOiJjcm5nMjEyMSIsImZtdCI6IlhEY09oakM0MCtBTGpsWVR0amJPaUE9PSJ9.f38-KXiH7HPNyIVlIH_xVLW5sbkbWmscrYGsmx8l_AY",
    METEOSOURCE: "anwjt7y1f1c2fe6c0nl22d8sszfqgzrjug6dgg8b",
    METEOBLUE: "m04826tObTJzrLnU"
}

urls = [
    f"https://{WEATHERAPI}/v1/current.json?key={api_keys[WEATHERAPI]}&q={city_name}",
    f"https://{WEATHERBIT}/v2.0/current?city={city_name}&key={api_keys[WEATHERBIT]}",
    f"https://{TOMORROW}/v4/weather/realtime?location={latitude},{longitude}&apikey={api_keys[TOMORROW]}",
    f"https://{VISUALCROSSING}/VisualCrossingWebServices/rest/services/timeline?location={city_name}&contentType=json&key={api_keys[VISUALCROSSING]}",
    f"https://{OPENMETEO}/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,uv_index",
    f"https://{XWEATHER}/conditions/summary/{latitude},{longitude}?for=now&client_id={api_keys[XWEATHER].split(':')[0]}&client_secret={api_keys[XWEATHER].split(':')[1]}",
    f"https://{OPENWEATHERMAP}/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_keys[OPENWEATHERMAP]}",
    f"https://{FORECA}/api/v1/current/{longitude},{latitude}?stations=1&windunit=MS&lang=en&token={api_keys[FORECA]}",
    f"https://{METEOSOURCE}/api/v1/free/point?lat={latitude}&lon={longitude}&units=metric&sections=daily&key={api_keys[METEOSOURCE]}",
    f"https://{METEOBLUE}/packages/basic-day?apikey={api_keys[METEOBLUE]}&lat={latitude}&lon={longitude}&asl=113&format=json"
]
