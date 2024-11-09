from fastapi import APIRouter
import sqlalchemy
from src.utils import database as db
from src.utils import log, jsonify, skutils
import json


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
        row['price'] = skutils.get_price(row['sku'])
        row['potion_type'] = skutils.get_type(row['sku'])
        rows.append(row)

    return json.loads(json.dumps(rows, default=str))
