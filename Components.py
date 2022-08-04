from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from time import sleep

from BaseFunctions import RemoveHTML
from BaseFunctions import RemoveSpaceSymbols

#Открывает панель для получения названий глав, ссылок на главы и слайдов.
def PrepareToParcingChapter(Browser):
    #Ожидание полной подгрузки страницы.
    Wait = WebDriverWait(Browser, 500)
    Wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "media-chapter__name")))

    #Получение ссылки на последнюю главу.
    BodyHTML = Browser.execute_script("return document.body.innerHTML;")
    Soup = BeautifulSoup(BodyHTML, "html.parser")
    LastChapter = Soup.find_all('div', {'class': 'media-chapter__name text-truncate'})[0]
    Soup = BeautifulSoup(str(LastChapter), "html.parser")
    LastChapter = Soup.find('a')

    #Переход к последней главе и отключение уведомлений.
    Browser.get("https://mangalib.me" + LastChapter['href'])
    Wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "control__text")))
    Browser.find_element(By.CLASS_NAME, 'control__text').click()
    Browser.find_element(By.CLASS_NAME, 'reader-caution-continue').click()
    Browser.find_elements(By.CLASS_NAME, 'reader-header-action__text')[1].click()

#Получение списка названий глав.
def GetChaptesNames(Browser):
    BodyHTML = Browser.execute_script("return document.body.innerHTML;")
    Soup = BeautifulSoup(BodyHTML, "html.parser")
    ChaptersNames = Soup.find_all('a', {'class': 'menu__item'})
    Bufer = []
    for InObj in ChaptersNames:
        Bufer.append(RemoveSpaceSymbols(RemoveHTML(InObj)))
    ChaptersNames = Bufer
    Bufer = []
    return ChaptersNames

#Получение списка ссылок на главы.
def GetChaptesLinks(Browser):
    BodyHTML = Browser.execute_script("return document.body.innerHTML;")
    Soup = BeautifulSoup(BodyHTML, "html.parser")
    ChaptersLinks = Soup.find_all('a', {'class': 'menu__item'})
    Bufer = []
    for InObj in ChaptersLinks:
        Bufer.append(RemoveSpaceSymbols(RemoveHTML(InObj['href'])))
    ChaptersLinks = Bufer
    Bufer = []
    return ChaptersLinks

#Получение списка ссылок на слайды манги. Принимает подстроку с относительным URL главы.
def GetMangaSlidesUrlArray(Browser, ChapterLink):
    Browser.get("https://mangalib.me" + ChapterLink)
    BodyHTML = Browser.execute_script("return document.body.innerHTML;")
    Soup = BeautifulSoup(BodyHTML, "html.parser")
    FramesCount = Soup.find('select', {'id': 'reader-pages'})
    FramesCount = RemoveHTML(list(FramesCount)[-1])
    FramesCount = FramesCount.split()[-1]

    #Получение ссылок на кадры главы.
    for i in range(int(FramesCount) - 1):
        Browser.find_element(By.CLASS_NAME, 'reader-view__container').click()
        sleep(1)
    BodyHTML = Browser.execute_script("return document.body.innerHTML;")
    Soup = BeautifulSoup(BodyHTML, "html.parser")
    SmallSoup = BeautifulSoup(str(Soup.find('div', {'class': 'reader-view__container'})), "html.parser")
    FramesLinksArray = SmallSoup.find_all('img')
    FrameLinks = []
    for i in range(len(FramesLinksArray)):
        FrameLinks.append(FramesLinksArray[i]['src'])
    return FrameLinks

'''
PrepareToParcingChapter(Browser)
ChaptesNames = GetChaptesNames(Browser)
ChaptesLinks = GetChaptesLinks(Browser)
MangaSlidesUrlArray = GetMangaSlidesUrlArray(Browser, ChaptesLinks[-1])

print(MangaSlidesUrlArray)
'''