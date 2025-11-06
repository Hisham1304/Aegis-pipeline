import requests
import os

AEGIS_API_KEY = os.getenv("AEGIS_API_KEY", "")
CONFIG_API_URL = os.getenv("CONFIG_API_URL", "")

def make_request(url):
    response = requests.get(url, timeout=10)
    return response.json() if response.status_code == 200 else None

if __name__ == "__main__":
    print("AEGIS_API_KEY present:", bool(AEGIS_API_KEY))
    print("CONFIG_API_URL:", CONFIG_API_URL)