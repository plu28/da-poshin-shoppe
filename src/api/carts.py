from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from src import customers as customer_table
from src import carts_table as ct
from src import catalog_table as cat
from src import global_inventory as gi
from src import cart_potions as cp
from src import log

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
    log.post_log(f'/carts/visits/{visit_id}')

    # Insert any new customers to the customers table
    for customer in customers:
        customer_row = customer_table.Customers().retrieve(customer.customer_name)
        if (customer_row == None):
            # First-time customer needs to be appended to customers table
            insert_query = sqlalchemy.text("INSERT INTO customers(customer_name, character_class, level, visit_count) VALUES (:customer_name, :character_class, :level, :visit_count)")
            with db.engine.begin() as connection:
                connection.execute(insert_query,
                    {
                        'customer_name': customer.customer_name,
                        'character_class': customer.character_class,
                        'level': customer.level,
                        'visit_count': 1
                    }
                )
        else:
            # Customer has previously visited, increment their visit count
            update_query = sqlalchemy.text("UPDATE customers SET visit_count = :visit_count WHERE customer_name = :customer_name")
            with db.engine.begin() as connection:
                connection.execute(update_query,
                    {
                        'visit_count': customer_row.visit_count + 1,
                        'customer_name': customer_row.customer_name
                    }
                )

    return [{"success": True}]


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    log.post_log('/carts/create_cart')

    cart_id = random.randint(100000000, 999999999) # Generates a random id, ~ 1 billion possible id's

    # Check to make sure there is no cart_id collision
    carts_table = ct.Carts().retrieve(cart_id)
    while (carts_table != None):
        cart_id = random.randint(100000000, 999999999) # Generates a new id if a collision was found and checks again to make sure it doesn't exist
        carts_table = ct.Carts().retrieve(cart_id)

    insert_query = sqlalchemy.text("INSERT INTO carts (cart_id, red_ml, green_ml, blue_ml, dark_ml, potion_quantity) VALUES (:cart_id, 0, 0, 0, 0, 0)")
    with db.engine.begin() as connection:
        connection.execute(insert_query, {'cart_id': cart_id})

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    log.post_log(f"/carts/{cart_id}/items/{item_sku}")

    cart = ct.Carts().retrieve(cart_id)
    potion = cat.CatalogInventory().retrieve(item_sku)

    # Add the proper ml to the cart
    cart.red_ml += potion.potion_type[0] * cart_item.quantity
    cart.green_ml += potion.potion_type[1] * cart_item.quantity
    cart.blue_ml += potion.potion_type[2] * cart_item.quantity
    cart.dark_ml += potion.potion_type[3] * cart_item.quantity

    # Update carts table
    update_query_carts = sqlalchemy.text("UPDATE carts SET red_ml = :red_ml, green_ml = :green_ml, blue_ml = :blue_ml, dark_ml = :dark_ml, potion_quantity = :potion_quantity WHERE cart_id = :cart_id")
    with db.engine.begin() as connection:
        connection.execute(update_query_carts,
            {
                'red_ml': cart.red_ml,
                'green_ml': cart.green_ml,
                'blue_ml': cart.blue_ml,
                'dark_ml': cart.dark_ml,
                'potion_quantity': cart.potion_quantity + cart_item.quantity,
                'cart_id': cart_id
            })

    # Update cart_potions table
    cart_potions_row = cp.CartPotions().retrieve(cart_id, item_sku)
    if (cart_potions_row == None):
        # Insert a new row
        insert_query = sqlalchemy.text("INSERT INTO cart_potions (cart_id, sku, quantity) VALUES (:cart_id, :sku, :quantity)")
        with db.engine.begin() as connection:
            connection.execute(insert_query,
                {
                    'cart_id': cart_id,
                    'sku': item_sku,
                    'quantity': cart_item.quantity
                })
    else:
        # Update existing row quantity
        update_query_cart_potions = sqlalchemy.text("UPDATE cart_potions SET quantity = :quantity")
        with db.engine.begin() as connection:
            connection.execute(update_query_cart_potions, {'quantity': cart_potions_row.quantity + cart_item.quantity})

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    log.post_log(f"/carts/{cart_id}/checkout")

    cart = ct.Carts().retrieve(cart_id)
    total = cart.get_cart_value()

    global_inventory = gi.GlobalInventory().retrieve()

    # Grabbing all this carts rows in cart_potions table
    select_query = sqlalchemy.text ("SELECT * FROM cart_potions WHERE cart_id = :cart_id")
    with db.engine.begin() as connection:
        cart_rows = connection.execute(select_query, { 'cart_id': cart_id }).fetchall()

    # Before checking out, check if there is enough stock to fulfill the order
    for cart_row in cart_rows:
        available_stock = cat.CatalogInventory().retrieve(cart_row.sku).quantity
        if available_stock < cart_row.quantity:
            return "NOT ENOUGH STOCK"
    # Passing this for loop means there is enough stock to fulfill the order

    potions_bought = 0
    for cart_row in cart_rows:
        potions_bought += cart_row.quantity

        # decrement stock in catalog
        available_stock = cat.CatalogInventory().retrieve(cart_row.sku).quantity
        update_cat_query = sqlalchemy.text("UPDATE catalog SET quantity = :quantity WHERE sku = :sku")
        with db.engine.begin() as connection:
            connection.execute(update_cat_query,
                {
                    'quantity': available_stock - cart_row.quantity,
                    'sku': cart_row.sku
                }
            )

    # update gold in inventory
    update_gi_query = sqlalchemy.text("UPDATE global_inventory SET gold = :gold")
    with db.engine.begin() as connection:
        connection.execute(update_gi_query, {'gold': global_inventory.gold + total })

    return {"total_potions_bought": potions_bought, "total_gold_paid": total}
