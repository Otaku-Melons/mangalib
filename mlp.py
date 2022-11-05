#!/usr/bin/env python3.9

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome
from PIL import ImageFile
from time import sleep

import datetime
import logging
import json
import time
import sys
import os

from BaseFunctions import SignInAndDisableWarning
from BaseFunctions import GetContentServersList
from BaseFunctions import SecondsToTimeString
from BaseFunctions import GetSynt_BranchID
from BaseFunctions import Shutdown
from BaseFunctions import Cls

from Components import GetChapterSlidesInJSON
from Components import ChromeHeadlessTest
from Components import UpdateTitle
from Components import ParceTitle
from Components import ScanTitles
from Components import Amend

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ЛОГОВ <<<<< #
#==========================================================================================#

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Время запуска скрипта.
StartTime = time.time()
# Формирование пути к файлу лога.
LogFilename = "Logs\\" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
# Установка конфигнурации.
logging.basicConfig(filename = LogFilename, encoding="utf-8", level = logging.INFO)

#==========================================================================================#
# >>>>> ОТКРЫТИЕ БРАУЗЕРА <<<<< #
#==========================================================================================#

# Расположении папки установки веб-драйвера в директории скрипта.
os.environ["WDM_LOCAL"] = "1"
# Разрешить чтение усечённых файлов.
ImageFile.LOAD_TRUNCATED_IMAGES = True
# Установка параметров работы браузера: отключение вывода логов в консоль, отключение аппаратного ускорения.
BrowserOptions = Options()
BrowserOptions.add_argument("--log-level=3")
BrowserOptions.add_argument("--disable-gpu")
BrowserOptions.add_argument("--disable-blink-features=AutomationControlled")
# Загрузка веб-драйвера и установка его в качестве используемого модуля.
Browser = Chrome(service = Service(ChromeDriverManager().install()), options = BrowserOptions)
# Очистка куков перед запуском (предположительный фикс бага авторизации).
Browser.delete_all_cookies()
# Очистка консоли от данных о сессии.
Cls()
# Установка размера окна браузера на FullHD для корректной работы сайтов.
Browser.set_window_size(1920, 1080)

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Вывод в лог заголовка: подготовка скрипта к работе.
logging.info("====== Prepare to starting ======")
# Запись времени начала работы скрипта.
logging.info("Script started at " + str(CurrentDate)[:-7] + ".")
# Запись команды, использовавшейся для запуска скрипта.
logging.info("Launch command: \"" + " ".join(sys.argv[1:len(sys.argv)]) + "\".")
# Инициализация хранилища настроек со стадартными значениями.
Settings = {
	"domain": "mangalib",
    "directory" : "",
    "scan-target" : "",
    "disable-age-limit-warning": True,
    "sign-in": False,
    "email": "",
    "password": "",
    "delay": 5,
    "getting-slide-sizes": False,
    "server": "main"
}

# Открытие файла настроек.
try:
	with open("Settings.json") as FileRead:
			Settings = json.load(FileRead)
			# Проверка успешной загрузки файла.
			if Settings == None:
				# Запись в лог ошибки о невозможности прочитать битый файл.
				logging.error("Unable to read \"Settings.json\". File is broken.")
			else:
				# Запись в лог сообщения об успешном чтении файла настроек.
				logging.info("The settings file was found successfully.")

				# Если директория загрузки не установлена, задать значение по умолчанию.
				if Settings["directory"] == "":
					# Установка директории по умолчанию на основе домена.
					Settings["directory"] = Settings["domain"].replace("lib", "")
					# Запись в лог сообщения об установке стандартной директории загрузки.
					logging.info("Save directory set as default.")
				else:
					# Запись в лог сообщения об установке директории загрузки.
					logging.info("Save directory set as " + Settings["directory"] + ".")

				# Если директория не существует, тогда создать её.
				if os.path.exists(Settings["directory"]) == False:
						os.makedirs(Settings["directory"])

				# Преобразование названия домена в URL целевого сайта.
				Settings["domain"] = "https://" + Settings["domain"] + ".me/"
				# Запись в лог сообщения об установке домена.
				logging.info("Domain set as \"" + Settings["domain"] + "\".")

				# Вывести сообщение об отключеннии получения размеров слайдов.
				if Settings["getting-slide-sizes"] == False:
					logging.info("Images sizing is disabled.")

