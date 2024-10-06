from src import database as db
import sqlalchemy

def post_log(endpoint, request="{}", response="{}"):
    with db.engine.begin() as connection:
        log = connection.execute(sqlalchemy.text(f"INSERT INTO logs (endpoint, request, response) VALUES ('{endpoint}', '{response}', '{request}')"))
