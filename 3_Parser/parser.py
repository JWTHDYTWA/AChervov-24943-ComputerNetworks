import argparse
import os
import csv
import re

from intspan import intspan

from playwright.sync_api import sync_playwright

root_dir = os.path.dirname(__file__)
screen_path = os.path.join(root_dir, 'screen.jpg')
csv_path = os.path.join(root_dir, 'results.csv')

url_meta_trunc = R'^(/card/[^/]+/(\d+))'


def price_to_int(text: str):
    text = ''.join(filter(str.isdigit, text))
    return int(text)


def main():
    arguments = argparse.ArgumentParser('Parser')
    arguments.add_argument('search', default='RTX 5070 Ti')
    arguments.add_argument('-p', '--page', default=1)
    arguments = arguments.parse_args()

    search_text = str.replace(arguments.search, ' ', '+')
    search_pages = intspan(arguments.page)
    # search_page = int(arguments.page)

    with sync_playwright() as p:
        browser = p.firefox.launch()
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        data = {}
        try:
            with open(csv_path, 'r', encoding='utf8') as f:
                reader = csv.DictReader(f)
                field_names = reader.fieldnames
                for row in reader:
                    data[row['id']] = row
        except FileNotFoundError:
            field_names = ['id', 'name', 'price', 'rating', 'url']

        for search_page in search_pages:
            url = (
                f'https://market.yandex.ru/search'
                f'?text={search_text}'
                f'&page={search_page}'
                '&how=aprice'
            )
            page.goto(url, wait_until='load')
            page.mouse.click(10, 10)
            page.screenshot(path=screen_path)

            product_cards = page.locator('[data-zone-name="productSnippet"]')
            print(f'Page {search_page}: {product_cards.count()} products')
            for i in range(min(product_cards.count(), 8)):
                card = product_cards.nth(i)

                product_name = card.locator('[itemprop="name"]').text_content()

                product_price = card.locator('[data-auto="snippet-price-current"]')
                product_price = product_price.locator('span').first.text_content()
                product_price = price_to_int(product_price)

                product_rating = card.locator('[data-zone-name="rating"]')
                if product_rating.count() > 0:
                    product_rating = product_rating.locator('[class*="ds-text"]')
                    product_rating = product_rating.first.text_content()
                    product_rating = float(product_rating)
                else:
                    product_rating = None

                raw_link = card.locator('a').first.get_attribute('href')
                url_path, product_id = re.findall(url_meta_trunc, raw_link)[0]
                product_url = 'https://market.yandex.ru' + url_path

                data[product_id] = {
                    'id': product_id,
                    'name': product_name,
                    'price': product_price,
                    'rating': product_rating,
                    'url': product_url,
                }

                print(i, product_price, product_name)

        with open(csv_path, 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=field_names, lineterminator='\n')
            writer.writeheader()
            writer.writerows(data.values())


if __name__ == '__main__':
    main()
