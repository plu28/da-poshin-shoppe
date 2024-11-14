from src import prices
import re

def get_price(sku: str):
    price = 0
    for ml_quantity, color in re.findall(r"(\d+)([a-z]+)", sku):
        ml_quantity = int(ml_quantity) # typecasting to int
        if color == "red":
            price += ml_quantity * prices.RED_PRICE_PER_ML
        elif color == "green":
            price += ml_quantity * prices.GREEN_PRICE_PER_ML
        elif color == "blue":
            price += ml_quantity * prices.BLUE_PRICE_PER_ML
        elif color == "dark":
            price += ml_quantity * prices.DARK_PRICE_PER_ML
    return round(price)

def get_type(sku: str):
    type = [0,0,0,0]
    for ml_quantity, color in re.findall(r"(\d+)([a-z]+)", sku):
        ml_quantity = int(ml_quantity) # typecasting to int
        if color == "red":
            type[0] = ml_quantity
        elif color == "green":
            type[1] = ml_quantity
        elif color == "blue":
            type[2] = ml_quantity
        elif color == "dark":
            type[3] = ml_quantity
    return type

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
