from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
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
    response = "OK"

    # Resetting global inventory table
    with db.engine.begin() as connection:
        update = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions=0, num_green_ml=0, gold=100"))

    # Emptying out carts
    with db.engine.begin() as connection:
        update = connection.execute(sqlalchemy.text("DELETE FROM carts"))

    # LOGGING
    with db.engine.begin() as connection:
        log = connection.execute(sqlalchemy.text(f"INSERT INTO logs (endpoint, request, response) VALUES ('/reset', '{{}}', '{{\"response\":\"{response}\"}}')"))

    return response
