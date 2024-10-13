from src.utils import database as db
import sqlalchemy

class Roxanne():
    def __init__(self, sku="", ml_per_barrel=0, price=0, quantity=0, potion_type=[0,0,0,0]):
        self.sku = sku
        self.ml_per_barrel = ml_per_barrel
        self.price = price
        self.quantity = quantity
        self.potion_type = potion_type

    # Given a customer name, returns an object of that customer. Returns none if the customer doesn't exist
    def retrieve(self, sku):
        select_query = sqlalchemy.text("SELECT * FROM roxanne WHERE sku = :sku")
        with db.engine.begin() as connection:
            select = connection.execute(select_query,
                {
                    'sku': sku
                }
            )
        row = select.fetchone()
        if (row == None):
            return None
        else:
            self.sku = row.sku
            self.ml_per_barrel = row.ml_per_barrel
            self.price = row.price
            self.quantity = row.quantity
            self.potion_type = row.potion_type
            return self

    def wipe(self):
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("DELETE FROM roxanne"))
