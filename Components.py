from bs4 import BeautifulSoup

import logging
import json
import os

# >>>>> КЛАССЫ <<<<< #
from BaseFunctions import ColoredPrinter

# >>>>> БАЗОВЫЕ ФУНКЦИИ <<<<< #
from BaseFunctions import RemoveArgumentsFromURL
from BaseFunctions import RemoveHTML
from BaseFunctions import Cls

# >>>>> ПАРСИНГ ТАЙТЛА <<<<< #
from BaseFunctions import CheckBranchOnSiteForEmpty
from BaseFunctions import PrepareToParcingChapters
from BaseFunctions import GetMangaSlidesUrlList
from BaseFunctions import GetMangaData_Status
from BaseFunctions import GetMangaData_Series
from BaseFunctions import GetChaptersNames
from BaseFunctions import GetChaptersLinks
from BaseFunctions import GetSynt_BranchID
from BaseFunctions import MakeContentData
from BaseFunctions import GetBranchesID
from BaseFunctions import GetMangaData
from BaseFunctions import IsMangaPaid

# >>>>> ОБНОВЛЕНИЕ ТАЙТЛА <<<<< #
from BaseFunctions import GetBranchesDescriptionStruct
from BaseFunctions import GetBranchesIdFromJSON
from BaseFunctions import TrueToSyntBranchID
from BaseFunctions import BuildLinksFromJSON
from BaseFunctions import ParceChapter

# >>>>> ИСПРАВЛЕНИЕ ТАЙТЛА <<<<< #
from BaseFunctions import CheckChapterForNoneSlideSizes
from BaseFunctions import AmendChapterSlides

#Парсинг тайтла.
def ParceTitle(Browser, MangaName, Settings, ShowProgress, ForceMode):

	#Проверка существования файла.
	IsFileAlredyExist = os.path.exists(Settings["directory"] + "\\" + MangaName + ".json")
	if IsFileAlredyExist == True and ForceMode == False:
		logging.info("Parcing: \"" + MangaName + "\". Already exists. Skipped.")
	else:

		#Сообщение в лог о перезаписи файла.
		if IsFileAlredyExist == True:
			logging.info("Parcing: \"" + MangaName + "\". Already exists. Will be overwritten...")

		#Получение данных о манге.
		JSON = GetMangaData(Browser, Settings, MangaName)
		IsPaid = IsMangaPaid(Browser, MangaName, Settings)
		BranchesCount = len(JSON["branches"])

		#Проверка лицензии.
		if JSON['is_licensed'] == False and IsPaid == False:
			#Получение BID веток.
			BIDs = None
			if BranchesCount > 1:
				BIDs = GetBranchesID(Browser, MangaName, Settings)
			logging.info("Parcing: \"" + MangaName + "\". Branches count: " + str(BranchesCount) + ".")
			#Если не лицензировано, парсить каждую ветку.
			for i in range(0, len(JSON["branches"])):
				BID = None
				if BIDs == None:
					BID = ""
				else:
					BID = BIDs[i]
				BIDlog = "none"
				#Проверка ветви на пустоту.
				if CheckBranchOnSiteForEmpty(Browser, Settings, MangaName, BID) == False:
					#Если существует только одна ветвь перевода.
					if BIDs is None:
						PrepareToParcingChapters(Browser, Settings, MangaName, BIDs)
					else:
						#Перезапись ID ветви с использованием BID, если ветвей много.
						JSON["branches"][i]["id"] = GetSynt_BranchID(MangaName, str(BIDs[i]))

						PrepareToParcingChapters(Browser, Settings, MangaName, BIDs[i])
						BIDlog = str(BIDs[i])

					ChaptersNames = GetChaptersNames(Browser)
					ChaptersLinks = GetChaptersLinks(Browser)
					logging.info("Parcing: \"" + MangaName + "\". Branch ID: " + BIDlog + ". Chapters in branch: " + str(len(ChaptersLinks)) + ".")
					if BIDs is None:
						JSON["content"][GetSynt_BranchID(MangaName, "")] = MakeContentData(Browser, Settings, ShowProgress, ChaptersNames, ChaptersLinks, "")
					else:
						BIDlog = str(BIDs[i])
						JSON["content"][GetSynt_BranchID(MangaName, str(BIDs[i]))] = MakeContentData(Browser, Settings, ShowProgress, ChaptersNames, ChaptersLinks, str(BIDs[i]))

				else:
					if BIDs != None:
						BIDlog = str(BIDs[i])

						#Перезапись ID ветви с использованием BID, если ветвей много.
						JSON["branches"][i]["id"] = GetSynt_BranchID(MangaName, str(BIDs[i]))
						JSON["content"][GetSynt_BranchID(MangaName, BIDs[i])] = []
					else:
						#Перезапись ID ветви с использованием BID, если ветвь одна и она пустая.
						JSON["branches"][i]["id"] = GetSynt_BranchID(MangaName, "")
						JSON["content"][GetSynt_BranchID(MangaName, "")] = []
					

					logging.info("Parcing: \"" + MangaName + "\". Branch ID: " + BIDlog + ". Chapters in branch: 0.")

		#Если лицензировано, ничего больше не парсить и вывести уведомление.
		elif JSON['is_licensed'] == True:
			logging.info("Parcing: \"" + MangaName + "\". Licensed. Skipped.")
		elif IsPaid == True:
			logging.info("Parcing: \"" + MangaName + "\". Is paid. Skipped.")
	
		with open(Settings["directory"] + "\\" + MangaName + ".json", "w", encoding = "utf-8") as FileWrite:
			json.dump(JSON, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))
			logging.info("Parcing: \"" + MangaName + "\". JSON file was created.")
		logging.info("Parcing: \"" + MangaName + "\". Completed.")

