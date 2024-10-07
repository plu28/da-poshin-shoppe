from src import database as db
import sqlalchemy

class CartPotions():
    def __init__(self, cart_id="", sku="", quantity=0):
        self.cart_id = cart_id
        self.sku = sku
        self.quantity = quantity


    def retrieve(self, cart_id, sku):
        select_query = sqlalchemy.text("SELECT * FROM cart_potions WHERE cart_id = :cart_id AND sku = :sku")
        with db.engine.begin() as connection:
            select = connection.execute(select_query,
                {
                    'cart_id': cart_id,
                    'sku': sku
                }
            )
        row = select.fetchone()
        if (row == None):
            return None
        else:
            self.cart_id = row.cart_id
            self.sku = row.sku
            self.quantity = row.quantity
            return self
