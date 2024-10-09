from math import gcd
from src import database as db
import sqlalchemy

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
