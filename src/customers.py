from src import database as db
import sqlalchemy

class Customers():
    def __init__(self, customer_name="", character_class="", level=0, visit_count=0):
        self.customer_name = customer_name
        self.character_class = character_class
        self.level = level
        self.visit_count = visit_count

    # Given a customer name, returns an object of that customer. Returns none if the customer doesn't exist
    def retrieve(self, customer_name):
        select_query = sqlalchemy.text("SELECT * FROM customers WHERE customer_name = :customer_name")
        with db.engine.begin() as connection:
            select = connection.execute(select_query,
                {
                    'customer_name': customer_name
                }
            )
        row = select.fetchone()
        if (row == None):
            return None
        else:
            self.customer_name = row.customer_name
            self.character_class = row.character_class
            self.level = row.level
            self.visit_count = row.visit_count
            return self
