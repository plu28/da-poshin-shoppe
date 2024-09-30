from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int


@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold, num_green_ml FROM global_inventory"))

    # info to be updated
    row = result.fetchone()
    current_gold = row.gold
    num_green_ml = row.num_green_ml

    # getting barrel info
    barrel_cost = 0
    num_added_green_ml = 0 # for now, we're only adding green ml


    # iterating over all the delivered barrels for the future, but version 1 expects only 1 barrel though in the list
    for barrel in barrels_delivered:
        print(f"Roxanne is delivering: {barrel.sku}, {barrel.ml_per_barrel}, {barrel.potion_type}, {barrel.price}, {barrel.quantity}")
        barrel_cost += (barrel.price * barrel.quantity)
        num_added_green_ml += (barrel.ml_per_barrel * barrel.quantity)

    # subtract gold by the number of barrels that were purchased
    # get gold by query and num_green_ml by query
    new_gold = current_gold - barrel_cost
    new_num_green_ml = num_green_ml + num_added_green_ml

    # update table
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {new_num_green_ml}, gold = {new_gold}"))

    # LOGGING
    # with db.engine.begin() as connection:
    #     log = connection.execute(sqlalchemy.text(f"INSERT INTO logs (endpoint, request, response) VALUES (\"/deliver/{order_id}\",{{}})"))
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    # TODO: make sure there is enough gold for the purchase before sending out the purchase request
    # print(f"WHOLESALE_CATALOG: {type(wholesale_catalog[0].price)}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))

    green_quantity = result.fetchone().num_green_potions
    print(type(green_quantity))

    # iterate over what roxanne's selling
    # what does roxanne's call look like?
    # will the barrels be diluted or will they be 100 of a color?
    for barrel in wholesale_catalog:
        with open("roxanne.txt", "w") as file:
            file.write(f"Roxanne is selling: {barrel.sku}, {barrel.ml_per_barrel}, {barrel.potion_type}, {barrel.price}, {barrel.quantity}")

        if (barrel.potion_type == [0,100,0,0]):
            if (green_quantity < 10):
                return [
                    {
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": 1,
                    }
                ]




# roxanne offers the barrels
# you send roxanne the plan, and she delivers the barrels
# bobo also
# goal is to optimize gold. get the most money in the competition. he will burn the shops before the customization occurs
# rgbd of ml will be added to create a potion
#
#
# 1500 unique adventurers that shop. every adventurer has a level that ranges from level 1-20. Higher levels are more likely to have more money.
# There are adventurer classes, fantasy race (orc, elf, gnome, etc). These traits will determine which . The same types of customers shop at the same times.
# There are shopping patterns to be uncovered to optimize your shop. Do logging, track which classes shop at which time and make sure your shop is well stocked to fulfill their needs.
# You can offer 6 potions at a time. You ca. You can mix on demand meaning when certain customers arrive you can mix what they want and offer it in the shop in time.
# Any data you collect in the beginning state will also be valid in the competition.

# The gnoll construction union will improve your capacity???
#
# Im guessing bobo is the bottler?
