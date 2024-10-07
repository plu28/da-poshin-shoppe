import sqlalchemy
from src import database as db
from . import prices

class Carts():
    def __init__(self, cart_id=0, red_ml=0, green_ml=0, blue_ml=0, dark_ml=0, potion_quantity=0):
        self.cart_id = cart_id
        self.red_ml = red_ml
        self.green_ml = green_ml
        self.blue_ml = blue_ml
        self.dark_ml = dark_ml
        self.potion_quantity = potion_quantity

    def retrieve(self, cart_id):
        select_query = sqlalchemy.text("SELECT * FROM carts WHERE cart_id = :cart_id")
        with db.engine.begin() as connection:
            select = connection.execute(select_query,
                {
                    'cart_id': cart_id
                }
            )
        row = select.fetchone()
        if (row == None):
            return None
        else:
            self.cart_id = cart_id
            self.red_ml = row.red_ml
            self.green_ml = row.green_ml
            self.blue_ml = row.blue_ml
            self.dark_ml = row.dark_ml
            self.potion_quantity = row.potion_quantity
            return self

    def get_cart_value(self):
        return (self.red_ml * prices.RED_PRICE_PER_ML) + (self.green_ml * prices.GREEN_PRICE_PER_ML) + (self.blue_ml * prices.BLUE_PRICE_PER_ML) + (self.dark_ml * prices.DARK_PRICE_PER_ML)
