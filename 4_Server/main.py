import os
import logging

import psycopg

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager


db_conninfo = (
    "dbname=PDB "
    "user=parser "
    f"password={os.getenv('DB_PASS')} "
    "host=localhost")

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
def get_market_prods():
    return {'message': None}