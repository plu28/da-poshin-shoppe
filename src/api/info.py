from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import json
from src.utils import database as db
from src.utils import log
from src.tables import global_inventory as gi
from src.tables import strategy as strat
router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

@router.post("/current_time")
def post_time(timestamp: Timestamp):
    """
    Share current time.
    """
    # LOGGING
    log.post_log("/current_time", request=json.dumps(timestamp.__dict__))
    global_inventory = gi.GlobalInventory().retrieve()
    if global_inventory.gold >= 500:
        print("Begin selling mixed potions")
        new_strat = {"50red50green":5, "50red50blue":5, "50green50blue":5}
        strat.Strategy().update(new_strat)
    elif global_inventory.gold >= 350:
        print("Buying all potion types")
        new_strat = {"100red":5, "100green":5, "100blue":5}
        strat.Strategy().update(new_strat)
    elif global_inventory.gold >= 220:
        print("Modifying strategy for 5 blue 5 green")
        new_strat = {"100red": 0, "100green":5, "100blue":5}
        strat.Strategy().update(new_strat)
    else:
        print("Can only buy reds")
        new_strat = {"100red":5, "100green":0, "100blue":0}
        strat.Strategy().update(new_strat)

    return "OK"
