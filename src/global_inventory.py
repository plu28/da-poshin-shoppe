from src import database as db
import sqlalchemy

class GlobalInventory():
    def __init__(self, gold=0, red_ml=0, green_ml=0, blue_ml=0, dark_ml=0):
        self.gold = gold
        self.red_ml = red_ml
        self.green_ml = green_ml
        self.blue_ml = blue_ml
        self.dark_ml = dark_ml

    def retrieve(self):
        with db.engine.begin() as connection:
            inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row = inventory.fetchone()
        self.gold = row.gold
        self.red_ml = row.red_ml
        self.green_ml = row.green_ml
        self.blue_ml = row.blue_ml
        self.dark_ml = row.dark_ml
        return self
