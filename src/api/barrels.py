from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import json
from json import dumps
from src import database as db
from src import global_inventory as gi
from src import log
import numpy as np
from . import bottler

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int


@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    log.post_log(f'/barrels/deliver/{order_id}')
    global_inventory = gi.GlobalInventory().retrieve() # Get current inventory state

    barrel_cost = 0
    red = global_inventory.red_ml
    green = global_inventory.green_ml
    blue = global_inventory.blue_ml
    dark = global_inventory.dark_ml

    for barrel in barrels_delivered:
        barrel_cost += (barrel.price * barrel.quantity)
        if barrel.potion_type == [1,0,0,0]:
            red += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0,1,0,0]:
            green += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0,0,1,0]:
            blue += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0,0,0,1]:
            dark += (barrel.ml_per_barrel * barrel.quantity)

    # Get new gold after purchasing barrels
    new_gold = global_inventory.gold - barrel_cost

    # Update global inventory
    # TODO: Handle updates in global_inventory.py at some point
    update_query = sqlalchemy.text("UPDATE global_inventory SET gold = :gold, red_ml = :red_ml, green_ml = :green_ml, blue_ml = :blue_ml, dark_ml = :dark_ml")
    with db.engine.begin() as connection:
        connection.execute(update_query,
            {
                'gold': new_gold,
                'red_ml': red,
                'green_ml': green,
                'blue_ml': blue,
                'dark_ml': dark
            }
        )

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # Log endpoint
    log.post_log('barrels/plan')

    # Log everything roxanne is selling
    log_query = sqlalchemy.text("INSERT INTO roxanne (sku, ml_per_barrel, potion_type, price, quantity) VALUES (:sku, :ml_per_barrel, :potion_type, :price, :quantity)")
    with db.engine.begin() as connection:
        for barrel in wholesale_catalog:
            connection.execute(log_query,
                {
                    'sku': barrel.sku,
                    'ml_per_barrel': barrel.ml_per_barrel,
                    'potion_type': barrel.potion_type,
                    'price': barrel.price,
                    'quantity': barrel.quantity
                }
            )

    global_inventory = gi.GlobalInventory().retrieve() # Getting current state of inventory
    current_gold = global_inventory.gold

    # TODO: Some logic for handling barrel purchasing
    # We dont want to buy more barrels then we can afford
    # Barrels calls bottler plan and figures out what the current plan is
    # Buys enough barrels for this bottling to occur

    bottle_plan = bottler.get_bottle_plan() # Get bottler plan
    red_need = green_need = blue_need = dark_need = 0 # Count up exactly how much of each type I need to buy

    # Adding up the total amount of ml quantities using numpy vector operations
    np_arr = np.array([0,0,0,0])
    for purchase in bottle_plan:
        np_arr += purchase['quantity'] * np.array(purchase['potion_type'])

    # TODO: FINISH BARREL LOGIC!
    return "OK"
