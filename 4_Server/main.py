import os
import logging

import psycopg
import fastapi.responses as responses

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager


ROOT_DIR = os.path.dirname(__file__)

db_conninfo = (
    "dbname=PDB "
    "user=parser "
    f"password={os.getenv('DB_PASS')} "
    "host=localhost")

SQL_GET_PRODUCTS = """
SELECT * FROM products
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger('uvicorn')
    logger.info('Password: %s', os.getenv('DB_PASS'))
    
    with psycopg.connect(db_conninfo) as db_connection:
        yield {'database': db_connection, 'logger': logger}


app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {'message': 'Hello world!'}

@app.get("/ym")
def get_market_prods(request: Request):
    db_connection: psycopg.Connection = request.state.database
    response = db_connection.execute(SQL_GET_PRODUCTS)
    print(response)
    return {'message': response.fetchall()}

@app.get('/favicon.ico')
def get_favicon():
    return responses.FileResponse(os.path.join(ROOT_DIR, 'favicon.jpg'))