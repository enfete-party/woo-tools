from dotenv import load_dotenv
from woocommerce import API
import os
import json
import pathlib
import sys
import csv
from dataclasses import dataclass, field, asdict

@dataclass
class OrderRecord:
    """ faire order record class """
    order_date: str
    order_number: str
    prefix: str
    brand_name: str
    product_name: str
    option_name: str
    sku: str
    gtin: str
    status: str
    quantity: str
    wholesale_price: str
    retail_price: str
    found: bool = field(init=False)
    updated: bool = field(init=False)

    @property
    def woo_sku(self) -> str | None:
        if self.prefix != '' and self.prefix != 'NO-PREFIX' and self.sku != '':
            return f"{self.prefix}-{self.sku}"

    def as_csv(self):
        values = [f"'{value}'" for name, value in vars(self).items() if not name.startswith('__')]
        return ",".join(values)

    def __post_init__(self):
        self.found = False
        self.updated = False


load_dotenv()

fieldnames = "order_date Order-Number Prefix Brand-Name Product-Name Option-Name SKU GTIN Status Quantity Wholesale-Price Retail-Price"
fieldnames = fieldnames.replace('-','_').lower()
fieldnames = fieldnames.split()

def csv_reader(filename):
    with open(filename, 'rt') as fp:
        csv_read = csv.DictReader(fp, fieldnames=fieldnames)
        for idx, row in enumerate(csv_read):
            if idx == 0:
                continue
            yield row

def log_record(record: OrderRecord, filename) -> None:
    with open(filename, 'at+') as fp:
        fp.write(f"{record.as_csv()}\n")


def init():
    not_found = pathlib.Path('not_found.csv')
    processed = pathlib.Path('processed.csv')

    if not_found.exists():
        not_found.unlink()

    if processed.exists():
        processed.unlink()

def main(filename):
    ck = os.environ.get('CONSUMER_KEY')
    cs = os.environ.get('CONSUMER_SECRET')
    init()
    woo = API(
        url="https://enfete.com",
        consumer_key=ck,
        consumer_secret=cs,
        version='wc/v3',
        timeout=10
    )

    for row in csv_reader(filename):
        record = OrderRecord(**row)

        if record.woo_sku is None:
            continue

        result = woo.get(f'products?sku={record.woo_sku}')

        if len(result.json()) == 0:
            log_record(record, "processed.csv")
            print(record.product_name, record.found)
            continue

        record.found = True
        product_data = result.json()

        if len(product_data) > 1:
            print(f"More than one result for {record.woo_sku}")

        data = { 'meta_data': [
            {
                'key': '_wc_gla_mpn',
                'value': record.sku
            },
            {
                'key': '_wc_gla_brand',
                'value': record.brand_name
            },
            {
                "key": "wpseo_global_identifier_values",
                "value": {
                    "gtin8": "",
                    "gtin12": "",
                    "gtin13": "",
                    "gtin14": "",
                    "isbn": "",
                    "mpn": record.sku
                }
            },
            {
                "key": "_wc_pinterest_google_product_category",
                "value": "Arts & Entertainment > Party & Celebration > Party Supplies"
            }
        ]}

        product_url = f"products/{product_data[0]['id']}"
        resp = woo.put(product_url, data)

        if resp.status_code >= 200 and resp.status_code < 300:
            record.updated = True

        log_record(record, "processed.csv")
        print(record.product_name, record.found, record.updated, resp.status_code, record.woo_sku, resp.url)

    #_wc_gla_brand

if __name__ == "__main__":
    filename = sys.argv[1]
    if not pathlib.Path(filename).exists():
        print("File couldnt be opened")
        exit()
    main(filename)
