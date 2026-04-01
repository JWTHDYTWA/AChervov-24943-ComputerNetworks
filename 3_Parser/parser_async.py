import argparse
import os
import csv
import re
import asyncio

from intspan import intspan
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright, BrowserContext, Locator

root_dir = os.path.dirname(__file__)
screen_path = os.path.join(root_dir, 'screen.jpg')
csv_path = os.path.join(root_dir, 'results.csv')

url_meta_trunc = R'^(/card/[^/]+/(\d+))'


def price_to_int(text: str):
    text = ''.join(filter(str.isdigit, text))
    return int(text)

# async def extract_card(cards: Locator, n):
#     card = cards.nth(n)

#     product_name = await card.locator('[itemprop="name"]').text_content()
#     print(f'Prod: {product_name}')

#     product_price = card.locator('[data-auto="snippet-price-current"]')
#     product_price = await product_price.locator('span').first.text_content()
#     product_price = price_to_int(product_price)

#     product_rating = card.locator('[data-zone-name="rating"]')
#     rating_occur = await product_rating.count()
#     if rating_occur > 0:
#         product_rating = product_rating.locator('[class*="ds-text"]')
#         product_rating = await product_rating.first.text_content()
#         product_rating = float(product_rating)
#     else:
#         product_rating = None

#     raw_link = await card.locator('a').first.get_attribute('href')
#     url_path, product_id = re.findall(url_meta_trunc, raw_link)[0]
#     product_url = 'https://market.yandex.ru' + url_path

#     results['product_id'] = {
#         'id': product_id,
#         'name': product_name,
#         'price': product_price,
#         'rating': product_rating,
#         'url': product_url,
#         }
#     ...

async def scrape_page(context: BrowserContext, search_text, page_num):
    print(f'scrape_page(..., {search_text}, {page_num})')
    page = await context.new_page()
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
            'id': product_id,
            'name': product_name,
            'price': product_price,
            'rating': product_rating,
            'url': product_url,
            }
    return results

async def scrape_pages(context: BrowserContext, search_text, page_nums):
    tasks = [scrape_page(context, search_text, page_n) for page_n in page_nums]
    batch = await asyncio.gather(*tasks)
    results = {}
    for result in batch:
        results |= result
    return result


async def main():
    arguments = argparse.ArgumentParser('Parser')
    arguments.add_argument('search', default='RTX 5070 Ti')
    arguments.add_argument('-p', '--page', default=1)
    arguments = arguments.parse_args()

    search_text = str.replace(arguments.search, ' ', '+')
    search_pages = intspan(arguments.page)
    # search_page = int(arguments.page)

    async with async_playwright() as p:
        browser = await p.firefox.launch()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )

        data = {}
        try:
            with open(csv_path, 'r', encoding='utf8') as f:
                reader = csv.DictReader(f)
                field_names = reader.fieldnames
                for row in reader:
                    data[row['id']] = row
        except FileNotFoundError:
            field_names = ['id', 'name', 'price', 'rating', 'url']

        # ↑↓↑↓↑↓↑↓

        results = await scrape_pages(context, search_text, search_pages)
        data |= results

        with open(csv_path, 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=field_names, lineterminator='\n')
            writer.writeheader()
            writer.writerows(data.values())


if __name__ == '__main__':
    asyncio.run(main())