except EnvironmentError:
	# Запись в лог ошибки о невозможности открытия файла настроек.
	logging.error("Unable to open \"Settings.json\". All options set as default.")

#==========================================================================================#
# >>>>> ОБРАБОТКА СПЕЦИАЛЬНЫХ ФЛАГОВ <<<<< #
#==========================================================================================#

# Активна ли опция выключения компьютера по завершении работы парсера.
IsShutdowAfterEnd = False
# Сообщение для внутренних функций: выключение ПК.
InFuncMessage_Shutdown = ""
# Активен ли режим перезаписи при парсинге.
IsForceModeActivated = False
# Сообщение для внутренних функций: режим перезаписи.
InFuncMessage_ForceMode = ""
# Запустить ли функцию amend по завершению работы.
AmendAfterWork = False
# Сообщение для внутренних функций: будет запущена команда amend после обработки.
InFuncMessage_AmendAfterWork = ""

# Обработка флага: режим перезаписи.
if "-f" in sys.argv:
	# Включение режима перезаписи.
	IsForceModeActivated = True
	# Запись в лог сообщения о включении режима перезаписи.
	logging.info("Force mode: ON")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: ON\n"
else:
	# Запись в лог сообщения об отключённом режиме перезаписи.
	logging.info("Force mode: OFF")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: OFF\n"

# Обработка флага: выключение ПК после завершения работы скрипта.
if "-s" in sys.argv:
	# Включение режима.
	IsShutdowAfterEnd = True
	# Запись в лог сообщения о том, что ПК будет выключен после завершения работы.
	logging.info("Computer will be turned off after the parser is finished!")
	# Установка сообщения для внутренних функций.
	InFuncMessage_Shutdown = "Computer will be turned off after the parser is finished!\n"

# Обработка флага: запустить ли функцию amend по завершению работы.
if "-am" in sys.argv:
	# Проверка наличия нужных команд.
	if "parce" in sys.argv or "update" in sys.argv:
		# Включение автоматического исправления.
		AmendAfterWork = True
		# Запись в лог сообщения о том, что по завершению работы будет запущена функция amend.
		logging.info("Amendid will be started after finishing.")
		# Установка сообщения для внутренних функций.
		InFuncMessage_AmendAfterWork = "Amendid will be started after finishing current task.\n"
		# Список файлов для обработки.
		global AmendAfterWork_TitleList
		AmendAfterWork_TitleList = list()
	else:
		# Запись в лог сообщения об ошибке: неверная команда для использования флага.
		logging.error("Flag \"-am\" is not applicable to this method.")

#==========================================================================================#
# >>>>> ОБРАБОТКА ОСНОВНЫХ КОММАНД <<<<< #
#==========================================================================================#

