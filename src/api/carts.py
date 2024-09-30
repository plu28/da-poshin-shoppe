from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
import random

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku,
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(f"ENDPOINT CALL: /visits/{visit_id}\ncustomers: {customers}")

    return [{"success": True}]


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    # cart_id = ASCII(new_cart.customer_name + new_cart.character_class + str(new_cart.level)) # WARNING: THIS cart_id METHOD MAY GENERATE DUPLICATE CART_ID's
    cart_id = random.randrange(10000,100000) # random number generator can still create two radom cart_id's that are the same
    print(f"ENDPOINT CALL: /create_cart \nnew_cart={new_cart}\ncustomer_id={cart_id}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"INSERT INTO carts (cart_id, red_ml, green_ml, blue_ml, dark_ml, potion_quantity) VALUES ('{cart_id}', 0, 0, 0, 0, 0)"))

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    print(f"ENDPOINT CALL: /{cart_id}/items/{item_sku}\ncart_id={cart_id}\nitem_sku={item_sku}\ncart_item={cart_item}\ncart_item.quantity={cart_item.quantity}")
    # currently, the shop only sells green potions so the item_sku is going to be GREEN_POTION
    # in the future, I am going to need another table that has its sku and mixture so I can update the table accordingly
    # THE FOLLOWING LINES ARE HARD-CODED ONLY FOR VERSION 1 AND WILL HAVE TO BE REMOVED FOR LATER VERSIONS
    # Get pre-existing quantitites
    with db.engine.begin() as connection:
        current = connection.execute(sqlalchemy.text(f"SELECT * FROM carts WHERE cart_id={cart_id}"))

    current = current.fetchone() # convert to row
    current_potion_quantity = current.potion_quantity
    current_green_ml = current.green_ml

    with db.engine.begin() as connection:
        update_cursor = connection.execute(sqlalchemy.text(f"UPDATE carts SET potion_quantity={current_potion_quantity + cart_item.quantity}, green_ml={current_green_ml + (cart_item.quantity * 100)} WHERE cart_id={cart_id}"))

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    # calculate price based on ml
    # 1 green ml = 1 gold
    COST_PER_GREEN_ML = 1

    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text(f"SELECT * FROM carts WHERE cart_id={cart_id}"))
    cart = cart.fetchone()
    cart_green_ml = cart.green_ml
    potions_bought = cart.potion_quantity

    total_gold_paid = cart_green_ml * COST_PER_GREEN_ML

    # update gold in inventory
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text(f"SELECT * FROM global_inventory"))
    current_gold = inventory.fetchone().gold

    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold={current_gold + total_gold_paid}"))

    return {"total_potions_bought": potions_bought, "total_gold_paid": cart_green_ml}
