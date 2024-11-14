from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import json
from json import dumps
from src.utils import database as db
from src.tables import global_inventory as gi
from src.tables import catalog_table as cat
from src.tables import roxanne as rox
from src.utils import log, strategy
from src.tables import strategy as strat
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

    # Get how much im paying and how much im buying from these barrels
    barrel_cost = 0
    red = 0
    green = 0
    blue = 0
    dark = 0

    for barrel in barrels_delivered:
        barrel_cost -= (barrel.price * barrel.quantity)
        if barrel.potion_type == [1,0,0,0]:
            red += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0,1,0,0]:
            green += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0,0,1,0]:
            blue += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type == [0,0,0,1]:
            dark += (barrel.ml_per_barrel * barrel.quantity)

    # SQL statement:
        # Retrieves current gold (necessary for the later WHERE EXISTS clause to check if I can afford this barrel delivery)
        # Inserts into the global inventory ledger IF the following conditions are true:
            # I can afford this (WHERE EXISTS)
            # This order_id hasn't come in before (AND NOT EXISTS)
    cte = '''
        WITH current_inv AS (
            SELECT
                SUM(gold_ledger.gold_change) AS gold
            FROM
                gold_ledger
        )
    '''

    condition = '''
        WHERE EXISTS (
            SELECT
                gold
            FROM
                current_inv
            WHERE
                gold >= -(:barrel_cost)
            )
        AND NOT EXISTS (
            SELECT
                transaction_id
            FROM
                gold_ledger
            WHERE
                transaction_id = :order_id
        )
    '''

    insert_gold_ledger_query = sqlalchemy.text(f'''
        {cte}
        INSERT INTO
            gold_ledger (gold_change, transaction_id)
        SELECT
            :barrel_cost,
            :order_id
        {condition}
    ''')

    insert_ml_ledger_query = sqlalchemy.text(f'''
        {cte}
        INSERT INTO
            ml_ledger (red, green, blue, dark, transaction_id)
        SELECT
            :red_ml, :green_ml, :blue_ml, :dark_ml, :order_id
        {condition}
        '''
    )
    with db.engine.begin() as connection:
        try:
            insert_ml = connection.execute(insert_ml_ledger_query,
                {
                    'red_ml': red,
                    'green_ml': green,
                    'blue_ml': blue,
                    'dark_ml': dark,
                    'order_id': order_id,
                    'barrel_cost': barrel_cost
                }
            )
            if insert_ml.rowcount == 0:
                raise Exception("insert_ml affected 0 rows")

            insert_gold = connection.execute(insert_gold_ledger_query,
                {
                    'barrel_cost': barrel_cost,
                    'order_id': order_id
                }
            )
            if insert_gold.rowcount == 0:
                raise Exception("insert_gold affected 0 rows")

        except Exception as e:
            print(e)
            return {"error": e}

    return "OK"

