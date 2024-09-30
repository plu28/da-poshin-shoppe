from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
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
    # get current potions and ml
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_green_potions FROM global_inventory"))

    row = result.fetchone()
    num_green_ml = row.num_green_ml
    num_green_potions = row.num_green_potions

    # add green potions
    # subtract green_ml
    # iterating over all the delivered barrels for the future, but version 1 expects only 1 barrel though in the list
    for potions in potions_delivered:

        with open("bobo.txt", "w") as file:
            file.write(f"Bobo is delivering: {potions.potion_type} of which there are {potions.quantity}")
        num_green_potions += potions.quantity
        num_green_ml -= (100 * potions.quantity)

    # update table
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {num_green_ml}, num_green_potions = {num_green_potions}"))


    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into green potions.
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))

    green_ml = result.fetchone().num_green_ml

    # This is how many bottles im creating
    bottle_quantity = green_ml // 100

    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": bottle_quantity,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())

# todo: check if you have enough gold to even buy barrels in barrel plan
# todo: check if you even have enough ml to mix into potions
# todo: figure out selling
