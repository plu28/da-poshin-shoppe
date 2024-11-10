from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
# from sqlalchemy.sql.sqltypes import TIMESTAMP
from src.api import auth
from enum import Enum
import sqlalchemy
# from sqlalchemy.orm import declarative_base, sessionmaker
# from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP
from src.utils import database as db
from src.tables import customers as customer_table
from src.tables import carts_table as ct
from src.tables import catalog_table as cat
from src.tables import global_inventory as gi
from src.tables import cart_potions as cp
from src.utils import log, skutils
# from datetime import datetime
import json

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

# Base = declarative_base()
# class carts(Base):
#     __tablename__ = 'carts'
#     id = Column(Integer, primary_key=True)
#     customer_name = Column(Text, nullable=True)
#     character_class = Column(Text, nullable=True)
#     level = Column(Integer, nullable=True)

# class cart_potions(Base):
#     __tablename__ = 'cart_potions'
#     id = Column(Integer, primary_key=True)
#     cart_id = Column(Integer, ForeignKey('carts.id'))
#     sku = Column(Text)
#     quantity = Column(Integer, nullable=True)

# class completed_carts(Base):
#     __tablename__ = 'completed_carts'
#     id = Column(Integer, ForeignKey('carts.id'), primary_key=True)
#     created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

# Base.metadata.create_all(db.engine)

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

    search_query = sqlalchemy.text(f'''
        SELECT
            cart_potions.sku AS item_sku,
            cart_potions.quantity AS quantity,
            carts.customer_name AS customer_name,
            completed_carts.created_at AS timestamp,
            completed_carts.line_item_total AS line_item_total
        FROM
            carts
        JOIN
            cart_potions ON carts.id = cart_potions.cart_id
        JOIN
            completed_carts ON carts.id = completed_carts.id
        WHERE
            customer_name ILIKE :customer_name
            AND sku ILIKE :potion_sku
        ORDER BY {sort_col.value} {sort_order.value}
        LIMIT 5
    ''')
    try:
        with db.engine.begin() as connection:
            search_result_mappings = connection.execute(search_query, {
                'customer_name': '%' + customer_name + '%',
                'potion_sku': '%' + potion_sku + '%',
                'search_page': search_page
            }).mappings()
    except Exception as e:
        print(e)
        return {'error': e}

    results = []
    for i, search_result in enumerate(search_result_mappings):
        search_result = dict(search_result)
        search_result['item_sku'] = f"{search_result['quantity']} {search_result['item_sku']}"
        search_result['timestamp'] = search_result['timestamp'].isoformat()
        search_result['line_item_id'] = + i

        # Remove key value pair to fit api spec
        del search_result['quantity']
        results.append(search_result)


    return {
        "previous": "",
        "next": "/carts/search/?sort_col=timestamp&sort_order=desc",
        "results": json.loads(json.dumps(results))
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

    insert_query = sqlalchemy.text('''
        INSERT INTO carts (customer_name, character_class, level)
        SELECT :customer_name, :character_class, :level
        RETURNING carts.id
    ''')
    with db.engine.begin() as connection:
        cart_insert = connection.execute(insert_query, {
            'customer_name': new_cart.customer_name,
            'character_class': new_cart.character_class,
            'level': new_cart.level
        }).fetchone()

    return {"cart_id": cart_insert.id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    log.post_log(f"/carts/{cart_id}/items/{item_sku}")

    try:
        with db.engine.begin() as connection:
            potion = connection.execute(sqlalchemy.text("SELECT quantity FROM view_catalog WHERE sku = :sku"), {'sku': item_sku}).fetchone()
            # cart = connection.execute(sqlalchemy.text("SELECT * FROM carts WHERE id = :cart_id")).fetchone()
        assert potion.quantity >= cart_item.quantity, f"Can't add more than what's available in stock. {potion.quantity} available, {cart_item.quantity} wanted"
    except Exception as e:
        print(e)
        return "ERROR"

    insert_cart_potions_query = sqlalchemy.text('''
        INSERT INTO cart_potions (cart_id, sku, quantity)
        SELECT :cart_id, :item_sku, :quantity
    ''')
    with db.engine.begin() as connection:
        connection.execute(insert_cart_potions_query, {
            'cart_id': cart_id,
            'item_sku': item_sku,
            'quantity': cart_item.quantity
        })

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    log.post_log(f"/carts/{cart_id}/checkout")

    cart_query = sqlalchemy.text('''
        WITH cart AS (
            SELECT sku, quantity
            FROM cart_potions
            WHERE cart_id = :cart_id
            GROUP BY sku, quantity
        )
        SELECT * FROM cart
        -- Ensuring that we are not checking out more potions than we have in stock
        WHERE NOT EXISTS (
            SELECT 1
            FROM cart
            JOIN view_catalog ON cart.sku = view_catalog.sku
            WHERE view_catalog.quantity < cart.quantity
        )
    ''')

    gold_ledger_query = sqlalchemy.text('''
        INSERT INTO gold_ledger (gold_change, transaction_id)
        SELECT :price, :cart_id
    ''')

    poshin_ledger_query = sqlalchemy.text('''
        INSERT INTO poshin_ledger (sku, quantity, transaction_id)
        SELECT cart_potions.sku, -(cart_potions.quantity), :cart_id
        FROM cart_potions
        WHERE cart_potions.cart_id = :cart_id
    ''')

    completed_carts_query = sqlalchemy.text('''
        INSERT INTO completed_carts (id, line_item_total)
        SELECT :cart_id, :line_item_total
    ''')

    try:
        with db.engine.begin() as connection:
            cart_rows = connection.execute(cart_query, {'cart_id': cart_id}).fetchall()
            if len(cart_rows) == 0:
                raise Exception("This cart is checking out more than my stock")

            # Getting the carts total and quantity of potions
            price = 0
            total_potions = 0
            for row in cart_rows:
                price += skutils.get_price(row.sku) * row.quantity
                total_potions += row.quantity

            update_gold_ledger = connection.execute(gold_ledger_query, {
                'price': price,
                'cart_id': cart_id
            })

            update_poshin_ledger = connection.execute(poshin_ledger_query, {'cart_id': cart_id})
            update_completed_carts = connection.execute(completed_carts_query, {'cart_id': cart_id, 'line_item_total': price})
    except Exception as e:
        print(e)
        return "ERROR"

    return {"total_potions_bought": total_potions, "total_gold_paid": price}