# Обновление тайтла.
def UpdateTitle(Browser, Settings, MangaName, InFuncMessage_Progress):
	# Очистка содержимого консоли.
	Cls()
	# Вывод прогресса обновления.
	print(InFuncMessage_Progress)

	# Проверка доступности файла.
	if os.path.exists(Settings["directory"] + "\\" + MangaName + ".json"):
		# Открытие JSON тайтла.
		with open(Settings["directory"] + "\\" + MangaName + ".json", encoding = "utf-8") as FileRead:
			# JSON файл тайтла.
			TitleJSON = json.load(FileRead)
			# Проверка файла на пустоту.
			if TitleJSON == None:
				logging.error("Failed to read \"" + MangaName + ".json\".")
			else:
				# Запись в лог сообщения о начале обновления тайтла.
				logging.info("Updating: \"" + MangaName + "\". Starting...")
				# Получение списка синтетических ID ветвей из JSON.
				Synt_BranchesID = GetBranchesIdFromJSON(TitleJSON)
				# Получение списка истинных ID ветвей из JSON.
				True_BranchesID = GetBranchesID(Browser, MangaName, Settings)
				# Пусты ли ветви.
				True_BranchesEmptiness = []
				# Структура контента для записи в JSON.
				ContentData = {}
				# Количество новых глав.
				NewChaptersCount = 0
				# Количество новых глав в последней обработанной ветви.
				NewChaptersInBranchCount = 0
				# Количество изменённых ветей.
				UpdatedBranchesCount = 0
				# Количество обновлений описания тайтла.
				DescriptionUpdatesCount = 0

				# Проверка пустоты всех ветвей.
				if len(True_BranchesID) == 0:
					True_BranchesEmptiness.append(CheckBranchOnSiteForEmpty(Browser, Settings, MangaName, ""))
				else:
					for i in range(0, len(True_BranchesID)):
						True_BranchesEmptiness.append(CheckBranchOnSiteForEmpty(Browser, Settings, MangaName, True_BranchesID[i]))

				# Получение статуса тайтла с сайта.
				StatusFromSite = GetMangaData_Status(Browser, Settings, MangaName)
				# Если статус изменился, записать его в лог и в JSON.
				if StatusFromSite != TitleJSON["status"]:
					# Изменить статус в JSON.
					TitleJSON["status"] = StatusFromSite
					# Запись в лог сообщения о новом статусе тайтла.
					logging.info("Updating: \"" + MangaName + "\". Detected new status of title: \"" + StatusFromSite["name"] + "\".")
					# Инкремент количества обновлений описания тайтла.
					DescriptionUpdatesCount += 1
				# Обновление серий тайтла.
				TitleJSON["series"] = GetMangaData_Series(Browser, Settings, MangaName)

				# Проверка на соответствие количества ветвей переводов: в JSON и на сайте одна ветвь.
				if len(True_BranchesID) == 0 and len(Synt_BranchesID) == 1:
					# Запись в лог сообщения о количестве новых ветвей переводов.
					logging.info("Updating: \"" + MangaName + "\". Branches in JSON: 1 / 1.")
					
					# Проверка пустоты ветви.
					if True_BranchesEmptiness[0] == False:
						# Список ссылок на главы, сформированных на основе JSON.
						ChaptersLinksFromJSON = BuildLinksFromJSON(TitleJSON, Synt_BranchesID[0], MangaName, Settings)
						# Подготовка к получению списка ссылок на главы с сайта.
						PrepareToParcingChapters(Browser, Settings, MangaName, None)
						# Список ссылок на главы, взятый с сайта.
						ChaptersLinksFromSite = GetChaptersLinks(Browser)
						# Обращение последовательности для верного порядка записи в JSON.
						ChaptersLinksFromSite.reverse()
						# Формирование контейнера для новой структуры.
						ContentData[Synt_BranchesID[0]] = []
						# Установка количества обновлённых ветвей.
						UpdatedBranchesCount = 1

						# Преобразование списка ссылок на главы, полученного с сайта, к полному типу.
						for i in range(0, len(ChaptersLinksFromSite)):
							ChaptersLinksFromSite[i] = Settings["domain"][:-1] + ChaptersLinksFromSite[i]

						# Для всех ссылок с сайта проверить присутствие в JSON.
						for i in range(0, len(ChaptersLinksFromSite)):
							# Если ссылки нет, то спарсить главу, иначе сохранить текущий узел с перезаписью индекса.
							if ChaptersLinksFromSite[i] not in ChaptersLinksFromJSON:
								# Запись в лог сообщения о нахождении новой главы.
								logging.info("Updating: \"" + MangaName + "\". Branch ID: none. New chapter has been found: \"" + ChaptersLinksFromSite[i].replace(Settings["domain"][:-1], "") + "\".")
								# Парсинг одной главы и помещение её в контейнер.
								ContentData[Synt_BranchesID[0]].append(ParceChapter(Browser, Settings, ChaptersLinksFromSite[i], ""))
								# Инкремент количества новых глав.
								NewChaptersCount += 1
							else:
								ContentData[Synt_BranchesID[0]].append(TitleJSON["content"][Synt_BranchesID[0]][ChaptersLinksFromJSON.index(ChaptersLinksFromSite[i])])
						
							# Перезапись индекса.
							ContentData[Synt_BranchesID[0]][-1]["index"] = i + 1

				# Проверка на соответствие количества ветвей переводов: в JSON и на сайте несколько ветвей.
				elif len(True_BranchesID) == len(Synt_BranchesID) and len(True_BranchesID) > 1:
					# Запись в лог сообщения о количестве новых ветвей переводов.
					logging.info("Updating: \"" + MangaName + "\". Branches in JSON: " + str(len(Synt_BranchesID)) + " / " + str(len(True_BranchesID)) + ".")
					# Словарь ссылок на главы, сформированных на основе всех ветвей JSON.
					ChaptersLinksFromJSON = {}
					# Словарь ссылок на главы во всех ветвях переводов, взятый с сайта.
					ChaptersLinksFromSite = {}
					# Структура контента для помещения в JSON.
					ContentData = {}

					# Для каждой ветви из JSON сформировать список ссылок на главы.
					for i in range(0, len(Synt_BranchesID)):
						ChaptersLinksFromJSON[Synt_BranchesID[i]] = BuildLinksFromJSON(TitleJSON, Synt_BranchesID[i], MangaName, Settings)

					# Для каждой ветви перевода на сайте сформировать список ссылок на главы, преобразовать к его полному типу и инвертировать (если ветвь не пуста).
					for i in range(0, len(True_BranchesID)):
						if True_BranchesEmptiness[i] == False:
							PrepareToParcingChapters(Browser, Settings, MangaName, True_BranchesID[i])
							ChaptersLinksFromSite[True_BranchesID[i]] = GetChaptersLinks(Browser)
							ChaptersLinksFromSite[True_BranchesID[i]].reverse()

							# Преобразование списка ссылок на главы, полученного с сайта, к полному типу.
							for k in range(0, len(ChaptersLinksFromSite[True_BranchesID[i]])):
								ChaptersLinksFromSite[True_BranchesID[i]][k] = Settings["domain"][:-1] + ChaptersLinksFromSite[True_BranchesID[i]][k]

					# Для каждой синтетической ветви подготовить контейнер.
					for i in range(0, len(Synt_BranchesID)):
						ContentData[Synt_BranchesID[i]] = []

					# Для каждой ветви перевода с сайта.
					for BranchIndex in range(0, len(True_BranchesID)):
						# Проверка пустоты ветви.
						if True_BranchesEmptiness[BranchIndex] == False:
							# Генерация синтетического BranchID для записи.
							KeySynt_BranchID = TrueToSyntBranchID(True_BranchesID[BranchIndex], MangaName)

							# Для всех ссылок с сайта проверить присутствие в JSON.
							for ChapterLinkIndex in range(0, len(ChaptersLinksFromSite[True_BranchesID[BranchIndex]])):
								# Если ссылки нет, то спарсить главу, иначе сохранить текущий узел с перезаписью индекса.
								if ChaptersLinksFromSite[True_BranchesID[BranchIndex]][ChapterLinkIndex] not in ChaptersLinksFromJSON[KeySynt_BranchID]:
									# Запись в лог сообщения о нахождении новой главы.
									logging.info("Updating: \"" + MangaName + "\". Branch ID: " + True_BranchesID[BranchIndex] + ". New chapter has been found: \"" + ChaptersLinksFromSite[True_BranchesID[BranchIndex]][ChapterLinkIndex].replace(Settings["domain"][:-1], "") + "\".")
									# Парсинг одной главы и помещение её в контейнер.
									ContentData[KeySynt_BranchID].append(ParceChapter(Browser, Settings, ChaptersLinksFromSite[True_BranchesID[BranchIndex]][ChapterLinkIndex], True_BranchesID[BranchIndex]))
									# Инкремент количества новых глав.
									NewChaptersCount += 1
								else:
									ContentData[KeySynt_BranchID].append(TitleJSON["content"][KeySynt_BranchID][ChaptersLinksFromJSON[KeySynt_BranchID].index(ChaptersLinksFromSite[True_BranchesID[BranchIndex]][ChapterLinkIndex])])
						
								# Перезапись индекса.
								ContentData[KeySynt_BranchID][-1]["index"] = ChapterLinkIndex

							# Подсчёт изменённых ветвей.
							if NewChaptersInBranchCount != NewChaptersCount:
								# Инкремент обновлённых ветвей переводов.
								UpdatedBranchesCount += 1
								# Обновление количества новых глав в последней спаршенной ветви перевода.
								NewChaptersInBranchCount = NewChaptersCount

				# Проверка на соответствие количества ветвей переводов: в JSON меньше ветвей, чем на сайте.
				elif len(True_BranchesID) > len(Synt_BranchesID):
					# Запись в лог сообщения о количестве новых ветвей переводов.
					logging.info("Updating: \"" + MangaName + "\". Branches in JSON: " + str(len(Synt_BranchesID)) + " / " + str(len(True_BranchesID)) + ".")
					# Генерация новой структуры ветвей и её запись.
					TitleJSON["branches"] = GetBranchesDescriptionStruct(Browser, Settings, MangaName, True_BranchesID)
					# Словарь ссылок на главы, сформированных на основе всех ветвей JSON.
					ChaptersLinksFromJSON = {}
					# Словарь ссылок на главы во всех ветвях переводов, взятый с сайта.
					ChaptersLinksFromSite = {}
					# Структура контента для помещения в JSON.
					ContentData = {}

					# Для каждой ветви из JSON сформировать список ссылок на главы.
					for i in range(0, len(Synt_BranchesID)):
						ChaptersLinksFromJSON[Synt_BranchesID[i]] = BuildLinksFromJSON(TitleJSON, Synt_BranchesID[i], MangaName, Settings)

					# Для каждой ветви перевода на сайте сформировать список ссылок на главы, преобразовать к его полному типу и инвертировать.
					for i in range(0, len(True_BranchesID)):
						if True_BranchesEmptiness[i] == False:
							PrepareToParcingChapters(Browser, Settings, MangaName, True_BranchesID[i])
							ChaptersLinksFromSite[True_BranchesID[i]] = GetChaptersLinks(Browser)
							ChaptersLinksFromSite[True_BranchesID[i]].reverse()

							# Преобразование списка ссылок на главы, полученного с сайта, к полному типу.
							for k in range(0, len(ChaptersLinksFromSite[True_BranchesID[i]])):
								ChaptersLinksFromSite[True_BranchesID[i]][k] = Settings["domain"][:-1] + ChaptersLinksFromSite[True_BranchesID[i]][k]

					# Для каждой синтетической ветви подготовить контейнер.
					for i in range(0, len(Synt_BranchesID)):
						ContentData[Synt_BranchesID[i]] = []

					# Создание пустых узлов для новых ветвей переводов, если требуется.
					for i in range(0, len(True_BranchesID)):
						# Проверка пустоты ветви.
						if True_BranchesEmptiness[i] == False:
							# Генерация синтетического BranchID для записи.
							KeySynt_BranchID = TrueToSyntBranchID(True_BranchesID[i], MangaName)

							# Если ключ отсутствует, то создать такой.
							if KeySynt_BranchID not in ChaptersLinksFromJSON.keys():
								ChaptersLinksFromJSON[KeySynt_BranchID] = []
								ContentData[KeySynt_BranchID] = []

								# Запись в лог сообщения о нахождении новой ветви перевода.
								logging.info("Updating: \"" + MangaName + "\". Located new translation branch with ID: " + True_BranchesID[i] + ".")

					# Для каждой ветви перевода с сайта.
					for BranchIndex in range(0, len(True_BranchesID)):
						# Проверка пустоты ветви.
						if True_BranchesEmptiness[BranchIndex] == False:
							# Генерация синтетического BranchID для записи.
							KeySynt_BranchID = TrueToSyntBranchID(True_BranchesID[BranchIndex], MangaName)

							# Для всех ссылок с сайта проверить присутствие в JSON.
							for ChapterLinkIndex in range(0, len(ChaptersLinksFromSite[True_BranchesID[BranchIndex]])):
								# Если ссылки нет, то спарсить главу, иначе сохранить текущий узел с перезаписью индекса.
								if ChaptersLinksFromSite[True_BranchesID[BranchIndex]][ChapterLinkIndex] not in ChaptersLinksFromJSON[KeySynt_BranchID]:
									# Запись в лог сообщения о нахождении новой главы.
									logging.info("Updating: \"" + MangaName + "\". Branch ID: " + True_BranchesID[BranchIndex] + ". New chapter has been found: \"" + ChaptersLinksFromSite[True_BranchesID[BranchIndex]][ChapterLinkIndex].replace(Settings["domain"][:-1], "") + "\".")
									# Парсинг одной главы и помещение её в контейнер.
									ContentData[KeySynt_BranchID].append(ParceChapter(Browser, Settings, ChaptersLinksFromSite[True_BranchesID[BranchIndex]][ChapterLinkIndex], True_BranchesID[BranchIndex]))
									# Инкремент количества новых глав.
									NewChaptersCount += 1
								else:
									ContentData[KeySynt_BranchID].append(TitleJSON["content"][KeySynt_BranchID][ChaptersLinksFromJSON[KeySynt_BranchID].index(ChaptersLinksFromSite[True_BranchesID[BranchIndex]][ChapterLinkIndex])])
						
								# Перезапись индекса.
								ContentData[KeySynt_BranchID][-1]["index"] = ChapterLinkIndex

							# Подсчёт изменённых ветвей.
							if NewChaptersInBranchCount != NewChaptersCount:
								# Инкремент обновлённых ветвей переводов.
								UpdatedBranchesCount += 1
								# Обновление количества новых глав в последней спаршенной ветви перевода.
								NewChaptersInBranchCount = NewChaptersCount

			# Перезапись контента.
			TitleJSON["content"] = ContentData

			# Если есть новые главы или описание тайтла изменилось, то перезаписать файл.
			if NewChaptersCount > 0 or DescriptionUpdatesCount > 0:
				# Сохранение файла JSON.
				with open(Settings["directory"] + "\\" + MangaName + ".json", "w", encoding = "utf-8") as FileWrite:
					json.dump(TitleJSON, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))

					# Запись в лог сообщения об успешном обновлении файла JSON, если получены новые главы.
					if NewChaptersCount > 0:
						logging.info("Updating: \"" + MangaName + "\". Completed. Added " + str(NewChaptersCount) + " chapters in " + str(UpdatedBranchesCount) + " branches.")

			# Запись в лог сообщения об отсутствующих новых главах.
			if NewChaptersCount == 0:
				logging.info("Updating: \"" + MangaName + "\". Completed. New chapters not found.")

	else:
		# Запись в лог сообщения об ошибке доступа к файлу.
		logging.error("Failed to find \"" + Settings["directory"] + "\\" + MangaName + ".json" + "\".")

