import requests

url_web_example = 'https://graphhopper.com/maps/?profile=%s&layer=Omniscale'


url_for_address = ('https://nominatim.openstreetmap.org/search?'
                   'q=%s&accept-language=ru-Ru&format=json&limit=1&addressdetails=1')


url_for_reverse = ('https://nominatim.openstreetmap.org/reverse?'
                   'lat=%s&lon=%s&accept-language=ru-Ru&format=json&limit=1&addressdetails=1')


def check_address(address: str):
    req = requests.get(url_for_address % address)
    return req.json()


def reverse_address(lat: str, lon: str):
    req = requests.get(url_for_reverse % (lat, lon))
    return req.json()
