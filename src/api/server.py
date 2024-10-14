from fastapi import FastAPI, exceptions, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.api import carts, catalog, bottler, barrels, admin, info, inventory, health
import json
import logging
import sys
import time
from starlette.middleware.cors import CORSMiddleware
from starlette.types import Message
import sqlalchemy
from src.utils import database as db

description = """
Central Coast Cauldrons is the premier ecommerce site for all your alchemical desires.
"""

app = FastAPI(
    title="Central Coast Cauldrons",
    description=description,
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Lucas Pierce",
        "email": "lupierce@calpoly.edu",
    },
)

origins = ["https://potion-exchange.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(inventory.router)
app.include_router(carts.router)
app.include_router(catalog.router)
app.include_router(bottler.router)
app.include_router(barrels.router)
app.include_router(admin.router)
app.include_router(info.router)
app.include_router(health.router)

@app.exception_handler(exceptions.RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    logging.error(f"The client sent invalid data!: {exc}")
    exc_json = json.loads(exc.json())
    response = {"message": [], "data": None}
    for error in exc_json:
        response['message'].append(f"{error['loc']}: {error['msg']}")

    return JSONResponse(response, status_code=422)

@app.get("/")
async def root():
    return {"message": "dis da poshin shoppe."}

async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {'type': 'http.request', 'body': body}
    request._receive = receive

@app.middleware("http")
async def log_requests_and_responses(request: Request, call_next):
    print(f"Request: {request.method} {request.url}")

    req_body = await request.body()
    print(f"Request Body:\n{req_body.decode('utf-8')}")

    await set_body(request, req_body)
    response = await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    print(f"Process time: {process_time:.4f} seconds")

    return response
