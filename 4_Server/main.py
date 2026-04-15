import os
import logging

from fastapi.responses import FileResponse
from fastapi import FastAPI, Depends, Request, HTTPException, status
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, update
from playwright.async_api import async_playwright, BrowserContext, Locator
from intspan import intspan

from scraper.scraper import scrape_pages, get_screenshot


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column()
    product_price: Mapped[int] = mapped_column()
    product_rating: Mapped[float | None] = mapped_column()
    product_url: Mapped[str] = mapped_column()


ROOT_DIR = os.path.dirname(__file__)
DATABASE_URL = f"postgresql+asyncpg://postgres:{os.getenv('DB_PASS')}@database:5432/postgres"

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_async_session() -> AsyncSession: # type: ignore
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger('uvicorn')
    logger.info('Password: %s', os.getenv('DB_PASS'))
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_playwright() as p:
        browser = await p.firefox.launch()
        app.state.browser_context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {'message': 'Hello world!'}

@app.get("/parse")
async def root(text = None, pages = '1', session: AsyncSession = Depends(get_async_session)):
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search text is empty"
        )
    
    results = await scrape_pages(
        context = app.state.browser_context,
        search_text = text,
        page_nums = intspan(pages)
    )
    if not results:
        return {'results': 0}

    results = list(results.values())

    stmt = insert(Product).values(results)
    upd_stmt = stmt.on_conflict_do_update(
        index_elements=['product_id'],
        set_={col.name: col for col in stmt.excluded if not col.primary_key}
    )
    await session.execute(upd_stmt)
    await session.commit()

    return {'results': len(results)}

@app.get("/pull")
async def get_market_prods(session: AsyncSession = Depends(get_async_session)):
    stmt = select(Product)
    resp = await session.execute(stmt)
    products = resp.scalars().all()
    return {'message': [
        {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "product_price": p.product_price,
            "product_rating": p.product_rating,
            "product_url": p.product_url
        } for p in products
    ]}

@app.get("/screen")
async def root(text = None):
    await get_screenshot(
        context = app.state.browser_context,
        search_text = text
    )
    return FileResponse('debug.jpg')

# @app.get('/favicon.ico')
# async def get_favicon():
#     return responses.FileResponse(os.path.join(ROOT_DIR, 'favicon.jpg'))