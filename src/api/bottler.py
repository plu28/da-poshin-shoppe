from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from src import global_inventory as gi
from src import catalog_table as ct
from src import log
from src import prices

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    log.post_log(f"/deliver/{order_id}")

    global_inventory = gi.GlobalInventory().retrieve()

    # add potions to catalog table. if the potion doesn't exist, insert a new row
    for potion in potions_delivered:
        sku = type_to_sku(potion.potion_type)
        catalog_row = ct.CatalogInventory().retrieve(sku)

        red_ml = potion.potion_type[0]
        green_ml = potion.potion_type[1]
        blue_ml = potion.potion_type[2]
        dark_ml = potion.potion_type[3]

        price = red_ml * prices.RED_PRICE_PER_ML + green_ml * prices.GREEN_PRICE_PER_ML + blue_ml * prices.BLUE_PRICE_PER_ML + dark_ml * prices.DARK_PRICE_PER_ML

        if (catalog_row == None):
            # TODO: Make it so the name is generated by an LLM to make it interesting
            insert_query = sqlalchemy.text("INSERT INTO catalog (sku, name, quantity, price, potion_type) VALUES (:sku, :name, :quantity, :price, :potion_type)")
            with db.engine.begin() as connection:
                connection.execute(insert_query,
                    {
                        'sku': sku,
                        'name': sku,
                        'quantity': potion.quantity,
                        'price': price,
                        'potion_type': potion.potion_type
                    }
                )
        else:
            # Update existing sku
            update_query = sqlalchemy.text("UPDATE catalog SET quantity = :quantity WHERE sku = :sku")
            with db.engine.begin() as connection:
                connection.execute(update_query,
                    {
                        'quantity': catalog_row.quantity + potion.quantity,
                        'sku': sku
                    }
                )

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    log.post_log('/plan')
    # DUMB LOGIC: Bottle into 5 red potions
    catalog = ct.CatalogInventory().retrieve("100red")
    # Insert if red isn't already in there
    if (catalog == None):
        insert_query = sqlalchemy.text("INSERT INTO catalog (sku, name, quantity, price, potion_type) VALUES (:sku, :name, :quantity, :price, :potion_type)")
        with db.engine.begin() as connection:
            connection.execute(insert_query,
                {
                    'sku': "100red",
                    'name': "100red",
                    'quantity': 0,
                    'price': 50,
                    'potion_type': [100,0,0,0]
                }
            )
        # Retrieve again
        catalog = ct.CatalogInventory().retrieve("100red")

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": 5 - catalog.quantity,
            }
        ]

def type_to_sku(potion_type):
    sku = []
    if potion_type[0] > 0:
        sku.append(f"{potion_type[0]}red")
    if potion_type[1] > 0:
        sku.append(f"{potion_type[1]}green")
    if potion_type[2] > 0:
        sku.append(f"{potion_type[2]}blue")
    if potion_type[3] > 0:
        sku.append(f"{potion_type[3]}dark")
    return "".join(sku)

if __name__ == "__main__":
    print(get_bottle_plan())