# Сканирование страницы каталога и сохранение списка тайтлов в манифест.
def ScanTitles(Browser, Settings, ScanTarget):
	# Переход на страницу каталога.
	if ScanTarget == None:
		Browser.get(Settings["scan-target"])
	else:
		Browser.get(ScanTarget)
	# HTML-код страницы после полной загрузки.
	BodyHTML = Browser.execute_script("return document.body.innerHTML;")
	# Парсинг HTML-кода страницы.
	Soup = BeautifulSoup(BodyHTML, "lxml")
	# Плашки тайтлов.
	MediaCards = Soup.find_all("a", {"class": "media-card"})
	# Список алиасов тайтлов на странице каталога.
	TitlesSlugs = []

	# Получение списка алиасов.
	for i in range(0, len(MediaCards)):
		TitlesSlugs.append(str(MediaCards[i]["href"]).split('/')[3])

	# Сохранение манифеста.
	with open(Settings["directory"] + "\\#Manifest.json", "w", encoding = "utf-8") as FileWrite:
		json.dump(TitlesSlugs, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))
		# Запись в лог сообщения о завершении сканирования.
		logging.info("Manifest file was created. Completed.")

# Получение данных о слайдах одной главы и запись их в JSON. Помогает исправлять записи с отсутствующими слайдами.
def GetChapterSlidesInJSON(Browser, ChapterURL, Settings):
	# Удаление домена из полного URL главы.
	ChapterURL = ChapterURL.replace(Settings["domain"][:-1], "")
	# Удаление запросов из URL.
	ChapterURL = RemoveArgumentsFromURL(ChapterURL)

	# Получение информации о слайдах.
	SlidesInfo = GetMangaSlidesUrlList(Browser, Settings, ChapterURL)

	# Сохранение информации о слайдах.
	with open(Settings["directory"] + "\\#Slides.json", "w", encoding = "utf-8") as FileWrite:
		json.dump(SlidesInfo, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))
		# Запись в лог сообщения об успешном создании файла.
		logging.info("Chapter slides info file was created. Completed.")

