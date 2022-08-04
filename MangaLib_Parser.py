from textwrap import indent
from selenium.webdriver import Chrome
import json

from Components import PrepareToParcingChapter
from Components import GetChaptesNames
from Components import GetChaptesLinks
from Components import GetMangaSlidesUrlArray
from Components import GetMangaData

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from time import sleep

from BaseFunctions import ReplaceEndlToComma
from BaseFunctions import RemoveSpaceSymbols
from BaseFunctions import LiteralToInt
from BaseFunctions import RemoveHTML

#Загрузка и настройка браузера.
Browser = Chrome()
Browser.set_window_size(1920, 1080)

JSON = GetMangaData(Browser, "martial-peak")

#Закрытие браузера.
Browser.close()


with open("data.json", "w", encoding = "utf-8") as FileWrite:
    json.dump(JSON, FileWrite, ensure_ascii = False, indent = 4, separators = (',', ' : ')) 


