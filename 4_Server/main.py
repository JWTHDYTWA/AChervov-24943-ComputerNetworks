import os
import logging

import psycopg
import fastapi.responses as responses

from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import select


class Base(DeclarativeBase):
    ...


class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column()
    product_price: Mapped[int] = mapped_column()
    product_rating: Mapped[float] = mapped_column()
    product_url: Mapped[str] = mapped_column()


ROOT_DIR = os.path.dirname(__file__)
DATABASE_URL = f"postgresql+asyncpg:///parser:{os.getenv('DB_PASS')}@localhost:5432/PDB"

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_async_session() -> AsyncSession: # type: ignore
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger('uvicorn')
    logger.info('Password: %s', os.getenv('DB_PASS'))
    
    yield {'logger': logger}
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {'message': 'Hello world!'}

@app.get("/ym")
async def get_market_prods(database: AsyncSession = Depends(get_async_session)):
    stmt = select(Product)
    
    resp = await database.execute(stmt)
    return {'message': resp.all()}

@app.get('/favicon.ico')
def get_favicon():
    return responses.FileResponse(os.path.join(ROOT_DIR, 'favicon.jpg'))