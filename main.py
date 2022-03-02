import requests
from bs4 import BeautifulSoup
import pandas as pd
import spacy
import re
import os
import time
import json

print("Initializing SpaCy...")
nlp = spacy.load('pl_core_news_sm')


class Offer:
    def __init__(self, URL, name, district, price, date_added, description):
        self.URL = URL
        self.name = name
        self.district = district
        self.price = price
        self.date_added = date_added
        self.description = description.strip()
        self.has_keywords = False

    def check_for_keywords_in_description(self, keywords):
        doc = nlp(self.description)

        self.has_keywords = True

        for keyword in keywords:
            has_keyword = False
            for token in doc:
                if token.lemma_ == keyword:
                    has_keyword = True
            if not has_keyword:
                self.has_keywords = False
                break

    def __str__(self):
        ret = self.name + '\n' + self.URL + '\n' + str(self.price) + ' zł\n' + self.district + ', Kraków\n' + self.date_added + '\n\n'
        ret += self.description + '\n\n' + '\n___________________________\n'
        return ret


class OLXWebScraper:

    HEADERS = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }
    NO_CHUNKS = 50
    DATA_FILENAME = "data.txt"

    def __init__(self, search_scope, query):
        self.subpage_links = set()
        self.search_scope = search_scope
        self.query = query
        self.offers = []
        self.read_data()
        self.initialize_offer_links()

    @staticmethod
    def clear_tags(html):
        expr = re.compile('<.*?>')
        return re.sub(expr, '', html)

    @staticmethod
    def divide_list(li, n):
        for i in range(0, len(li), n):
            yield li[i:i + n]

    def initialize_offer_links(self):
        print("Fetching offer URLs...")
        try:
            with open('data/offer_links.txt', 'r') as read_file:
                mod_date = os.path.getmtime('data/offer_links.txt',)
                time_since_modification = time.time() - mod_date
                if time_since_modification > 60 * 60 * 6: # 6 Hours
                    self.get_offer_links_from_web()
                else:
                    lines = read_file.readlines()
                    for line in lines:
                        if len(line) > 1:
                            self.subpage_links.add(line.strip())
        except FileNotFoundError:
            self.get_offer_links_from_web()

    def get_offer_links_from_web(self):
        page_no = 0
        while True:
            page_no += 1
            URL = self.search_scope + '/q-' + self.query + '/?page=' + str(page_no)
            res = requests.get(URL, self.HEADERS)

            # See if the page was redirected to determine if it reached the last page
            if len(res.history) > 0 and page_no != 1:
                print('Task completed')
                break
            soup = BeautifulSoup(res.content, 'html.parser')

            # Scrape all links leading to OLX for further use
            new_links = set(map(lambda x: x['href'] if 'olx' in x['href'] else None,
                                soup.find_all('a', {'class': 'linkWithHash'})))
            self.subpage_links = self.subpage_links.union(new_links)
        self.subpage_links.remove(None)

        with open('data/offer_links.txt', 'w') as save_file:
            for link in self.subpage_links:
                save_file.write(link + '\n')

    def scrape_offers_from_website(self):
        print("Scraping offers...")
        chunk_size = len(self.subpage_links) // self.NO_CHUNKS
        chunk_list = list(self.divide_list(list(self.subpage_links), chunk_size))
        i = 0

        print(len(self.offers))
        for chunk in chunk_list:
            i += 1
            print(f"Chunk {i - 1} of {self.NO_CHUNKS}...")
            offers_to_dump = []

            for link in chunk:
                if any(offer.URL == link for offer in self.offers):
                    continue
                res = requests.get(link, self.HEADERS)
                soup = BeautifulSoup(res.content, 'html.parser')
                try:
                    name = soup.find('h1', { 'data-cy': 'ad_title' }).text
                    price = ''
                    try:
                        price_div = soup.find('div', {'data-testid': 'ad-price-container' })
                        price = price_div.find('h3').text
                    except AttributeError:
                        price = '0 zł'
                    price = int(price.replace(' ', '')[:-2])
                    date_added = soup.find('span', {'data-cy': 'ad-posted-at'}).text

                    script_text = str(soup.find('script', {'id': 'olx-init-config'}))
                    prerender = script_text.splitlines()[4].strip()
                    district = [field for field in prerender.split(',') if 'districtName' in field]
                    split = district[0].split('\"')
                    district = split[3][:-1]

                    description = soup.find('div', {'class': 'css-g5mtbi-Text'}).text
                    offer = Offer(link, name, district, price, date_added, description)
                    offers_to_dump.append(offer)
                    self.offers.append(offer)
                except:
                    pass
                    # Offer no longer Valid!!!

            if offers_to_dump:
                self.save_data(self.offers)

    def save_data(self, dump_list):
        with open(f"data/{self.DATA_FILENAME}", 'w', encoding='utf-8') as save_file:
            json_string = json.dumps([offer.__dict__ for offer in dump_list], indent=4, ensure_ascii=False)
            save_file.write(json_string)

    def read_data(self):
        try:
            with open(f"data/{self.DATA_FILENAME}", 'r', encoding='utf-8') as read_file:
                print("Reading data from file...")
                data = json.loads(read_file.read())
                for offer in data:
                    self.offers.append(Offer(offer['URL'],
                                             offer['name'],
                                             offer['district'],
                                             offer['price'],
                                             offer['date_added'],
                                             offer['description']))
                print("Done")
        except FileNotFoundError:
            self.offers = []

    def check_for_keywords_in_description(self, keywords):
        print("Looking for offers by keywords...")
        resulting_offers = []
        i = 0
        for offer in self.offers:
            i += 1
            if i % 30 == 0:
                print(str(round(i / len(self.offers) * 100, 2)) + "%")
            offer.check_for_keywords_in_description(keywords)
            if offer.has_keywords:
                resulting_offers.append(offer)
        print(f"Found {len(resulting_offers)} matching results: ")
        print("________________________________________")
        for offer in resulting_offers:
            print(offer)
        return resulting_offers


def transform_keywords(kwds):
    text = ' '.join(kwds)
    doc = nlp(text)
    transformed_keywords = [token.lemma_ for token in doc]
    return transformed_keywords

def main():
    search_URL = 'https://www.olx.pl/nieruchomosci/mieszkania/krakow'
    query = ''  # Query for the OLX search engine, if there is none, leave empty string
    keywords = ['garaż', 'dwupokojowe', 'drugie piętro']
    keywords = transform_keywords(keywords)

    print("Done")
    scraper = OLXWebScraper(search_URL, query)
    scraper.scrape_offers_from_website()
    scraper.check_for_keywords_in_description(keywords)

main()