# Двухкомпонентные команды: parce, update, getsl, ubid, scan.
if len(sys.argv) >= 3:
	# Вход на сайт и отключение уведомления о возрастном ограничении согласно настройкам.
	SignInAndDisableWarning(Browser, Settings)

	# Парсинг тайтлов.
	if sys.argv[1] == "parce":
		# Вывод в лог заголовка: парсинг.
		logging.info("====== Parcing ======")

		# Если вместо алиаса установлен флаг -all, начать парсинг всех тайтлов из манифеста, иначе провести парсинг по переданному алиасу.
		if sys.argv[2] == "-all":
			# Открытие манифеста.
			if os.path.exists(Settings["directory"] + "\\#Manifest.json"):
				with open(Settings["directory"] + "\\#Manifest.json") as FileRead:
					TitlesList = json.load(FileRead)
					#Проверка загрузки манифеста.
					if TitlesList == None:
						# Запись в лог ошибки о невозможности прочитать битый файл.
						logging.error("Failed to read manifest.")
					else:
						# Запись в лог сообщения о количестве тайтлов в манифесте.
						logging.info("Manifest successfully was loaded. Titles: " + str(len(TitlesList)) + ".")

						# Если будет запускаться amend, то сохранить список тайтлов.
						AmendAfterWork_TitleList = TitlesList

						# Парсить каждый тайтл.
						for i in range(0, len(TitlesList)):
							# Алиас манги.
							MangaName = TitlesList[i]
							# Запись в лог сообщения о начале парсинга конкретной манги.
							logging.info("Parcing: \"" + MangaName + "\". Starting...")
							# Сообщение для внутренних функций: прогресс выполнения.
							InFuncMessage_Progress = ""
							# Генерация сообщения для внутренних функций о прогрессе выполнения.
							InFuncMessage_Progress += InFuncMessage_AmendAfterWork + InFuncMessage_Shutdown + InFuncMessage_ForceMode + "Parcing titles from manifest: " + str(i + 1) + " / " + str(len(TitlesList)) + "\n"
							# Парсинг тайтла.
							ParceTitle(Browser, MangaName, Settings, ShowProgress = InFuncMessage_Progress, ForceMode = IsForceModeActivated)

			else:
				# Запись в лог ошибки о невозможности открытия файла настроек.
				logging.error("Failed to find \"" + Settings["directory"] + "\\Manifest.json\". Aborted.")

		else:
			# Установка алиаса тайтла из аргументов команды.
			MangaName = sys.argv[2]
			# Запись в лог сообщения о начале парсинга конкретной манги.
			logging.info("Parcing: \"" + MangaName + "\". Starting...")
			# Парсинг тайтла.
			ParceTitle(Browser, MangaName, Settings, ShowProgress = InFuncMessage_AmendAfterWork + InFuncMessage_Shutdown + InFuncMessage_ForceMode, ForceMode = IsForceModeActivated)

	# Обновление JSON тайтлов.
	if sys.argv[1] == "update":
		# Вывод в лог заголовка: обновление.
		logging.info("====== Updating ======")

		# Если вместо алиаса установлен флаг -all, начать обновление всех тайтлов из директории обработки, иначе провести обновление по переданному алиасу.
		if sys.argv[2] == "-all":
			# Получение списка файлов в директории.
			TitlesList = os.listdir(Settings["directory"])
			# Фильтрация только файлов формата JSON.
			TitlesList = list(filter(lambda x: x.endswith(".json"), TitlesList))
			# Уадление манифеста.
			if "#Manifest.json" in TitlesList:
				TitlesList.remove("#Manifest.json")
			# Удаление файла с определениями слайдов.
			if "#Slides.json" in TitlesList:
				TitlesList.remove("#Slides.json")

			# Если будет запускаться amend, то сохранить список тайтлов.
			AmendAfterWork_TitleList = TitlesList

			# Обновлять каждый тайтл.
			for i in range(0, len(TitlesList)):
				# Алиас манги.
				MangaName = TitlesList[i].replace(".json", "")
				# Сообщение для внутренних функций: прогресс выполнения.
				InFuncMessage_Progress = ""
				# Генерация сообщения для внутренних функций о прогрессе выполнения.
				InFuncMessage_Progress += InFuncMessage_AmendAfterWork + InFuncMessage_Shutdown + "Updating titles: " + str(i + 1) + " / " + str(len(TitlesList))
				# Парсинг тайтла.
				UpdateTitle(Browser, Settings, MangaName, InFuncMessage_Progress)
				# Выдерживание интервала перехода между тайтлами.
				sleep(Settings["delay"])

		else:
			# Установка алиаса тайтла из аргументов команды.
			MangaName = sys.argv[2]
			# Генерация сообщения для внутренних функций о прогрессе выполнения.
			InFuncMessage_Progress = InFuncMessage_AmendAfterWork + InFuncMessage_Shutdown + "Updating title \"" + MangaName + "\"...\n"
			# Обновление тайтла.
			UpdateTitle(Browser, Settings, MangaName, "")

	# Попытка получить размер слайдов для описанных в JSON глав.
	if sys.argv[1] == "amend" or AmendAfterWork == True:
		# Вывод в лог заголовка: другие методы.
		logging.info("====== Amending ======")
		# Список серверов с контентом.
		Servers = GetContentServersList(Browser, Settings)

		# Если вместо алиаса установлен флаг -all, начать дополнение всех слайдов всех глав из директории обработки, иначе провести дополнение по переданному алиасу.
		if sys.argv[2] == "-all":
			# Получение списка файлов в директории.
			FilesList = os.listdir(Settings["directory"])
			# Фильтрация только файлов формата JSON.
			FilesList = list(filter(lambda x: x.endswith(".json"), FilesList))
			# Уадление манифеста.
			if "#Manifest.json" in FilesList:
				FilesList.remove("#Manifest.json")
			# Удаление файла с определениями слайдов.
			if "#Slides.json" in FilesList:
				FilesList.remove("#Slides.json")

			# Если запускается после парсинга или обновления, то получить список тайтлов.
			FilesList = AmendAfterWork_TitleList

			# Дополнять каждый тайтл.
			for i in range(0, len(FilesList)):
				# Алиас манги.
				MangaName = FilesList[i].replace(".json", "")
				# Сообщение для внутренних функций: прогресс выполнения.
				InFuncMessage_Progress = ""
				# Генерация сообщения для внутренних функций о прогрессе выполнения.
				InFuncMessage_Progress += InFuncMessage_Shutdown + "Amending titles: " + str(i + 1) + " / " + str(len(FilesList))
				# Парсинг тайтла.
				Amend(Browser, Settings, Servers, MangaName, InFuncMessage_Progress)
				# Выдерживание интервала перехода между слайдами.
				sleep(Settings["delay"])

		else:
			# Установка алиаса тайтла из аргументов команды.
			MangaName = sys.argv[2]
			# Генерация сообщения для внутренних функций о прогрессе выполнения.
			InFuncMessage_Progress = InFuncMessage_Shutdown + "Amending title \"" + MangaName + "\"..."
			# Исправление тайтла.
			Amend(Browser, Settings, Servers, MangaName, InFuncMessage_Progress)

	# Генерация синтетического BranchID алиаса.
	if sys.argv[1] == "ubid":
		# Вывод в лог заголовка: другие методы.
		logging.info("====== Other ======")
		# Запись в лог сообщения о преобразовании алиаса в синтетический BranchID.
		logging.info("Alias \"" + sys.argv[2] + "\" synthetic branch ID is: " + GetSynt_BranchID(sys.argv[2], ""))
		# Вывод в консоль преобразованного в синтетический BranchID алиаса.
		print("Alias \"" + sys.argv[2] + "\" Synthetic branch ID is: " + GetSynt_BranchID(sys.argv[2], "") + "\nIf title has translation branches, add the \"bid\" from the browser address bar to get the desired value.")

	# Получение данных о слайдах конкретной главы.
	if sys.argv[1] == "getsl":
		# Вывод в лог заголовка: другие методы.
		logging.info("====== Other ======")
		# Сохранение информации о слайдах конкретной главы в Slides.json.
		GetChapterSlidesInJSON(Browser, sys.argv[2], Settings)

	# Запись всех алиасов на странице каталога сайта (поддерживает фильтры).
	if sys.argv[1] == "scan":
		# Вывод в лог заголовка: другие методы.
		logging.info("====== Other ======")
		# Запись в лог сообщения о начале сканирования страницы каталога.
		logging.info("Scanning site on: \"" + Settings["scan-target"] + "\"...")

		# Переключение между режимами передачи аргумента.
		if "-target" in sys.argv:
			ScanTitles(Browser, Settings, None)
		else:
			ScanTitles(Browser, Settings, sys.argv[2])

