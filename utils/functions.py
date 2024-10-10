from urllib.parse import urlparse


def find(pred, iter):
    return next(filter(pred, iter), None)


def parse_domain_name(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def kelvin_to_celsius(k):
    return round(k - 273.15, 2)


def fahrenheit_to_celsius(f):
    return round((f - 32) / 1.8, 2)
