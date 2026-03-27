import requests
from config import logger, headers, url


def connect_to_api():
    stocks = ["TSLA", "MSFT", "GOOGL"]
    json_response = []

    for stock in stocks:
        querystring = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": stock,
            "outputsize": "compact",
            "interval": "5min",
            "datatype": "json"
        }

        try:
            print(f"Requesting {stock}...")

            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            print(f"{stock} status code:", response.status_code)

            response.raise_for_status()

            data = response.json()
            print(f"{stock} response keys:", data.keys())

            logger.info(f"{stock} successfully loaded")
            json_response.append(data)

        except requests.exceptions.RequestException as e:
            print(f"Request error for {stock}: {e}")
            logger.error(f"Error on stock {stock}: {e}")
            break

    print("Finished connect_to_api")
    print("json_response length:", len(json_response))
    return json_response


def extract_json(response):
    records = []

    print("Entering extract_json")
    #print("response is:", response)

    for data in response:
        if "Meta Data" not in data:
            print("Missing 'Meta Data' in response:", data)
            continue

        if "Time Series (5min)" not in data:
            print("Missing 'Time Series (5min)' in response:", data)
            continue

        symbol = data["Meta Data"]["2. Symbol"]

        for date_str, metrics in data["Time Series (5min)"].items():
            record = {
                "symbol": symbol,
                "date": date_str,
                "open": metrics["1. open"],
                "close": metrics["4. close"],
                "high": metrics["2. high"],
                "low": metrics["3. low"]
            }
            records.append(record)

    print("Total extracted records:", len(records))
    return records