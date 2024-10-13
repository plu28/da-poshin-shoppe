from fastapi import APIRouter
import sqlalchemy
from src.utils import database as db
from src.utils import log
from src.utils import jsonify

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # LOGGING
    log.post_log("/catalog")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM catalog WHERE quantity > 0"))
    row_list = result.fetchall()
    if (row_list == []):
        return []

    # Currently just selects the top 6 rows.
    # Future: implement better logic for selecting what potions need to be sold
    if len(row_list) < 6:
        return jsonify.rows_to_json(row_list)
    else:
        return jsonify.rows_to_json(row_list[0:6])
