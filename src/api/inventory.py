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

# Retrieving gold
@router.get("/audit")
def get_inventory():
    """ """
    log.post_log('/inventory/audit')

    get_audit = sqlalchemy.text('''
        SELECT
            (SELECT gold FROM view_gold) AS gold,
            (SELECT red FROM view_ml) AS red,
            (SELECT green FROM view_ml) AS green,
            (SELECT blue FROM view_ml) AS blue,
            (SELECT dark FROM view_ml) AS dark,
            (SELECT COALESCE(SUM(quantity)) FROM view_catalog) AS total_poshins
    ''')

    try:
        with db.engine.begin() as connection:
            audit = connection.execute(get_audit).fetchone()
            if audit == None:
                raise Exception("Audit returned no rows")
    except Exception as e:
        print(e)
        return {"error": e}

    return {
        "number_of_potions": audit.total_poshins,
        "ml_in_barrels": audit.red + audit.green + audit.blue + audit.dark,
        "gold": audit.gold
    }

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
