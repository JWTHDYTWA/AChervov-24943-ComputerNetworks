import re
import asyncio

from playwright.async_api import async_playwright, BrowserContext, Locator

url_meta_trunc = R'^(/card/[^/]+/(\d+))'


def price_to_int(text: str):
    text = ''.join(filter(str.isdigit, text))
    return int(text)

async def scrape_page(context: BrowserContext, search_text, page_num):
    print(f'scrape_page(..., {search_text}, {page_num})')
    page = await context.new_page()

    try:
        url = (
            f'https://market.yandex.ru/search'
            f'?text={search_text}'
            f'&page={page_num}'
            '&how=aprice'
        )
        results = {}
        await page.goto(url=url, wait_until='load')
        await page.mouse.click(10, 10)
        product_cards = page.locator('[data-zone-name="productSnippet"]')
        card_count = await product_cards.count()
        print(f'Product count on page {page_num}: {card_count}')

        for i in range(min(card_count, 8)):
            card = product_cards.nth(i)

            product_name = await card.locator('[itemprop="name"]').text_content()
            print(f'Prod: {product_name}')

            product_price = card.locator('[data-auto="snippet-price-current"]')
            product_price = await product_price.locator('span').first.text_content()
            product_price = price_to_int(product_price)

            product_rating = card.locator('[data-zone-name="rating"]')
            rating_occur = await product_rating.count()
            if rating_occur > 0:
                product_rating = product_rating.locator('[class*="ds-text"]')
                product_rating = await product_rating.first.text_content()
                product_rating = float(product_rating)
            else:
                product_rating = None

            raw_link = await card.locator('a').first.get_attribute('href')
            url_path, product_id = re.findall(url_meta_trunc, raw_link)[0]
            product_url = 'https://market.yandex.ru' + url_path

            results[product_id] = {
                'product_id': product_id,
                'product_name': product_name,
                'product_price': product_price,
                'product_rating': product_rating,
                'product_url': product_url,
                }
    finally:
        await page.close()
    return results

async def scrape_pages(context: BrowserContext, search_text, page_nums):
    tasks = [scrape_page(context, search_text, page_n) for page_n in page_nums]
    batch = await asyncio.gather(*tasks)
    results = {}
    for result in batch:
        results |= result
    return results

async def get_screenshot(context: BrowserContext, search_text):
    page = await context.new_page()

    try:
        url = (
            f'https://market.yandex.ru/search'
            f'?text={search_text}'
            '&how=aprice'
        )
        await page.goto(url=url, wait_until='load')
        await page.mouse.click(10, 10)
        await page.screenshot(path='debug.jpg')
    finally:
        await page.close()
