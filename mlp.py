from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome

import datetime
import logging
import json
import sys

from BaseFunctions import DisableAgeLimitWarning
from BaseFunctions import PrintProgress
from BaseFunctions import LogIn
from BaseFunctions import Cls

from Components import ParceTitle
from Components import ScanTitles

#Запись лога.
CurrentTime = datetime.datetime.now()
LogFilename = "Logs\\" + str(CurrentTime)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
logging.basicConfig(filename = LogFilename, level = logging.INFO)

#Открытие браузера.
BrowserOptions = Options()
BrowserOptions.add_argument("--log-level=3")
Browser = Chrome(service = Service(ChromeDriverManager().install()), options = BrowserOptions)
Cls()
Browser.set_window_size(1920, 1080)
Browser.implicitly_wait(10)

#Чтение настроек.
logging.info("====== Prepare to parcing ======")
Settings = {}
with open("Settings.json") as FileRead:
		Settings = json.load(FileRead)
		#Проверка загрузки файла настроек.
		if Settings == None:
			logging.error("The settings file could not be opened.")
		else:
			#Проверка директории сохранения данных.
			logging.info("The settings file was found successfully.")
			if Settings["save-directory"] == "":
				Settings["save-directory"] = "manga"
				logging.info("Save directory set as default.")
			else:
				logging.info("Save directory set as " + Settings["save-directory"] + ".")

#Обработка аргументов.
if len(sys.argv) > 2:
	#Парсинг манги с созданием/перезаписью JSON.
	if "parce" in sys.argv:
		if Settings["disable-age-limit-warning"] == True:
			DisableAgeLimitWarning(Browser)
			logging.info("Age limit warning disabled.")
		if Settings["sign-in"] == True:
			if Settings["email"] != "" and Settings["password"] != "":
				LogIn(Browser, Settings)
				logging.info("Sign in as \"" + Settings["email"] + "\".")
			else:
				logging.error("Uncorrect user data! Check \"Settings.json\".")
		logging.info("====== Parcing ======")
		#Парсинг всей манги, о которой есть информация в манифесте.
		if "-all" in sys.argv:
			MangaList = []
			with open(Settings["save-directory"] + "\\#Manifest.json") as FileRead:
				MangaList = json.load(FileRead)
				#Проверка загрузки манифеста.
				if MangaList == None:
					logging.error("The manifest could not be opened.")
				else:
					#Проверка директории сохранения данных.
					logging.info("Manifest successfully was loaded. Titles descripted:" + str(len(MangaList)) + ".")
				for i in range(0, len(MangaList)):
					PrintProgress("Parcing titles from manifest:", str(i + 1), str(len(MangaList)))
					MangaName = MangaList[i]
					logging.info("Parcing: \"" + MangaName + "\". Starting...")
					ParceTitle(Browser, MangaName, Settings, ShowProgress = False)
		#Парсинг одного тайтла.
		else:
			MangaName = sys.argv[2]
			logging.info("Parcing: \"" + MangaName + "\". Starting...")
			ParceTitle(Browser, MangaName, Settings, ShowProgress = True)

#Поиск данных о манге методом перелистывания ID.
if "scan" in sys.argv:
	ScanTitles(Browser, Settings)

#Исключение: недостаточно аргументов.
if len(sys.argv) == 1:
	logging.error("Not enough arguments.")

#Закрытие браузера.
Browser.close()