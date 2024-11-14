from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
import json
from src.utils import database as db
from src.utils import log, skutils, strategy
from src.tables import global_inventory as gi
from src.tables import strategy as strat
from src import potion_combos
import random

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

    return "OK"
