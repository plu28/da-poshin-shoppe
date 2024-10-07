from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from src import log
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

    # Resetting global inventory table
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET red_ml = 0, green_ml = 0, blue_ml = 0, dark_ml = 0, gold = 100"))

    # Resetting catalog

    # Emptying out some tables
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("DELETE FROM cart_potions"))
        connection.execute(sqlalchemy.text("DELETE FROM carts"))
        connection.execute(sqlalchemy.text("DELETE FROM catalog"))

    return "OK"
