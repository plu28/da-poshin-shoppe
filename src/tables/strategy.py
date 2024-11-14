from math import gcd
from src.utils import database as db
import sqlalchemy
import re

class Strategy():
    def __init__(self, sku="", quantity=0,):
        self.sku = sku
        self.quantity = quantity

    # Returns as key value pairs where they key is the sku and value is the quantity
    def retrieve_as_dict(self):
        select_query = sqlalchemy.text("SELECT * FROM strategy")
        with db.engine.begin() as connection:
            select = connection.execute(select_query)
        rows = select.fetchall()
        if (rows == None):
            return None
        else:
            strategy = {}
            for row in rows:
                strategy[row.sku] = row.quantity

            return strategy

    def retrieve_as_need(self):
        ml_query = sqlalchemy.text('''
            SELECT
                red,
                green,
                blue,
                dark
            FROM
                view_ml
        ''')

        select_query = sqlalchemy.text('''
            SELECT
                *
            FROM
                strategy
        ''')
        with db.engine.begin() as connection:
            select = connection.execute(select_query)
            current_ml = connection.execute(ml_query).fetchone()
        rows = select.fetchall()
        if (rows == None):
            return None
        else:
            need = {
                'red': -current_ml.red,
                'green': -current_ml.green,
                'blue': -current_ml.blue,
                'dark': -current_ml.dark
            }
            for row in rows:
                for ml_quantity, color in re.findall(r"(\d+)([a-z]+)", row.sku):
                    ml_quantity = int(ml_quantity) # typecasting to int
                    if color == "red":
                        need['red'] += ml_quantity * row.quantity
                    elif color == "green":
                        need['green'] += ml_quantity * row.quantity
                    elif color == "blue":
                        need['blue'] += ml_quantity * row.quantity
                    elif color == "dark":
                        need['dark'] += ml_quantity * row.quantity

            print(f"FROM STRAT TABLE CLASS {need}")
            return need

    def update(self, new_strat):
        # NOTE: WE'RE DOING AN UPDATE FOR EVERY ROW IN STRATEGY TABLE! NOT GOOD
        for sku, quantity in new_strat.items():
            update_query = sqlalchemy.text("UPDATE strategy SET quantity = :quantity WHERE sku = :sku")
            with db.engine.begin() as connection:
                connection.execute(update_query,
                    {
                        'quantity': quantity,
                        'sku': sku
                    }
                )

    def wipe(self):
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("DELETE FROM strategy"))