# Gets called every other tick
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # Log endpoint
    log.post_log('/barrels/plan')

    # Determine strategy once
    strategy.determine_strategy()

    wholesale_catalog.sort(key = lambda barrel: -barrel.ml_per_barrel)
    order = {}
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM view_gold")).scalar_one()
    price = 0
    red_cart = green_cart = blue_cart = dark_cart = 0

    need = strat.Strategy().retrieve_as_need()
    # Loop while strategy is not empty
    while (need['red'] > 0, need['green'] > 0, need['blue'] > 0, need['dark'] > 0):
        need = strat.Strategy().retrieve_as_need()
        print(f"{red_cart} : {need['red']}")
        print(f"{green_cart} : {need['green']}")
        # Loop while there is need
        while (red_cart < need['red']) or (green_cart < need['green']) or (blue_cart < need['blue']) or (dark_cart < need['dark']):
            marker = 0
            if red_cart < need['red']:
                # Buy the biggest barrel we can afford
                for barrel in wholesale_catalog:
                    if (barrel.quantity > 0) and (gold >= barrel.price + price) and (barrel.potion_type == [1,0,0,0]) and (red_cart < need['red']):
                        if (barrel.sku in order.keys()):
                            order[barrel.sku] += 1
                        else:
                            order[barrel.sku] = 1
                        price += barrel.price
                        barrel.quantity -= 1
                        red_cart += barrel.ml_per_barrel
                        marker += 1
                        break
            if green_cart < need['green']:
                # Buy the biggest barrel we can afford
                for barrel in wholesale_catalog:
                    if (barrel.quantity > 0) and (gold >= barrel.price + price) and (barrel.potion_type == [0,1,0,0]) and (green_cart < need['green']):
                        if (barrel.sku in order.keys()):
                            order[barrel.sku] += 1
                        else:
                            order[barrel.sku] = 1
                        price += barrel.price
                        barrel.quantity -= 1
                        green_cart += barrel.ml_per_barrel
                        marker += 1
                        break
            if blue_cart < need['blue']:
                # Buy the biggest barrel we can afford
                for barrel in wholesale_catalog:
                    if (barrel.quantity > 0) and (gold >= barrel.price + price) and (barrel.potion_type == [0,0,1,0]) and (blue_cart < need['blue']):
                        if (barrel.sku in order.keys()):
                            order[barrel.sku] += 1
                        else:
                            order[barrel.sku] = 1
                        price += barrel.price
                        barrel.quantity -= 1
                        blue_cart += barrel.ml_per_barrel
                        marker += 1
                        break
            if dark_cart < need['dark']:
                # Buy the biggest barrel we can afford
                for barrel in wholesale_catalog:
                    if (barrel.quantity > 0) and (gold >= barrel.price + price) and (barrel.potion_type == [0,0,0,1]) and (dark_cart < need['dark']):
                        if (barrel.sku in order.keys()):
                            order[barrel.sku] += 1
                        else:
                            order[barrel.sku] = 1
                        price += barrel.price
                        barrel.quantity -= 1
                        dark_cart += barrel.ml_per_barrel
                        marker += 1
                        break
            if marker == 0:
                break

        try:
            with db.engine.begin() as connection:
            # we either fill the need or buy nothing
                if (red_cart < need['red']):
                    # reduce quantity of a potion containing red
                    decrease_red_potions = sqlalchemy.text('''
                    WITH red_skus AS (
                        SELECT
                            sku
                        FROM
                            strategy
                        WHERE
                            sku ILIKE '%red%'
                    )
                    UPDATE
                        strategy
                    SET
                        quantity = quantity - 1
                    WHERE
                        strategy.sku IN (SELECT red_skus.sku FROM red_skus)
                        AND quantity > 0
                    ''')
                    connection.execute(decrease_red_potions)
                if (green_cart < need['green']):
                    # reduce quantity of a potion containing green in strategy
                    decrease_green_potions = sqlalchemy.text('''
                    WITH green_skus AS (
                        SELECT
                            sku
                        FROM
                            strategy
                        WHERE
                            sku ILIKE '%green%'
                    )
                    UPDATE
                        strategy
                    SET
                        quantity = quantity - 1
                    WHERE
                        strategy.sku IN (SELECT green_skus.sku FROM green_skus)
                        AND quantity > 0
                    ''')
                    connection.execute(decrease_green_potions)
                if (blue_cart < need['blue']):
                    # reduce quantity of a potion containing blue
                    decrease_blue_potions = sqlalchemy.text('''
                    WITH blue_skus AS (
                        SELECT
                            sku
                        FROM
                            strategy
                        WHERE
                            sku ILIKE '%blue%'
                    )
                    UPDATE
                        strategy
                    SET
                        quantity = quantity - 1
                    WHERE
                        strategy.sku IN (SELECT blue_skus.sku FROM blue_skus)
                        AND quantity > 0
                    ''')
                    connection.execute(decrease_blue_potions)
                if (dark_cart < need['dark']):
                    # reduce quantity of a potion containing dark
                    decrease_dark_potions = sqlalchemy.text('''
                    WITH dark_skus AS (
                        SELECT
                            sku
                        FROM
                            strategy
                        WHERE
                            sku ILIKE '%dark%'
                    )
                    UPDATE
                        strategy
                    SET
                        quantity = quantity - 1
                    WHERE
                        strategy.sku IN (SELECT dark_skus.sku FROM dark_skus)
                        AND quantity > 0
                    ''')
                    connection.execute(decrease_dark_potions)
                if (red_cart >= need['red'] and green_cart >= need['green'] and blue_cart >= need['blue'] and dark_cart >= need['dark']):
                    # break out of the loop. we've fulfilled the need
                    print("breaking out of loop")
                    break
        except Exception as e:
            print(e)
            return []

    return_list = []
    for barrel_sku, quantity in order.items():
        return_list.append({
            "sku": barrel_sku,
            "quantity": quantity
        })
    return json.loads(json.dumps(return_list))
