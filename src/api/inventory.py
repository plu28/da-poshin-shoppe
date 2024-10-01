from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db
router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    # LOGGING
    with db.engine.begin() as connection:
        log = connection.execute(sqlalchemy.text(f"INSERT INTO logs (endpoint) VALUES ('/inventory/audit')"))

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    row = result.fetchone()
    number_of_potions = row.num_green_potions
    ml_in_barrels = row.num_green_ml
    gold = row.gold

    return {"number_of_potions": number_of_potions, "ml_in_barrels": ml_in_barrels, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """
    # LOGGING
    with db.engine.begin() as connection:
        log = connection.execute(sqlalchemy.text(f"INSERT INTO logs (endpoint) VALUES ('/inventory/plan')"))

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """
    # LOGGING
    with db.engine.begin() as connection:
        log = connection.execute(sqlalchemy.text(f"INSERT INTO logs (endpoint) VALUES ('/inventory/deliver/{order_id}')"))

    return "OK"
