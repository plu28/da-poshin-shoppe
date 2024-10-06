from src import database as db
import sqlalchemy

class CatalogInventory():
    def __init__(self, sku="", name="", quantity=0, price=0, potion_type = [0,0,0,0]):
        self.sku = sku
        self.name = name
        self.quantity = quantity
        self.price = price
        self.potion_type = potion_type

    # Given a catalog sku, returns an object of that catalog item. Returns none if the item doesn't exist
    def retrieve(self, sku):
        select_query = sqlalchemy.text("SELECT * FROM catalog WHERE sku = :sku")
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
            self.name = row.name
            self.quantity = row.quantity
            self.price = row.price
            self.potion_type = row.potion_type
            return self
