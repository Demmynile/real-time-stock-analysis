from extract import connect_to_api, extract_json
from config import logger
from producer_setup import init_producer, topic
import time


def main():
    response = connect_to_api()

    data = extract_json(response)

    producer = init_producer()

    logger.info(f"{len(data)} records extracted")

    seen_symbols = []

    for stock in data:
        result = {
            'date': stock['date'],
            'symbol': stock['symbol'],
            'open': stock['open'],
            'low': stock['low'],
            'high': stock['high'],
            'close': stock['close']
        }

        producer.send(topic, result)

        # Add delay (simulate streaming)
        time.sleep(0.5)

        if stock["symbol"] not in seen_symbols:
            logger.info(f"{stock['symbol']} data successfully processed")
            seen_symbols.append(stock["symbol"])

    producer.flush()
    producer.close()
    print(f"Data sent to {topic} topic")

    return None


if __name__ == "__main__":
    main()