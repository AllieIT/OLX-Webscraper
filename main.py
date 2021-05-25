import requests
from bs4 import BeautifulSoup
import pandas as pd
import spacy
import re

nlp = spacy.load("pl_core_news_sm")


def clear_tags(html):
    expr = re.compile('<.*?>')
    return re.sub(expr, '', html)


headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }

full_list = []


for i in range(1, 8):
    url = "https://www.olx.pl/praca/krakow" + '/q-student' + '/?page=' + str(i)
    req = requests.get(url, headers)
    soup = BeautifulSoup(req.content, 'html.parser')

    specific_h3 = soup.find_all('h3', {'class': 'lheight22'})
    containers = [h3.parent for h3 in specific_h3]
    data_list = []

    for iterator, container in enumerate(containers):
        name = container.find_all('strong')
        str_name = name[0].contents[0]

        link = container.find_all('a')
        str_link = link[0].get('href')

        salary = ''
        salary_div = container.find('div', {'class': 'list-item__price'})
        labels = salary_div.find_all('span', {'class': 'price-label'})
        period = salary_div.find_all('span', {'class': 'salary-period'})
        if len(labels) == 1:
            salary = labels[0].contents[0] + ' ' + str(period[0].contents[0])
        elif len(labels) == 2:
            price1 = labels[0].contents[1]
            price2 = labels[1].contents[1]
            salary = 'od' + str(price1) + ' do' + str(price2) + ' ' + str(period[0].contents[0])

        subpage_req = requests.get(str_link, headers)
        subpage_soup = BeautifulSoup(subpage_req.content, 'html.parser')

        ward = subpage_soup.find('span', {'class': 'css-1c0ed4l'}).contents[0]
        description = subpage_soup.find('div', {'class': 'css-2t3g1w-Text'}).contents
        str_description = ''
        for d in description:
            cleared = clear_tags(str(d))
            str_description += (' ' + cleared)

        doc = nlp(str_description)
        has_keyword = False
        keywords = ['uczeń', 'maturzysta']

        for token in doc:
            if token.lemma_ in keywords:
                print(token.text)
                has_keyword = True

        data_row = [str_name, str_link, salary, str(ward), has_keyword]
        data_list.append(data_row)

    print(data_list)
    full_list.extend(data_list)

print(full_list)
df = pd.DataFrame.from_records(full_list)
df.to_csv('export.csv', index=False, sep=';', encoding='utf-8')