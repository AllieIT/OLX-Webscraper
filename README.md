# OLX Webscraper

This project was created in response to inaccurate results displaying using default search engine on internet marketplace OLX.pl. Program crawls through all flat offers at any given moment and stores information about them in JSON files. This data can be further used to search for given keywords in offer description, giving more accurate results, ommiting additional appearances of so-called "promoted offers" and giving the user insight into many suggestions which otherwise would be more difficult to find.

# Installation

To use the program, you need to install dependencies:

```
pip install pip setuptools wheel
pip install pandas bs4 spacy
python -m spacy download pl_core_news_sm
```

Main package needed here is a Natural Language Processing package called SpaCy. It is used to provide better, accurate results by transforming the keywords and the description of the offer to their basic lexical form.

# Usage and working principle

First, the program takes a `search_URL` and `query` as an argument. The last part of the URL can be changed to any city in Poland, giving results in that location - it is set to Kraków by default. The `query` can be anything - it is however not recommended to put anything inside, because it may provide inaccurate results *(the search engine of OLX.pl seems biased towards 'promoted offers').* 

The `keywords` list can be modified into a list of any number of elements. Every word inside is then lemmatized and passed as an argument to the `check_for_keywords_in_description()` method.

OLXWebScraper object is initialized and tries to read cached data from the data folder. If it fails to retrieve URLs to offers, which are stored in **offer_links.txt** file or the cache is outdated (default to 6 hours), then it scrapes the data from OLX.pl page and stores it in file.

`scrape_offers_from_website()` method collects the data from the set of URLs retrieved from file or the web. It uses BeautifulSoup package to find specific information and creates Offer objects, which contain information scraped from the website. This data is then stored in a JSON-formatted file. To prevent crashes from destroying the data, all of URLs are split into chunks and the data is saved to the file after successfully scraping given chunk. After restarting the program, saved data gets loaded from the file and the program starts its work just where it abruptly ended, saving time and resources.

The last method, `check_for_keywords_in_description()` uses SpaCy to lemmatize every word in description and compare them with given keywords. It then returns offers that match the query and prints all of the data in user-friendly way

[Google Colab link](https://colab.research.google.com/drive/1XWXXtYvm7WyVgBVGPR2Na8VRNOVPrnmi#scrollTo=Asws-5yNaTHN)
