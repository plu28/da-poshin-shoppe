from fastapi import APIRouter
import sqlalchemy
from src import database as db
from src import log
from src import jsonify

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # LOGGING
    log.post_log("/catalog")

    # grabs the green potions from the database
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM catalog WHERE quantity > 0"))
    row_list = result.fetchall()

    # Currently just selects the top 6 rows.
    # Future: implement better logic for selecting what potions need to be sold
    if len(row_list) < 6:
        return jsonify.rows_to_json(row_list)
    else:
        return jsonify.rows_to_json(row_list[0:6])
