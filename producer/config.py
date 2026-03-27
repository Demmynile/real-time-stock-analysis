import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

BASE_URL = "alpha-vantage.p.rapidapi.com"
url = f"https://{BASE_URL}/query"

api_key = os.getenv("API_KEY")

print("Loaded API key:", api_key is not None)
print("URL:", url)

headers = {
    "x-rapidapi-key": api_key,
    "x-rapidapi-host": BASE_URL
}