# Дополнение глав тайтла размерами слайдов.
def Amend(Browser, Settings, Servers, MangaName, InFuncMessage_Progress):
	# Очистка содержимого консоли.
	Cls()
	# Вывод прогресса исправления.
	print(InFuncMessage_Progress)

	# Проверка доступности файла.
	if os.path.exists(Settings["directory"] + "\\" + MangaName + ".json"):
		# Открытие JSON тайтла.
		with open(Settings["directory"] + "\\" + MangaName + ".json", encoding = "utf-8") as FileRead:
			# JSON файл тайтла.
			TitleJSON = json.load(FileRead)
			# Провка ошибки парсинга JSON-формата.
			if TitleJSON == None:
				logging.error("Failed to read \"" + MangaName + ".json\".")
			else:
				# Получение списка синтетических ID ветвей из JSON.
				Synt_BranchesID = GetBranchesIdFromJSON(TitleJSON)
				# Количество неполных описаний слайдов.
				ChaptersBadDescriptionsCount = 0
				# Статус: запускалось ли исправление.
				AmendingWasStarted = False
				# Запись в лог сообщения о начале исправления.
				logging.info("Amending: \"" + MangaName + "\". Starting...")

				# В каждой ветви искать главу с неполным описанием.
				for BranchIndex in range(0, len(Synt_BranchesID)):
					# Проверить каждую главу.
					for ChapterIndex in range(0, len(TitleJSON["content"][Synt_BranchesID[BranchIndex]])):
						# Если глава не полностью описана, попытаться исправить её.
						if CheckChapterForNoneSlideSizes(TitleJSON["content"][Synt_BranchesID[BranchIndex]][ChapterIndex]) > 0:
							# Переключение статуса исправления.
							AmendingWasStarted = True
							# Сохранение структуры главы после попытки исправления.
							TitleJSON["content"][Synt_BranchesID[BranchIndex]][ChapterIndex] = AmendChapterSlides(Browser, Settings, Servers, TitleJSON, TitleJSON["content"][Synt_BranchesID[BranchIndex]][ChapterIndex])
							# Инкремент количества плохих описаний глав, если не исправлено.
							if CheckChapterForNoneSlideSizes(TitleJSON["content"][Synt_BranchesID[BranchIndex]][ChapterIndex]) > 0:
								ChaptersBadDescriptionsCount += 1

				# Если исправление запускалось.
				if AmendingWasStarted == True:
					# Сохранение файла JSON.
					with open(Settings["directory"] + "\\" + MangaName + ".json", "w", encoding = "utf-8") as FileWrite:
						json.dump(TitleJSON, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))

					# Запись в лог сообщения о завершении исправлении файла JSON.
					logging.info("Amending: \"" + MangaName + "\". Completed. Bad chapters: " + str(ChaptersBadDescriptionsCount) + ".")

				# Если исправление не запускалось.
				elif AmendingWasStarted == False:
					# Запись в лог сообщения об отсутствии надобности в исправлении файла JSON.
					logging.info("Amending: \"" + MangaName + "\". No slides without sizes. Completed.")

	else:
		# Запись в лог сообщения об ошибке доступа к файлу.
		logging.error("Failed to find \"" + Settings["directory"] + "\\" + MangaName + ".json" + "\".")

