from dotenv import load_dotenv
from woocommerce import API
import os
import json
import pathlib
import sys
import csv
from dataclasses import dataclass, field, asdict


load_dotenv()

def main(sku):
    ck = os.environ.get('CONSUMER_KEY')
    cs = os.environ.get('CONSUMER_SECRET')
    woo = API(
        url="https://staging2.enfete.com",
        consumer_key=ck,
        consumer_secret=cs,
        version='wc/v3',
        timeout=10
    )

    result = woo.get(f'products?sku={sku}')

    if len(result.json()) != 0:
        print(json.dumps(result.json(), indent=2))

if __name__ == "__main__":
    sku = sys.argv[1]
    main(sku)

