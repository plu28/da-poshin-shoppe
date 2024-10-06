class Carts():
    def __init__(self, cart_id=0, red_ml=0, green_ml=0, blue_ml=0, dark_ml=0, potion_quantity=0):
        self.cart_id = cart_id
        self.red_ml = red_ml
        self.green_ml = green_ml
        self.blue_ml = blue_ml
        self.dark_ml = dark_ml
        self.potion_quantity = potion_quantity

    def retrieve(self):
        with db.engine.begin() as connection:
            inventory = connection.execute(sqlalchemy.text("SELECT cart_id, red_ml, green_ml, blue_ml, dark_ml, potion_quantity FROM carts"))
        row = inventory.fetchone()
        self.sku = row.sku
        self.quantity = row.quantity
        return self
