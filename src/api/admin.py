from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src.utils import database as db
from src.utils import log
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    log.post_log('/reset')
    reset_gold = sqlalchemy.text('''
        INSERT INTO gold_ledger (gold_change)
        SELECT (SELECT -(gold) + 100 FROM view_gold) AS gold_change
    ''')

    reset_ml = sqlalchemy.text('''
        INSERT INTO ml_ledger (red, green, blue, dark)
        SELECT
            (SELECT -red FROM view_ml) AS red,
            (SELECT -green FROM view_ml) AS green,
            (SELECT -blue FROM view_ml) AS blue,
            (SELECT -dark FROM view_ml) AS dark
    ''')

    reset_poshin = sqlalchemy.text('''
        INSERT INTO poshin_ledger (sku, quantity)
        SELECT sku, -(quantity) FROM view_catalog
    ''')

    reset_carts = sqlalchemy.text('''
        TRUNCATE TABLE cart_potions, completed_carts, carts
    ''')

    try:
        with db.engine.begin() as connection:
            connection.execute(reset_gold)
            connection.execute(reset_ml)
            connection.execute(reset_poshin)
            connection.execute(reset_carts)

    except Exception as e:
        print(e)
        return "ERROR"
    return "OK"