# Запуск теста Chrome Headless Detection.
def ChromeHeadlessTest(Browser):
	# Переход на стрицу теста.
	Browser.get("https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html")
	# Цветной вывод.
	ColoredPrinterObj = ColoredPrinter()
	# HTML-код страницы после полной загрузки.
	BodyHTML = Browser.execute_script("return document.body.innerHTML;")
	# Парсинг HTML-кода страницы.
	Soup = BeautifulSoup(BodyHTML, "lxml")
	# Получение значения WebDriver.
	UserAgent = RemoveHTML(Soup.find("td", {"id": "user-agent-result"}))
	# Получение значения WebDriver.
	WebDriver = RemoveHTML(Soup.find("td", {"id": "webdriver-result"}))
	# Получение значения Chrome.
	Chrome = RemoveHTML(Soup.find("td", {"id": "chrome-result"}))
	# Получение значения Chrome.
	Permissions = RemoveHTML(Soup.find("td", {"id": "permissions-result"}))
	# Получение значения Chrome.
	PluginsLength = RemoveHTML(Soup.find("td", {"id": "plugins-length-result"}))
	# Получение значения Chrome.
	Languages = RemoveHTML(Soup.find("td", {"id": "languages-result"}))

	# Очистка консоли.
	Cls()
	# Вывод результатов теста.
	print(f"UserAgent: {UserAgent}")
	print("WebDriver: ", end = "")
	if WebDriver == "missing (passed)":
		ColoredPrinterObj.Print(f"{WebDriver}", ColoredPrinterObj.GREEN)
	else:
		ColoredPrinterObj.Print(f"{WebDriver}", ColoredPrinterObj.RED)
	print(f"Chrome: {Chrome}")
	print(f"Permissions: {Permissions}")
	print(f"PluginsLength: {PluginsLength}")
	print(f"Languages: {Languages}\n")
	# Закрытие браузера.
	Browser.close()

	# Пауза.
	input("Press ENTER to exit...")







