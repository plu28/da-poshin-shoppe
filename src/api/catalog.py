from fastapi import APIRouter
import sqlalchemy
from src.utils import database as db
from src.utils import log
from src.utils import jsonify
import re
import json
from src import prices


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # LOGGING
    log.post_log("/catalog")

    # Select my top 6 largest quantity potions
    retrieve_catalog_query = sqlalchemy.text('''
        SELECT
            sku,
            sku AS name,
            CAST(SUM(quantity) AS INTEGER) AS quantity
        FROM poshin_ledger
        GROUP BY sku
        HAVING SUM(quantity) > 0
        LIMIT 6
    ''')
    try:
        with db.engine.begin() as connection:
            catalog_result = connection.execute(retrieve_catalog_query)
    except Exception as e:
        print(e)
        return []

    rows = []
    for row in catalog_result.mappings():
        row = dict(row)
        row['price'] = get_price(row['sku'])
        row['potion_type'] = get_type(row['sku'])
        rows.append(row)

    return json.loads(json.dumps(rows, default=str))

def get_price(sku: str):
    price = 0
    for ml_quantity, color in re.findall(r"(\d+)([a-z]+)", sku):
        ml_quantity = int(ml_quantity) # typecasting to int
        if color == "red":
            price += ml_quantity * prices.RED_PRICE_PER_ML
        elif color == "green":
            price += ml_quantity * prices.GREEN_PRICE_PER_ML
        elif color == "blue":
            price += ml_quantity * prices.BLUE_PRICE_PER_ML
        elif color == "dark":
            price += ml_quantity * prices.DARK_PRICE_PER_ML
    return price

def get_type(sku: str):
    type = [0,0,0,0]
    for ml_quantity, color in re.findall(r"(\d+)([a-z]+)", sku):
        ml_quantity = int(ml_quantity) # typecasting to int
        if color == "red":
            type[0] = ml_quantity
        elif color == "green":
            type[1] = ml_quantity
        elif color == "blue":
            type[2] = ml_quantity
        elif color == "dark":
            type[3] = ml_quantity
    return type
