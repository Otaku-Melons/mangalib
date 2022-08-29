from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome

import datetime
import logging
import json
import sys

from BaseFunctions import Shutdown
from BaseFunctions import Cls

from Components import GetChapterSlidesInJSON
from Components import SignInAndDisableWarning
from Components import ParceTitle
from Components import ScanTitles

from BaseFunctions import GetCodeBID

#Запись лога.
CurrentTime = datetime.datetime.now()
LogFilename = "Logs\\" + str(CurrentTime)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
logging.basicConfig(filename = LogFilename, level = logging.INFO)

#Открытие браузера.
BrowserOptions = Options()
BrowserOptions.add_argument("--log-level=3")
BrowserOptions.add_argument("--disable-gpu")
Browser = Chrome(service = Service(ChromeDriverManager().install()), options = BrowserOptions)
Cls()
Browser.set_window_size(1920, 1080)
Browser.implicitly_wait(10)

#Чтение настроек.
logging.info("====== Prepare to starting ======")
Settings = {}
InFuncProgress_Shutdown = ""
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
	#Вывод в лог сообщения об активированном режиме отключения ПК после работы парсера.
	if "-s" in sys.argv:
		logging.info("Computer will be turned off after the parser is finished!")
		InFuncProgress_Shutdown = "Computer will be turned off after the parser is finished!\n"

	#Парсинг манги с созданием/перезаписью JSON.
	if "parce" in sys.argv:
		SignInAndDisableWarning(Browser, Settings)
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
					MangaName = MangaList[i]
					logging.info("Parcing: \"" + MangaName + "\". Starting...")
					InFuncProgress = ""
					InFuncProgress += InFuncProgress_Shutdown + "Parcing titles from manifest: " + str(i + 1) + " / " + str(len(MangaList)) + "\n"
					ParceTitle(Browser, MangaName, Settings, ShowProgress = InFuncProgress)
		#Парсинг одного тайтла.
		else:
			MangaName = sys.argv[2]
			logging.info("Parcing: \"" + MangaName + "\". Starting...")
			ParceTitle(Browser, MangaName, Settings, ShowProgress = InFuncProgress_Shutdown)

	#Вывод BID алиаса.
	if "ubid" in sys.argv and len(sys.argv) == 3:
		logging.info("====== Other ======")
		logging.info("Alias \"" + sys.argv[2] + "\" UBID is: " + GetCodeBID(sys.argv[2], ""))
		print("Alias \"" + sys.argv[2] + "\" UBID is: " + GetCodeBID(sys.argv[2], "") + "\nIf title has translation branches, add the \"bid\" from the browser address bar to get the desired value.")
	#Получение и сохранение данных о слайдах конкретной главы.
	elif "getsl" in sys.argv and len(sys.argv) == 3:
		SignInAndDisableWarning(Browser, Settings)
		logging.info("====== Other ======")
		GetChapterSlidesInJSON(Browser, sys.argv[2], Settings)
	#Обработка исключения: недостаточно аргументов.
	elif len(sys.argv) == 2:
		logging.error("Not enough arguments.")

#Поиск данных о манге методом перелистывания ID.
if "scan" in sys.argv:
	logging.info("====== Scanning ======")
	logging.info("Scanning site on: \"" + Settings["scan-target"] + "\"...")
	ScanTitles(Browser, Settings)

#Если передан аргумент, выключить компьютер по завершению работы.
if "-s" in sys.argv:
	if len(sys.argv) == 2:
		logging.error("Not enough arguments.")
	logging.info("Shutdowning computer.")
	Shutdown()
#Обработка исключения: недостаточно аргументов.
elif len(sys.argv) == 1:
	logging.error("Not enough arguments.")

#Закрытие браузера.
Browser.close()
Cls()