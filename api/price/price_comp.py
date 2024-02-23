# scraper.py

from seleniumbase import SB
from bs4 import BeautifulSoup as soup
import threading
from time import sleep
from typing import List


class DataScraper:
    def get_price(self, price_of_product):
        temp = ''
        found = False
        for c in price_of_product:
            try:
                int(c)
                temp += c
                found = True
            except:
                if c != ',' and found:
                    break
        return temp

    def scrape_daraz(self, search_query, sb):
        results = []

        try:
            print("daraz called")
            sb.open('https://www.daraz.com.np/')
            search_box = sb.driver.find_element('css selector', 'div.search-box__bar--29h6 input#q')
            search_box.send_keys(search_query)
            search_box.submit()

            sb.wait_for_element('css selector', 'div.box--ujueT')
            content = sb.get_page_source()
            soup_bs4 = soup(content, 'html.parser')
            product_divs = soup_bs4.select('div.box--ujueT div[data-qa-locator="product-item"]')

            for div in product_divs:
                title_of_product = div.select_one('.title-wrapper--IaQ0m').text.split('|')[0].strip()
                price_of_product = div.select_one('span.currency--GVKjl').text
                image_of_product = div.select_one('img#id-img').attrs.get('src')
                if search_query in title_of_product:


                    results.append({
                        'title': title_of_product,
                        'price': price_of_product,
                        'image': image_of_product,
                        'site': 'Daraz'
                    })

        except Exception as e:
            print(f"Error at Daraz: {e}")

        return results

    def scrape_smartdoko(self, search_query, sb):
        results = []

        try:
            print("smartdoko called")
            sb.open(f'https://smartdoko.com/search?category=all&q={search_query}&device=desktop')
            sleep(5)
            content = sb.get_page_source()
            soup_bs4 = soup(content, 'html.parser')
            product_divs = soup_bs4.find_all('div', class_='product bordered col-lg-3 col-md-6')
            print(product_divs[0] if product_divs else "No product divs found")
            for div in product_divs:
                title_of_product = div.select_one('h4 a').text
                price_of_product = div.select_one('span.price-new').text
                image_of_product = div.select_one('img.v-lazy-image').attrs.get('src')
                if search_query in title_of_product:


                    results.append({
                        'title': title_of_product,
                        'price': price_of_product,
                        'image': image_of_product,
                        'site': 'smartdoko'
                    })

        except Exception as e:
            print(f"An error occurred: {e}")

        return results

    def scrape_sastodeal(self, search_query, sb):
        results = []

        try:
            print("sastodeal called")
            sb.open(f"https://www.sastodeal.com/catalogsearch/result/?q={search_query}")

            content = sb.get_page_source()
            soup_bs = soup(content, 'html.parser')
            product_divs = soup_bs.select('div.products ol.filterproducts li.item')

            for div in product_divs:
                title_of_product = div.select_one('a.product-item-link').text
                price_of_product = div.select_one('span.price').text
                image_of_product = div.select_one('span.product-image-wrapper img').attrs.get('src')

                if search_query in title_of_product:

                    results.append({
                        'title': title_of_product,
                        'price': price_of_product,
                        'image': image_of_product,
                        'site': 'Sastodeal'
                    })

        except Exception as e:
            print(f"Error at Sastodeal: {e}")

        return results
def main(search_query: str) -> List[dict]:
    scraper = DataScraper()
    with SB(uc=True, test=False,Headless=True) as sb:
        daraz_results = scraper.scrape_daraz(search_query,sb)
        smartdoko_results = scraper.scrape_smartdoko(search_query,sb)
        sastodeal_results = scraper.scrape_sastodeal(search_query,sb)
        
        all_results = daraz_results + smartdoko_results + sastodeal_results
        return all_results
