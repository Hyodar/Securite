import requests

def run_scan(url):
    url = requests.get(url)
    print(url)
    return url