# Однокомпонентные команды: chtest.
if len(sys.argv) >= 2:

	# Тестирование парсера на скрытность.
	if sys.argv[1] == "chtest":
		# Вывод в лог заголовка: другие методы.
		logging.info("====== Other ======")
		# Запуск теста Chrome Headless Detection.
		ChromeHeadlessTest(Browser)

# Обработка исключения: недостаточно аргументов.
elif len(sys.argv) == 1:
	logging.error("Not enough arguments.")

#==========================================================================================#
# >>>>> ЗАВЕРШЕНИЕ РАБОТЫ СКРИПТА <<<<< #
#==========================================================================================#

# Закрытие браузера, если уже не закрыт.
try:
	Browser.close()
except Exception:
	pass

# Очистка консоли.
Cls()

# Время завершения работы скрипта.
EndTime = time.time()
# Запись времени завершения работы скрипта.
logging.info("Script finished at " + str(datetime.datetime.now())[:-7] + ". Execution time: " + SecondsToTimeString(EndTime - StartTime) + ".")

# Выключение ПК, если установлен соответствующий флаг.
if IsShutdowAfterEnd == True:
	# Запись в лог сообщения о немедленном выключении ПК.
	logging.info("Turning off the computer.")
	# Выключение ПК.
	Shutdown()

# Выключение логгирования.
logging.shutdown()

# Удаление лога, если в процессе работы скрипта не проводился парсинг или обновление, а также указано настройками.
if "parce" not in sys.argv and "update" not in sys.argv and "amend" not in sys.argv and Settings["logs-cleanup"] == True:
	os.remove(LogFilename)