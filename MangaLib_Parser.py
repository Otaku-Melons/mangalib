from textwrap import indent
from selenium.webdriver import Chrome
import json

from Components import PrepareToParcingChapter
from Components import GetChaptesNames
from Components import GetChaptesLinks
from Components import GetMangaSlidesUrlArray

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from time import sleep

from BaseFunctions import ReplaceEndlToComma
from BaseFunctions import RemoveSpaceSymbols

#Загрузка и настройка браузера.
Browser = Chrome()
Browser.set_window_size(1920, 1080)
Browser.get("https://mangalib.me/martial-peak?section=info")

BodyHTML = Browser.execute_script("return document.body.innerHTML;")
Soup = BeautifulSoup(BodyHTML, "html.parser")
MangaNameRU = Soup.find('div', {'class': 'media-name__main'}).get_text()
MangaNameEN = Soup.find('div', {'class': 'media-name__alt'}).get_text()
AnotherName = ReplaceEndlToComma(Soup.find_all('div', {'class': 'media-info-list__value'})[-1].get_text())
Description = RemoveSpaceSymbols(Soup.find('div', {'class': 'media-description__text'}).get_text())


#Закрытие браузера.
Browser.close()


JSON = { 
    "id" : 0, 
    "img" : "ARR", 
    "en_name" : MangaNameEN,
    "rus_name" : MangaNameRU, 
    "another_name" : AnotherName,
    "dir" : "___",
    "description" : Description,
    "issue_year" : "___",
    "avg_rating" : "___",
    "admin_rating" : "",
    "count_rating" : "___",
    "age_limit" : "___",
    "status" : "ARR",
    "count_bookmarks": 0,
    "total_votes": 0,
    "total_views": 1230982,
    "type": {
        "id": 0,
        "name": "Манга"
    }
}


with open("data.json", "w", encoding="utf-8") as FileWrite:
    json.dump(JSON, FileWrite, ensure_ascii = False, indent = 4, separators = (',', ' : ')) 


