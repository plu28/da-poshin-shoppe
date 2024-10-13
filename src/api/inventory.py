from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src.utils import database as db
from src.tables import global_inventory as gi
from src.utils import log

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    log.post_log('/inventory/audit')

    # Counts up all the potion stock in the catalog
    with db.engine.begin() as connection:
        quantities = connection.execute(sqlalchemy.text(f"SELECT quantity FROM catalog"))
    quantity_rows = quantities.fetchall()
    potion_stock = 0
    for quantity_row in quantity_rows:
        potion_stock += quantity_row.quantity

    global_inventory = gi.GlobalInventory().retrieve()
    ml_in_barrels = global_inventory.red_ml + global_inventory.green_ml + global_inventory.blue_ml + global_inventory.dark_ml # Counts up all the ml

    return {"number_of_potions": potion_stock, "ml_in_barrels": ml_in_barrels, "gold": global_inventory.gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """
    log.post_log('/inventory/plan')

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
    log.post_log('/inventory/deliver/{order_id}')
    return "OK"
