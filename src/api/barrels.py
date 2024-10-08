from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import json
from json import dumps
from src import database as db
from src import global_inventory as gi
from src import catalog_table as cat
from src import roxanne as rox
from src import log
from src import strategy as strat
import re


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
    log.post_log('/barrels/plan')
    global_inventory = gi.GlobalInventory().retrieve() # Getting current state of inventory

    if (global_inventory.gold < 60):
        return "NO BARREL PURCHASE"

    # Drop what roxanne sold in the last barrels call
    # with db.engine.begin() as connection:
    #     connection.execute(sqlalchemy.text("DELETE FROM roxanne"))

    # Log everything roxanne is selling
    # log_query = sqlalchemy.text("INSERT INTO roxanne (sku, ml_per_barrel, potion_type, price, quantity) VALUES (:sku, :ml_per_barrel, :potion_type, :price, :quantity)")
    # with db.engine.begin() as connection:
    #     for barrel in wholesale_catalog:
    #         connection.execute(log_query,
    #             {
    #                 'sku': barrel.sku,
    #                 'ml_per_barrel': barrel.ml_per_barrel,
    #                 'potion_type': barrel.potion_type,
    #                 'price': barrel.price,
    #                 'quantity': barrel.quantity
    #             }
    #         )

    new_strat = strat.Strategy().retrieve_as_dict()
    while(sum(new_strat.values()) != 0):
        print(new_strat)
        barrels_im_buying = []
        price = 0

        red_need = green_need = blue_need = dark_need = 0 # Count up exactly how much of each type I need to buy
        # subtract any pre-existing stock
        red_need -= global_inventory.red_ml
        green_need -= global_inventory.green_ml
        blue_need -= global_inventory.blue_ml
        dark_need -= global_inventory.dark_ml

        # Get how many ml we need for the strategy
        for sku, quantity in new_strat.items():
            # Since sku corresponds to potion makeup, I can use regex
            for ml_quantity, color in re.findall("(\d+)([a-z]+)", sku):
                ml_quantity = int(ml_quantity) # typecasting to int
                if color == "red":
                    red_need += ml_quantity * quantity
                elif color == "green":
                    green_need += ml_quantity * quantity
                elif color == "blue":
                    blue_need += ml_quantity * quantity
                elif color == "dark":
                    dark_need += ml_quantity * quantity

        print(f"[{red_need},{green_need},{blue_need},{dark_need}]")
        # Greedy algorithm. If I don't have enough gold, adjust the strategy by removing 1 potion and trying again
        # NOTE: This is an approximate solution which means its sub-optimal. There will be better barrel purchasing combinations
        # TODO: Rewrite to be more maintainable

        # Sort offerings by ml (larger barrels are better value)
        if red_need > 0:
            with db.engine.begin() as connection:
                red_barrels = connection.execute(sqlalchemy.text("SELECT * FROM roxanne WHERE potion_type = ARRAY[1,0,0,0] ORDER BY ml_per_barrel DESC")).fetchall()
                for red_barrel in red_barrels:
                    # print(f"{red_barrel.sku}")
                    if red_barrel.ml_per_barrel <= red_need:
                        quantity = red_need // red_barrel.ml_per_barrel
                        if (quantity > red_barrel.quantity):
                            quantity = red_barrel.quantity
                        red_need -= red_barrel.ml_per_barrel * quantity
                        price += red_barrel.price * quantity
                        barrels_im_buying.append({'sku':red_barrel.sku, 'quantity': quantity})
        if green_need > 0:
            with db.engine.begin() as connection:
                green_barrels = connection.execute(sqlalchemy.text("SELECT * FROM roxanne WHERE potion_type = ARRAY[0,1,0,0] ORDER BY ml_per_barrel DESC")).fetchall()
                for green_barrel in green_barrels:
                    if green_barrel.ml_per_barrel <= green_need:
                        quantity = green_need // green_barrel.ml_per_barrel
                        if (quantity > green_barrel.quantity):
                            quantity = green_barrel.quantity
                        green_need -= green_barrel.ml_per_barrel * quantity
                        price += green_barrel.price * quantity
                        barrels_im_buying.append({'sku':green_barrel.sku, 'quantity': quantity})
        if blue_need > 0:
            with db.engine.begin() as connection:
                blue_barrels = connection.execute(sqlalchemy.text("SELECT * FROM roxanne WHERE potion_type = ARRAY[0,0,1,0] ORDER BY ml_per_barrel DESC")).fetchall()
                for blue_barrel in blue_barrels:
                    if blue_barrel.ml_per_barrel <= blue_need:
                        quantity = blue_need // blue_barrel.ml_per_barrel
                        if (quantity > blue_barrel.quantity):
                            quantity = blue_barrel.quantity
                        blue_need -= blue_barrel.ml_per_barrel * quantity
                        price += blue_barrel.price * quantity
                        barrels_im_buying.append({'sku':blue_barrel.sku, 'quantity': quantity})
        if dark_need > 0:
            with db.engine.begin() as connection:
                dark_barrels = connection.execute(sqlalchemy.text("SELECT * FROM roxanne WHERE potion_type = ARRAY[0,0,0,1] ORDER BY ml_per_barrel DESC")).fetchall()
                for dark_barrel in dark_barrels:
                    if dark_barrel.ml_per_barrel <= dark_need:
                        quantity = dark_need // dark_barrel.ml_per_barrel
                        if (quantity > dark_barrel.quantity):
                            quantity = dark_barrel.quantity
                        dark_need -= dark_barrel.ml_per_barrel * quantity
                        price += dark_barrel.price * quantity
                        barrels_im_buying.append({'sku':dark_barrel.sku, 'quantity': quantity})

        # Check if we can even afford this
        print(f"{price} <= {global_inventory.gold}")
        if (price <= global_inventory.gold):
            # wahoo we can afford
            print(f"we can afford {barrels_im_buying}")

            # update table with the strategy we ended up with
            strat.Strategy().update(new_strat)

            return json.loads(json.dumps(barrels_im_buying))
        else:
            print(f"we CANT afford {barrels_im_buying}")
            # decrement the potion with the largest quantity (preserving a diverse catalog)
            largest_key = max(new_strat, key = new_strat.get)
            new_strat[largest_key] -= 1

    return "NO BARREL PURCHASE"
