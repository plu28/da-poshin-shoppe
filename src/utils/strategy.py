import sqlalchemy
import json
from src.utils import database as db
from src.utils import log, skutils
from src.tables import global_inventory as gi
from src.tables import strategy as strat
from src import potion_combos
import random

# On every barrel tick we call determine_strategy
# Determine strategy returns a list of tuple: quantity pairs
#   NOTE: quantity will be set to maximize our potion capacity. this depends on how many potions we already
#   have in our catalog and our current capacity status
# Barrels then attempts to fulfill this strategy.
#   If we can't fulfill strategy, decrement a potion quantity and try again
#       If strategy is now empty, then we just dont buy barrels this tick we are too broke
# Bottler should just bottle everything in the strategy and set the strategy to be empty again
#   On the next tick, it won't do anything

def determine_strategy():

    # get all combos, make a copy, and cut down that copy based on limitations
    potion_mixes = potion_combos.COMBOS.copy()

    inv_query = sqlalchemy.text('''
        SELECT
            view_gold.gold AS gold,
            view_ml.red AS red,
            view_ml.green AS green,
            view_ml.blue AS blue,
            view_ml.dark AS dark
        FROM
            view_gold, view_ml
    ''')

    catalog_query = sqlalchemy.text('''
        SELECT
            view_catalog.sku AS sku,
            view_catalog.quantity AS quantity
        FROM
            view_catalog
    ''')

    strategy = []

    try:
        with db.engine.begin() as connection:
            inv = connection.execute(inv_query).fetchone()
            if inv == None:
                raise Exception("inventory returned none?")

            catalog = connection.execute(catalog_query).fetchall()
            if catalog == None:
                raise Exception("catalog returned none?")

        gold = inv.gold
        red = inv.red
        green = inv.green
        blue = inv.blue
        dark = inv.dark

    except Exception as e:
        print(e)
        return None

    add_random = 6 - len(catalog)

    if gold < 100:
        # too broke to do anything rn
        return strategy
    elif gold < 220:
        # can only afford absolutes (red and green), no dark
        add_random = 1
        strategy = list(filter(lambda mix: mix.count(0) == 3 and mix[3] == 0 and mix[2] == 0, potion_mixes))
    elif gold < 320:
        # can only make 2 color mixes, no dark
        add_random = 2
        strategy = list(filter(lambda mix: mix.count(0) == 2 and mix[3] == 0, potion_mixes))
    elif gold < 1050:
        # every color mix is fair game except dark
        strategy = list(filter(lambda mix: mix[3] == 0, potion_mixes))
    else:
        strategy = potion_mixes

    # select a random potion from the strategy
    strategy = random.sample(strategy, add_random)
    insert_value = []

    for potion_type in strategy:
        sku = skutils.type_to_sku(potion_type)
        insert_value.append(f"(\'{sku}\', 10)")

    insert_value_str = ', '.join(insert_value)


    reset_strategy_query = sqlalchemy.text('''
        TRUNCATE TABLE strategy
    ''')
    strategy_insert_query = sqlalchemy.text(f'''
        INSERT INTO
            strategy (sku, quantity)
        VALUES
            {insert_value_str}
    ''')
    try:
        with db.engine.begin() as connection:
            connection.execute(reset_strategy_query)
            connection.execute(strategy_insert_query)
    except Exception as e:
        print(e)
        return None

    return 1
