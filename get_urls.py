import json
import requests
from bs4 import BeautifulSoup

import pandas as pd

url = "https://www.jazzdisco.org/"

page = requests.get(url)
soup = BeautifulSoup(page.text)

def get_urls():
    for a in soup.find_all("a"):
        if "-" in a["href"]:
            yield (a.text, url[:-1] + a["href"] + "discography/")

urls = dict(get_urls())
json.dump(urls, open("urls.json", "w"))
