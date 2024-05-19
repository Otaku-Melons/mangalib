from dublib.Methods import Cls, ReadJSON, RemoveFolderContent, RemoveRecurringSubstrings, WriteJSON, Zerotify
from dublib.WebRequestor import WebRequestor
from Source.Functions import ToInt
from bs4 import BeautifulSoup
from time import sleep

import urllib.parse
import logging
import json
import os

class Parser:
	"""Парсер тайтла."""

	def __Amend(self):
		# Запись в лог сообщения: дополнение глав.
		logging.info("Title: \"" + self.__Slug + "\". Amending...")
		# Количество глав во всех ветвях.
		TotalChaptersCount = 0
		# Глобальный индекс текущей главы.
		CurrentChapterIndex = 0
		# Количество дополненных глав.
		AmendedChaptersCount = 0
		
		# Для каждой ветви.
		for Branch in self.__Title["branches"]:
			# Подсчёт количества глав.
			TotalChaptersCount += Branch["chapters-count"]
		
		# Для каждой ветви.
		for BranchID in self.__Title["chapters"].keys():
			
			# Для каждый главы.
			for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
				# Инкремент глобального индекса текущей главы.
				CurrentChapterIndex += 1
				# Очистка консоли.
				Cls()
				# Вывод в консоль: сообщение из внешнего обработчика и прогресс.
				print(self.__Message + "\n" + f"Amending: {CurrentChapterIndex} / {TotalChaptersCount}")
				
				# Если слайды не описаны или включён режим перезаписи.
				if self.__Title["chapters"][BranchID][ChapterIndex]["slides"] == [] or self.__ForceMode == True:
					
					# Получение списка слайдов главы.
					Slides = self.__GetChapterSlides(
						self.__Title["chapters"][BranchID][ChapterIndex]["number"],
						self.__Title["chapters"][BranchID][ChapterIndex]["volume"],
						BranchID
					)
					# Инкремент количества обновлённых глав.
					AmendedChaptersCount += 1
					# Запись в лог сообщения: глава дополнена.
					if Slides != []: logging.info("Title: \"" + self.__Slug + "\". Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " amended.")
					# Запись информации о слайде.
					self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = Slides
					# Выжидание интервала.
					sleep(self.__Settings["delay"])

		# Запись в лог сообщения: завершение дополнения.
		logging.info("Title: \"" + self.__Slug + f"\". Amended {AmendedChaptersCount} chapters.")

	def __BuildBranches(self):
		"""Строит структуру ветвей и глав."""

		# Структуры ветвей и глав.
		Branches = list()
		Chapters = dict()
		# Запрос: главы.
		Response = self.__Requestor.get(f"https://api.lib.social/api/manga/{self.__Slug}/chapters")
		
		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг данных в JSON.
			Data = Response.json["data"]

			# Для каждой главы.
			for Chapter in Data:

				# Для каждой ветви.
				for BranchData in Chapter["branches"]:
					# ID ветви.
					BranchID = str(BranchData["branch_id"])
					if BranchID == "None": BranchID = str(self.__Title["id"]) + "0"
					# Если ветвь не существует, создать её.
					if BranchID not in Chapters.keys(): Chapters[BranchID] = list()
					# Буфер главы.
					Buffer = {
						"id": BranchData["id"],
						"volume": float(Chapter["volume"]) if "." in Chapter["volume"] else int(Chapter["volume"]),
						"number": float(Chapter["number"]) if "." in Chapter["number"] else int(Chapter["number"]),
						"name": Zerotify(Chapter["name"]),
						"is-paid": False,
						"translator": BranchData["teams"][0]["name"] if BranchData["teams"] else None,
						"slides": []	
					}
					# Запись главы.
					Chapters[BranchID].append(Buffer)

			# Для каждой ветви.
			for BranchID in Chapters.keys():
				# Буфер ветви.
				Buffer = {
					"id": int(BranchID),
					"chapters-count": len(Chapters[BranchID])
				}
				# Запись ветви.
				Branches.append(Buffer)

			# Сохранение данных.
			self.__Title["branches"] = Branches
			self.__Title["chapters"] = Chapters

		else:
			# Запись в лог ошибки: не удалось получить доступ к главам.
			logging.error("Title: \"" + self.__Slug + "\". Unable to get chapters data.")
			# Переключение статуса тайтла.
			self.__IsActive = False

	def __GetAgeRating(self, data: dict) -> int:
		"""
		Получает возрастной рейтинг.
			data – словарь данных тайтла.
		"""

		# Возрастной рейтинг.
		Rating = int(data["ageRestriction"]["label"].split(" ")[0].replace("+", ""))

		return Rating 

	def __GetAuthor(self, data: dict) -> str | None:
		"""
		Получает имя автора.
			data – словарь данных тайтла.
		"""

		# Имя автора.
		Author = None
		# Если определён автор, записать его имя.
		if len(data["authors"]): Author = data["authors"][0]["name"]

		return Author

	def __GetCovers(self, data: dict) -> list[dict]:
		"""
		Получает имя автора.
			data – словарь данных тайтла.
		"""

		# Список обложек.
		Covers = list()

		# Если обложка присутствует.
		if data["cover"]:
			# Буфер обложки.
			Buffer = {
				"link": None,
				"filename": None,
				"width": None,
				"height": None
			}
			# Заполнение данных.
			Buffer["link"] =data["cover"]["default"]
			Buffer["filename"] = data["cover"]["default"].split("/")[-1]
			# Запись буфера.
			Covers.append(Buffer)

		return Covers

	def __GetChapterSlides(self, number: str, volume: str, branch_id: str) -> list[dict]:
		"""
		Получает данные о слайдах главы.
			number – номер главы;
			volume – номер тома;
			branch_id – ID ветви.
		"""

		# Список слайдов.
		Slides = list()
		# Модификатор запроса ветви.
		Branch = "" if branch_id == str(self.__Title["id"]) + "0" else f"&branch_id={branch_id}"
		# Запрос: слайды главы.
		Response = self.__Requestor.get(f"https://api.lib.social/api/manga/{self.__Slug}/chapter?number={number}&volume={volume}{Branch}", headers = {"Authorization": self.__Settings["token"]})

		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг данных в JSON.
			Data = Response.json["data"]["pages"]

			# Для каждого слайда.
			for SlideIndex in range(len(Data)):
				# Буфер слайда.
				Buffer = {
					"index": SlideIndex + 1,
					"link": urllib.parse.quote_plus(self.__Server + Data[SlideIndex]["url"]),
					"width": Data[SlideIndex]["width"],
					"height": Data[SlideIndex]["height"]
				}
				# Запись слайда. 
				Slides.append(Buffer)

		else:
			# Запись в лог ошибки: не удалось получить слайды.
			logging.error(f"Title: \"{self.__Slug}\". Unable to load chapter slides. Response code: {Response.status_code}.")

		return Slides

	def __GetDescription(self, data: dict) -> str | None:
		"""
		Получает описание.
			data – словарь данных тайтла.
		"""

		# Описание.
		Description = None
		# Если присутствует описание, записать его и отформатировать.
		if "summary" in data.keys(): Description = RemoveRecurringSubstrings(data["summary"], "\n").strip().replace(" \n", "\n")

		return Description

	def __GetGenres(self, data: dict) -> list[str]:
		"""
		Получает список жанров.
			data – словарь данных тайтла.
		"""

		# Описание.
		Genres = list()
		# Для каждого жанра записать имя.
		for Genre in data["genres"]: Genres.append(Genre["name"].lower())

		return Genres

	def __GetTags(self, data: dict) -> list[str]:
		"""
		Получает список тегов.
			data – словарь данных тайтла.
		"""

		# Описание.
		Tags = list()
		# Для каждого тега записать имя.
		for Tag in data["tags"]: Tags.append(Tag["name"].lower())

		return Tags

	def __GetTitle(self):
		"""Получает описательные данные тайтла."""
		
		# Запрос: описание тайтла.
		Response = self.__Requestor.get(f"https://api.lib.social/api/manga/{self.__Slug}?fields[]=eng_name&fields[]=otherNames&fields[]=summary&fields[]=releaseDate&fields[]=type_id&fields[]=caution&fields[]=genres&fields[]=tags&fields[]=franchise&fields[]=authors&fields[]=manga_status_id&fields[]=status_id", headers = {"Authorization": self.__Settings["token"]})
		
		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг данных в JSON.
			Data = Response.json["data"]
			# Заполнение описания тайтла.
			self.__Title["site"] = self.__Domain
			self.__Title["id"] = Data["id"]
			self.__Title["slug"] = Data["slug"]
			self.__Title["covers"] = list()
			self.__Title["ru-name"] = Data["rus_name"]
			self.__Title["en-name"] = Data["eng_name"]
			self.__Title["another-names"] = Data["otherNames"]
			self.__Title["author"] = self.__GetAuthor(Data)
			self.__Title["publication-year"] = int(Data["releaseDate"])
			self.__Title["age-rating"] = self.__GetAgeRating(Data)
			self.__Title["description"] = self.__GetDescription(Data)
			self.__Title["type"] = self.__GetType(Data)
			self.__Title["status"] = self.__GetStatus(Data)
			self.__Title["is-licensed"] = Data["is_licensed"]
			self.__Title["series"] = self.__GetSeries(Data)
			self.__Title["genres"] = self.__GetGenres(Data)
			self.__Title["tags"] = self.__GetTags(Data)
			self.__Title["branches"] = list()
			self.__Title["chapters"] = dict()
			
			# Получение обложек и структуры контента.
			self.__Title["covers"] = self.__GetCovers(Data)
			self.__BuildBranches()
			# Запись в лог сообщения: получено описание тайтла.
			logging.info("Title: \"" + self.__Title["slug"] + "\". Request title data... Done.")
			
		elif "Данный тайтл недоступно на территории РФ." in Response.text:
			# Запись в лог ошибки: тайтл недоступен на территории РФ.
			logging.error(f"Title: \"{self.__Slug}\". Not available on the territory of the Russian Federation.")
			# Переключение статуса тайтла.
			self.__IsActive = False
			
		else:
			
			# Если тайтл не найден.
			if Response.status_code == 404 or "Обновления популярной манги" in Response.text :
				# Запись в лог ошибки: тайтл не найден.
				logging.error("Title: \"" + self.__Title["slug"] + "\". Not found. Skipped.")
				
			else:
				# Запись в лог ошибки: нет доступа к тайтлу.
				logging.error("Title: \"" + self.__Slug + "\". Not accessed. Skipped.")
				
			# Переключение статуса тайтла.
			self.__IsActive = False
	
	def __GetSeries(self, data: dict) -> list[str]:
		"""
		Получает список серий.
			data – словарь данных тайтла.
		"""

		# Серии.
		Series = list()
		# Для каждой серии записать название.
		for Franchise in data["franchise"]: Series.append(Franchise["name"])
		# Удаление серии оригинальных работ.
		if "Оригинальные работы" in Series: Series.remove("Оригинальные работы")

		return Series

	def __GetServer(self) -> str:
		"""Возвращает домен сервера хранения изображений."""

		# Сервер.
		Server = ""
		# ID серверов.
		ServersID = {
			"mangalib.me": 1,
			"yaoilib.me": 2,
			"hentailib.me": 4
		}
		# ID текущего сервера.
		CurrentServerID = ServersID[self.__Domain]
		# Запрос: серверные константы.
		Response = self.__Requestor.get(f"https://api.lib.social/api/constants?fields[]=imageServers", headers = {"Authorization": self.__Settings["token"]})

		# Если запрос успешен.
		if Response.status_code == 200:
			# Парсинг данных в JSON.
			Data = Response.json["data"]["imageServers"]

			# Для каждого сервера.
			for ServerData in Data:
				# Если сервер поддерживает текущий домен, записать его URL.
				if ServerData["id"] == self.__Settings["server"] and CurrentServerID in ServerData["site_ids"]: Server = ServerData["url"]

		else:
			# Запись в лог ошибки: не удалось получить список серверов.
			logging.error("Title: \"" + self.__Slug + "\". Unable to load servers constants.")

		return Server

	def __GetStatus(self, data: dict) -> str:
		"""
		Получает статус.
			data – словарь данных тайтла.
		"""

		# Статус тайтла.
		Status = "UNKNOWN"
		# Статусы тайтлов.
		Statuses = {
			1: "ONGOING",
			2: "COMPLETED",
			3: "ABANDONED",
			4: "ABANDONED"
		}
		# Индекс статуса на сайте.
		SiteStatusIndex = data["status"]["id"]
		# Если индекс статуса валиден, преобразовать его в поддерживаемый статус.
		if SiteStatusIndex in Statuses.keys(): Status = Statuses[SiteStatusIndex]

		return Status

	def __GetType(self, data: dict) -> str:
		"""
		Получает тип тайтла.
			data – словарь данных тайтла.
		"""

		# Тип тайтла.
		Type = "UNKNOWN"
		# Типы тайтлов.
		Types = {
			"Манга": "MANGA",
			"Манхва": "MANHWA",
			"Руманга": "RUS_COMIC",
			"Комикс западный": "WESTERN_COMIC",
			"OEL-манга": "OEL",
			"Маньхуа": "MANHUA"
		}
		# Определение с сайта.
		SiteType = data["type"]["label"]
		# Если определение с сайта валидно, преобразовать его.
		if SiteType in Types.keys(): Type = Types[SiteType]

		return Type

		# Дополняет тайтл информацией о слайдах из локального JSON.

	def __Merge(self):
		# Локальный тайтл.
		LocalTitle = None
		# Локальные определения слайдов.
		LocalSlides = dict()
		# Количество скопированных глав.
		MergedChaptersCount = 0

		# Если существует файл с ID в названии.
		if os.path.exists(self.__Settings["titles-directory"] + "/" + str(self.__Title["id"]) + ".json"):
			# Чтение локального файла.
			LocalTitle = ReadJSON(self.__Settings["titles-directory"] + "/" + str(self.__Title["id"]) + ".json")
			
		# Если существует файл с алиасом в названии.
		elif os.path.exists(self.__Settings["titles-directory"] + "/"  + self.__Slug + ".json"):
			# Чтение локального файла.
			LocalTitle = ReadJSON(self.__Settings["titles-directory"] + "/"  + self.__Slug + ".json")
			
		# Если локальный тайтл прочитан.
		if LocalTitle != None:
			
			# Если отключен режим перезаписи.
			if self.__ForceMode == False:
				# Запись в лог сообщения: найден локальный файл.
				logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Merging...")
			
				# Для каждой ветви.
				for BranchID in LocalTitle["chapters"]:
			
					# Для каждой главы.
					for Chapter in LocalTitle["chapters"][BranchID]:
						# Записать информацию о слайдах.
						LocalSlides[Chapter["id"]] = Chapter["slides"]
					
				# Для каждой ветви.
				for BranchID in self.__Title["chapters"]:
			
					# Для каждой главы.
					for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
					
						# Если для главы с таким ID найдены слайды.
						if self.__Title["chapters"][BranchID][ChapterIndex]["id"] in LocalSlides.keys():
							# Записать информацию о слайдах.
							self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = LocalSlides[self.__Title["chapters"][BranchID][ChapterIndex]["id"]]
							# Инкремент количества объединённых глав.
							MergedChaptersCount += 1
						
				# Запись в лог сообщения: завершение слияния.
				logging.info("Title: \"" + self.__Slug + "\". Merged chapters: " + str(MergedChaptersCount) + ".")

	def __init__(self,
			  settings: dict,
			  requestor: WebRequestor,
			  slug: str,
			  domain: str = "mangalib.me",
			  force_mode: bool = False,
			  message: str = "",
			  amending: bool = True
		):
		"""
		Парсер тайтла.
			settings – глобальные настройки;
			requestor – менеджер запросов;
			slug – алиас тайтла;
			domain – домен сайта;
			force_mode – указывает, перезаписывать ли существующие локальные данные;
			message – сообщение из внешнего обработчика;
			amending – указывает, следует ли дополнять главы информацией о слайдах.
		"""
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Сообщение из внешнего обработчика.
		self.__Message = message + "Current title: " + slug + "\n"
		# Состояние: включена ли перезапись файлов.
		self.__ForceMode = force_mode
		# Глобальные настройки.
		self.__Settings = settings.copy()
		# Обработчик навигации.
		self.__Requestor = requestor
		# Состояние: доступен ли тайтл.
		self.__IsActive = True
		# Домен.
		self.__Domain = domain
		# Описательная структура тайтла.
		self.__Title = {
			"format": "dmp-v1",
			"site": None,
			"id": None,
			"slug": slug,
			"covers": list(),
			"ru-name": None,
			"en-name": None,
			"another-names": None,
			"author": None,
			"publication-year": None,
			"age-rating": None,
			"description": None,
			"type": None,
			"status": None,
			"is-licensed": None,
			"series": list(),
			"genres": list(),
			"tags": list(),
			"branches": list(),
			"chapters": dict()
		}
		# Данные тайтла.
		self.__Data = None
		# Алиас тайтла.
		self.__Slug = slug
		# Выбранный сервер.
		self.__Server = self.__GetServer()
		
		# Очистка консоли.
		Cls()
		# Вывод в консоль: сообщение из внешнего обработчика и алиас обрабатываемого тайтла.
		print(self.__Message, end = "")
		# Запись в лог сообщения: парсинг начат.
		logging.info("Title: \"" + self.__Slug + "\". Parsing...")
		
		#---> Получение данных о тайтле.
		#==========================================================================================#
		# Запрос описания тайтла.
		self.__GetTitle()
		
		# Если тайтл доступен.
		if self.__IsActive == True:
			
			# Если отключен режим перезаписи.
			if force_mode == False:
				# Попытка слияния.
				self.__Merge()
				
			else:
				# Запись в лог сообщения: найден локальный описательный файл тайтла.
				logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Will be overwritten...")
			
			# Если включено дополнение глав, то дополнить.
			if amending == True: self.__Amend()
		
	def download_covers(self):
		"""Загружает обложки."""

		# Если тайтл активен.
		if self.__IsActive == True:
			# Используемое имя тайтла.
			UsedName = None
			# Если каталог обложек не существует, создать его.
			if not os.path.exists(self.__Settings["covers-directory"]): os.makedirs(self.__Settings["covers-directory"])
			# Очистка консоли.
			Cls()
		
			# Если вместо алиаса используется ID.
			if self.__Settings["use-id-instead-slug"] == True:
				# Установка имени тайтла.
				UsedName = str(self.__Title["id"])
			
				# Если существует папка для обложек с альтернативным названием алиасом.
				if os.path.exists(self.__Settings["covers-directory"] + "/"  + self.__Slug) == True:
					# Удаление старой обложки.
					RemoveFolderContent(self.__Settings["covers-directory"] + "/"  + self.__Slug)
					# Удаление папки с алиасом в названии.
					os.rmdir(self.__Settings["covers-directory"] + "/"  + self.__Slug)
				
			else:
				# Установка имени тайтла.
				UsedName = str(self.__Slug)
			
				# Если существует папка для обложек с альтернативным названием ID.
				if os.path.exists(self.__Settings["covers-directory"] + "/"  + str(self.__Title["id"])) == True:
					# Удаление старой обложки.
					RemoveFolderContent(self.__Settings["covers-directory"] + "/"  + str(self.__Title["id"]))
					# Удаление папки с алиасом в названии.
					os.rmdir(self.__Settings["covers-directory"] + "/"  + str(self.__Title["id"]))
				
			# Если включен режим перезаписи.
			if self.__ForceMode == True:
			
				try:
					# Удаление следов старой обложки.
					RemoveFolderContent(self.__Settings["covers-directory"] + "/"  + UsedName)
					os.rmdir(self.__Settings["covers-directory"] + "/"  + UsedName)
				
				except: pass
			
			# Если обложка не загружена.
			if os.path.exists(self.__Settings["covers-directory"] + "/"  + UsedName + "/" + self.__Title["covers"][0]["filename"]) == False:
				# Если папка не существует, создать папку для обложки.
				if os.path.exists(self.__Settings["covers-directory"] + "/"  + UsedName) == False: os.mkdir(self.__Settings["covers-directory"] + "/"  + UsedName)
				# Вывод в консоль: загрузка обложки.
				print(self.__Message + "\nDownloading cover: \"" + self.__Title["covers"][0]["link"] + "\"... ", end = "")
				# Загрузка изображения.
				Response = self.__Requestor.get(self.__Title["covers"][0]["link"])
			
				# Если запрос успешен.
				if Response.status_code == 200:
				
					# Открытие файла для записи.
					with open(self.__Settings["covers-directory"] + "/"  + UsedName + "/" + self.__Title["covers"][0]["filename"], "wb") as FileWriter:
						# Запись файла обложки.
						FileWriter.write(Response.content)
						# Вывод в консоль: загрузка завершена.
						print("Done.")
						# Запись в лог сообщения: обложка загружена.
						logging.info("Title: \"" + self.__Slug + "\". Cover downloaded.")
					
				else:
					# Вывод в консоль: загрузка прервана.
					print("Error!")
				
			else:
				# Запись в лог сообщения: обложка уже загружена.
				logging.info("Title: \"" + self.__Slug + "\". Cover already exists. Skipped.")
			
	def repair_chapter(self, ChapterID: int | str):
		"""Заново получает слайды в конкретной главе."""

		# Приведение ID главы к целочисленному.
		ChapterID = int(ChapterID)
		# Состояние: восстановлена ли глава.
		IsRepaired = False		

		# Для каждой ветви.
		for BranchID in self.__Title["chapters"].keys():
			
			# Для каждый главы.
			for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
				
				# Если ID совпадает с искомым.
				if self.__Title["chapters"][BranchID][ChapterIndex]["id"] == ChapterID:
					# Переключение состояния.
					IsRepaired = True
					# Получение списка слайдов главы.
					Slides = self.__GetChapterSlides(
						self.__Title["chapters"][BranchID][ChapterIndex]["number"],
						self.__Title["chapters"][BranchID][ChapterIndex]["volume"],
						BranchID
					)
					# Запись в лог сообщения: глава дополнена.
					logging.info("Title: \"" + self.__Slug + "\". Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " repaired.")
					# Запись информации о слайде.
					self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = Slides
					
		# Если глава восстановлена.
		if IsRepaired == False:
			# Запись в лог критической ошибки: глава не найдена.
			logging.critical("Title: \"" + self.__Slug + f"\". Chapter {ChapterID} not found.")
			# Выброс исключения.
			raise Exception(f"Chapter with ID {ChapterID} not found.")
	
	def save(self):
		"""Сохраняет данные в локальный файл."""

		# Используемое имя тайтла.
		UsedName = None
		# Если каталог тайтлов не существует, создать его.
		if not os.path.exists(self.__Settings["titles-directory"]): os.makedirs(self.__Settings["titles-directory"])
		
		# Если вместо алиаса используется ID.
		if self.__Settings["use-id-instead-slug"]:
			# Установка имени тайтла.
			UsedName = str(self.__Title["id"])
			# Если существует JSON с альтернативным названием алиасом.
			if os.path.exists(self.__Settings["titles-directory"] + "/"  + self.__Slug + ".json") == True: os.remove(self.__Settings["titles-directory"] + "/"  + self.__Slug + ".json")
				
		else:
			# Установка имени тайтла.
			UsedName = str(self.__Slug)
			# Если существует JSON с альтернативным названием ID.
			if os.path.exists(self.__Settings["titles-directory"] + "/"  + str(self.__Title["id"]) + ".json") == True: os.remove(self.__Settings["titles-directory"] + "/"  + str(self.__Title["id"]) + ".json")
			
		# Если тайтл активен, записать JSON.
		if self.__IsActive: WriteJSON(self.__Settings["titles-directory"] + "/"  + UsedName + ".json", self.__Title)