from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # grabs the green potions from the database
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

    num_green_potions = result.fetchone().num_green_potions
    if num_green_potions == 0:
        return []

    return [
        {
            "sku": "GREEN_POTION",
            "name": "green potion",
            "quantity": num_green_potions,
            "price": 100,
            "potion_type": [0,100,0,0],
        }
    ]

    # return [
    #         {
    #             "sku": "RED_POTION_0",
    #             "name": "red potion",
    #             "quantity": 1,
    #             "price": 100,
    #             "potion_type": [100, 0, 0, 0],
    #         }
    #     ]
