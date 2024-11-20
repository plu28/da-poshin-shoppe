from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import json
import re
from src.utils import database as db
from src.tables import global_inventory as gi
from src.tables import catalog_table as ct
from src.utils import log
from src import prices
from src.tables import strategy as strat

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    log.post_log(f"/deliver/{order_id}")

    print(f"POTIONS_DELIVERED: {potions_delivered} ORDER_ID: {order_id}")

    if len(potions_delivered) == 0:
        return "OK"

    # Retrieves current ml in strategy
    need = strat.Strategy().retrieve_as_need()

    # Check idempotency query 
    idempotency_check_query = sqlalchemy.text('''
        SELECT 1
        FROM poshin_ledger
        WHERE transaction_id = :order_id
    ''')

    insert_ml_query = sqlalchemy.text(f'''
        INSERT INTO ml_ledger (red, green, blue, dark, transaction_id)
        SELECT -(:red), -(:green), -(:blue), -(:dark), :order_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM ml_ledger
            WHERE transaction_id = :order_id
        )
        AND (SELECT red FROM view_ml) >= :red
        AND (SELECT green FROM view_ml) >= :green
        AND (SELECT blue FROM view_ml) >= :blue
        AND (SELECT dark FROM view_ml) >= :dark
    ''')

    insert_poshin_query = sqlalchemy.text(f'''
        INSERT INTO poshin_ledger (sku, quantity, transaction_id)
        SELECT strategy.sku, strategy.quantity, :order_id
        FROM strategy
        WHERE strategy.quantity > 0
    ''')

    try:
        with db.engine.begin() as connection:
            idempotency = connection.execute(idempotency_check_query, {'order_id': order_id})
            if idempotency.rowcount != 0:
                # this call has already been made
                print("BOTTLER DELIVER: idempotency detected")
                return "OK"

            insert_ml = connection.execute(insert_ml_query, {
                'red': need['red'],
                'green': need['green'],
                'blue': need['blue'],
                'dark': need['dark'],
                'order_id': order_id
            })
            if insert_ml.rowcount == 0:
                raise Exception("Inserting into ml_ledger failed")
            print(insert_ml.rowcount)

            insert_poshin = connection.execute(insert_poshin_query, {
                'red': need['red'],
                'green': need['green'],
                'blue': need['blue'],
                'dark': need['dark'],
                'order_id': order_id
            })
            if insert_poshin.rowcount == 0:
                raise Exception("Inserting into poshin ledger failed")
            print(insert_poshin.rowcount)

    except Exception as e:
        print(e)
        return "ERROR"

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    log.post_log('/bottler/plan')

    try:
        with db.engine.begin() as connection:
            # looking at current inventory
            current_ml_inventory_query = sqlalchemy.text('''
                SELECT * FROM view_ml
            ''')
            ml_inventory = connection.execute(current_ml_inventory_query).fetchone()
            if ml_inventory == None:
                raise Exception("There is no ml in inventory.")
    except Exception as e:
        print(e)
        return []

    available_red = ml_inventory.red
    available_green = ml_inventory.green
    available_blue = ml_inventory.blue
    available_dark = ml_inventory.dark

    bottle_plan = []
    mystrat = strat.Strategy().retrieve_as_dict()

    # calculating how much of each ml my strategy calls for
    for sku, quantity in mystrat.items():
        # print(f"{sku}")
        if quantity == 0:
            # print(f"skipping {sku}")
            continue
        red_ml = green_ml = blue_ml = dark_ml = 0
        order = {}
        # Since sku corresponds to potion makeup, I can use regex
        for ml_quantity, color in re.findall(r"(\d+)([a-z]+)", sku):
            ml_quantity = int(ml_quantity) # typecasting to int
            if color == "red":
                available_red -= ml_quantity
                red_ml += ml_quantity
            elif color == "green":
                available_green -= ml_quantity
                green_ml += ml_quantity
            elif color == "blue":
                available_blue -= ml_quantity
                blue_ml += ml_quantity
            elif color == "dark":
                available_dark -= ml_quantity
                dark_ml += ml_quantity

        order['potion_type'] = [red_ml, green_ml, blue_ml, dark_ml]
        order['quantity'] = quantity
        bottle_plan.append(order)

    # Check that we aren't bottling more than what's available
    try:
        assert available_red >= 0, "Bottling more red_ml than available"
        assert available_green >= 0, "Bottling more green_ml than available"
        assert available_blue >= 0, "Bottling more blue_ml than available"
        assert available_dark >= 0, "Bottling more dark_ml than available"
    except AssertionError as e:
        print(f"AssertionError: {e}")
        return []


    return json.loads(json.dumps(bottle_plan))

if __name__ == "__main__":
    print(get_bottle_plan())
