from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import json

#=== ПАРСИНГ ГЛАВ ===#
from BaseFunctions import GetBID
from BaseFunctions import PrepareToParcingChapter
from BaseFunctions import GetChaptersNames
from BaseFunctions import GetChaptersLinks
from BaseFunctions import GetMangaData
from BaseFunctions import MakeContentData

#Парсинг одного тайтла.
def ParceTitle(Browser, MangaName, Settings, ShowProgress):
	#Получение данных о манге.
	JSON = GetMangaData(Browser, MangaName)
	BranchesCount = len(JSON["branches"])

	#Проверка лицензии.
	if JSON['is_licensed'] == False:
		#Получение BID веток.
		BIDs = None
		if BranchesCount > 1:
			BIDs = GetBID(Browser, MangaName, BranchesCount)
		logging.info("Parcing: \"" + MangaName + "\". Branches count: " + str(BranchesCount) + ".")
		#Если не лицензировано, парсить каждую ветку.
		for i in range(0, len(JSON["branches"])):
			BID = ""
			BIDlog = "none"
			if BIDs is None:
				PrepareToParcingChapter(Browser, MangaName, JSON['age_limit'], BIDs)
			else:
				PrepareToParcingChapter(Browser, MangaName, JSON['age_limit'], BIDs[i])
				BID = "?bid=" + str(BIDs[i])
				BIDlog = str(BIDs[i])
			ChaptersNames = GetChaptersNames(Browser)
			ChaptersLinks = GetChaptersLinks(Browser)
			logging.info("Parcing: \"" + MangaName + "\". Branch ID: " + BIDlog + ". Chapters in branch: " + str(len(ChaptersLinks)) + ".")
			JSON["content"][str(i + 1)] = MakeContentData(i + 1, ChaptersNames, ChaptersLinks, BID, Browser, Settings, ShowProgress)
	else:
		 #Если лицензировано, ничего больше не парсить и вывести уведомление.
		 logging.info("Parcing: \"" + MangaName + "\". Licensed. Skipped.")
	
	with open(Settings["save-directory"] + "\\" + MangaName + ".json", "w", encoding = "utf-8") as FileWrite:
		json.dump(JSON, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))
		logging.info("Parcing: \"" + MangaName + "\". JSON file was created.")
	logging.info("Parcing: \"" + MangaName + "\". SUCCESSFULLY!!!")

#Сканирование страницы каталога и получение списка тайтлов.
def ScanTitles(Browser, Settings):
	Browser.get(Settings["scan-target"])
	BodyHTML = Browser.execute_script("return document.body.innerHTML;")
	Soup = BeautifulSoup(BodyHTML, "lxml")
	MediaCards = Soup.find_all('a', {'class': 'media-card'})
	TitlesAliasArray = []

	for i in range(0, len(MediaCards)):
		TitlesAliasArray.append(str(MediaCards[i]["href"]).split('/')[3])

	with open(Settings["save-directory"] + "\\#Manifest.json", "w", encoding = "utf-8") as FileWrite:
		json.dump(TitlesAliasArray, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))

		






