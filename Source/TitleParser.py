from dublib.Methods import Cls, ReadJSON, RemoveFolderContent, RemoveRecurringSubstrings, WriteJSON
from dublib.WebRequestor import WebRequestor
from Source.Functions import ToInt
from bs4 import BeautifulSoup
from time import sleep

import logging
import json
import os

# Список жанров.
GENRES = [
	"арт",	
	"безумие",	
	"боевик",	
	"боевые искусства",	
	"вампиры",	
	"военное",	
	"гарем",	
	"гендерная интрига",	
	"героическое фэнтези",	
	"демоны",	
	"детектив",	
	"детское",	
	"дзёсэй",	
	"драма",	
	"игра",	
	"исекай",	
	"история",	
	"киберпанк",	
	"кодомо",	
	"комедия",	
	"махо-сёдзё",	
	"машины",	
	"меха",	
	"мистика",	
	"музыка",	
	"научная фантастика",	
	"омегаверс",	
	"пародия",	
	"повседневность",	
	"полиция",	
	"постапокалиптика",	
	"приключения",	
	"психология",	
	"романтика",	
	"самурайский боевик",	
	"сверхъестественное",	
	"сёдзё",	
	"сёдзё-ай",	
	"сёнэн",	
	"сёнэн-ай",	
	"спорт",	
	"супер сила",	
	"сэйнэн",	
	"трагедия",	
	"триллер",	
	"ужасы",	
	"фантастика",	
	"фэнтези",	
	"школа",	
	"эротика",	
	"этти",	
	"юри",	
	"яой"
]

# Парсер тайтлов.
class TitleParser:
	
	# Дополняет главы информацией о слайдах.
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
						self.__Title["chapters"][BranchID][ChapterIndex]["id"],
						self.__Title["chapters"][BranchID][ChapterIndex]["CHAPTER_SLUG"],
						self.__Title["chapters"][BranchID][ChapterIndex]["number"],
						self.__Title["chapters"][BranchID][ChapterIndex]["volume"],
						BranchID[len(str(self.__Title["id"])):]
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

	# Строит ветви.
	def __BuildBranches(self, Data: dict) -> list[dict]:
		# Словарь ветвей.
		BranchesDictionary = dict()
		# Список ветвей.
		Branches = list()
		
		# Для каждой главы.
		for Chapter in Data["chapters"]["list"]:
			
			# Если глава не принадлежит ветви перевода.
			if Chapter["branch_id"] == None:
				# ID ветви.
				BranchID = str(self.__Title["id"]) + str(0)
				
				# Если ветвь уже определена.
				if BranchID in BranchesDictionary.keys(): 
					# Инкремент количества глав.
					BranchesDictionary[BranchID]["chapters-count"] += 1
					
				else:
					# Создание ветви.
					BranchesDictionary[BranchID] = {
						"id": int(BranchID),
						"chapters-count": 1
					}
				
			else:
				# ID ветви.
				BranchID = str(self.__Title["id"]) + str(Chapter["branch_id"])
				
				# Если ветвь уже определена.
				if BranchID in BranchesDictionary.keys(): 
					# Инкремент количества глав.
					BranchesDictionary[BranchID]["chapters-count"] += 1
					
				else:
					# Создание ветви.
					BranchesDictionary[BranchID] = {
						"id": int(BranchID),
						"chapters-count": 1
					}
				
		# Для каждой ветви записать значение в список.
		for BranchID in BranchesDictionary.keys(): Branches.append(BranchesDictionary[BranchID])
		
		return Branches
	
	# Строит главы.
	def __BuildChapters(self, Data: dict) -> dict:
		# Структура глав.
		Chapters = dict()
		
		# Для каждой описанной ветви.
		for Branch in self.__Title["branches"]:
			
			# Если ID ветви ещё нет в структуре глав, то создать.
			if str(Branch["id"]) not in Chapters.keys(): Chapters[str(Branch["id"])] = list()
		
		# Для каждой главы с сервера.
		for Chapter in Data["chapters"]["list"]:
			# Буфер главы.
			Bufer = {
				"id": Chapter["chapter_id"],
				"volume": Chapter["chapter_volume"],
				"number": float(Chapter["chapter_number"]) if "." in Chapter["chapter_number"] else int(Chapter["chapter_number"]),
				"name": Chapter["chapter_name"] if Chapter["chapter_name"] != "" else None,
				"is-paid": True if (Chapter["price"]) > 0 else False,
				"translator": None,
				"CHAPTER_SLUG": Chapter["chapter_slug"],
				"slides": list()
			}
			
			# Генерация ID ветви.
			BranchID = str(self.__Title["id"]) + (str(ToInt(Chapter["branch_id"])) if Chapter["branch_id"] != None else "0")
				
			# Поиск нужной ветви.
			for Branch in Data["chapters"]["branches"]:
					
				# Если найдена нужная ветвь, записать переводчика.
				if Branch["id"] == Chapter["branch_id"] and len(Branch["teams"]) > 0: Bufer["translator"] = Branch["teams"][0]["name"]

			# Запись главы.
			Chapters[BranchID].append(Bufer)
			
		# Для каждой ветви.
		for BranchID in Chapters.keys():
			# Сортировка глав по возрастанию.
			Chapters[BranchID] = sorted(Chapters[BranchID], key = lambda Value: (Value["volume"], Value["number"])) 
		
		return Chapters
	
	# Проверяет, лицензирован ли тайтл.
	def __CheckLicense(self, Page: str) -> bool:
		# Состояние: лицензирован ли тайтл.
		IsLicensed = False
		# Если главы удалены, сменить статус лицензии.
		if "Главы удалены по требованию правообладателя." in Page: IsLicensed = True
		
		return IsLicensed
	
	# Вовзращает возрастное ограничение.
	def __GetAgeRating(self, Page: str) -> int:
		# Возрастное ограничение.
		Rating = 0
		# Поиск списка данных.
		MediaList = Page.find("div", {"class": "media-info-list paper"})
		# Поиск всех ссылок.
		InfoLinks = MediaList.find_all("a")
		
		# Для каждой ссылки.
		for Link in InfoLinks:
			
			# Если блок содержит возрастное ограничение.
			if "Возрастной рейтинг" in str(Rating):
				# Получение возрастного ограничения.
				Rating = int(Link.get_text().replace("Возрастной рейтинг", "").strip("\n +"))
	
		return Rating
	
	# Возвращает имя автора.
	def __GetAuthor(self, Page: str) -> str | None:
		# Имя автора.
		Author = None
		# Поиск блоков описания.
		InfoBlocks = Page.find_all("div", {"class": "media-info-list__item"})
		
		# Для каждого блока.
		for Block in InfoBlocks:
			
			# Если блок содержит возрастное ограничение.
			if "Автор" in str(Block):
				# Получение возрастного ограничения.
				Author = Block.get_text().replace("Автор", "").strip()
	
		return Author
	
	# Возвращает список слайдов главы.
	def __GetChapterSlides(self, ChapterID: int| str, ChapterSlug: str, Number: float | int | str, Volume: int | str, BranchID: int | str = str(), FromJavaScript: bool = True) -> list[dict]:
		# Список слайдов.
		Slides = list()
		
		# Если используется метод получения слайдов со страницы загрузки.
		if FromJavaScript == False:
			# Запрос данных главы.
			Response = self.__Requestor.get(f"https://{self.__Domain}/download/{ChapterSlug}")
			# Конвертирование ответа в словарь.
			Data = json.loads(Response.text)
		
			# Для каждого изображения.
			for ImageIndex in range(0, len(Data["images"])):
				# Буфер слайда.
				Bufer = {
					"index": ImageIndex + 1,
					"link": Data["downloadServer"] + "/manga/" + self.__Title["slug"] + f"/chapters/{ChapterID}/" + Data["images"][ImageIndex],
					"width": None,
					"height": None
				}
				# Экранирование пробелов URL.
				Bufer["link"] = Bufer["link"].replace(" ", "%20")
				# Запись информации о слайде.
				Slides.append(Bufer)
				
		else:
			# Параметры запроса.
			RequestParams = {
				"ui": self.__Settings["user-id"],
				"bid": str(BranchID)
			}
			# Если не задана ветвь, удалить параметр запроса.
			if BranchID == "" or str(BranchID) == "0": del RequestParams["bid"]
			# Запрос страницы главы.
			Response = self.__Requestor.get(f"https://{self.__Domain}/{self.__Slug}/v{Volume}/c{Number}", params = RequestParams)
			# Парсинг страницы главы.
			Soup = BeautifulSoup(Response.text, "html.parser")
			# Поиск блока JavaScript, определяющего имена файлов изображений.
			ImagesScript = Soup.find("script", {"id": "pg"})
			
			# Если слайды присутствуют.
			if ImagesScript != None:
				# Получение кода JavaScript.
				ImagesScript = ImagesScript.get_text()
				# Преобразование скрипта в словарь.
				Data = json.loads(ImagesScript.replace("window.__pg", "").strip("= ;\n"))
				# Текущий сервер.
				Server = self.__GetServersList(Soup)[self.__Server]
			
				# Для каждого изображения.
				for ImageIndex in range(0, len(Data)):
					# Если изображение является GIF, задать вторичный сервер.
					if Data[ImageIndex]["u"].lower().endswith(".gif") == True: Server = self.__GetServersList(Soup)["secondary"]
					# Буфер слайда.
					Bufer = {
						"index": ImageIndex + 1,
						"link": Server + "/manga/" + self.__Title["slug"] + f"/chapters/{ChapterSlug}/" + Data[ImageIndex]["u"],
						"width": None,
						"height": None
					}
					# Экранирование пробелов URL.
					Bufer["link"] = Bufer["link"].replace(" ", "%20")
					# Запись информации о слайде.
					Slides.append(Bufer)
					
			else:
				# Запись в лог предупреждения: не удалось получить слайды.
				logging.warning(f"Title: \"{self.__Slug}\". Chapter {ChapterID}. Unable to load slides. Request code: {Response.status_code}.")
			
		return Slides
	
	# Возвращает описание обложки.
	def __GetCover(self, Page: str) -> dict:
		# Буфер описания.
		Bufer = {
			"link": None,
			"filename": None,
			"width": None,
			"height": None
		}
		
		# Поиск блока с обложкой.
		Cover = Page.find("div", {"class": "media-sidebar__cover paper"})
		# Поиск обложки.
		Cover = Cover.find("img")
		# Получение ссылки на обложку.
		Bufer["link"] = Cover["src"]
		# Получение названия файла обложки.
		Bufer["filename"] = Bufer["link"].split("/")[-1]
		
		return Bufer
	
	# Возвращает описание тайтла.
	def __GetDescription(self, Page: str) -> str:
		# Блок описания.
		DescriptionBlock = Page.find("div", {"class": "media-description__text"})
		# Описание.
		Description = None
		# Если описание есть, записать его.
		if DescriptionBlock != None: Description = RemoveRecurringSubstrings(DescriptionBlock.get_text().strip().replace("\r", ""), "\n")

		return Description
	
	# Возвращает список жанров.
	def __GetGenres(self, Page: str) -> list[str]:
		# Поиск контейнера тегов.
		TagsContainer = Page.find("div", {"class": "media-tags"})
		# Список ссылок тегов.
		TagsLinks = TagsContainer.find_all("a")
		# Список тегов.
		Tags = list()
		# Список жанров.
		Genres = list()
		
		# Для каждой ссылки сохранить название тега.
		for Link in TagsLinks: Tags.append(Link.get_text().strip().lower())
		
		# Для каждого тега.
		for Index in range(0, len(Tags)):
			
			# Если тег является жанром.
			if Tags[Index] in GENRES:
				# Запись жанра.
				Genres.append(Tags[Index])

		return Genres
	
	# Возвращает год публикации.
	def __GetPublicationYear(self, Page: str) -> int | None:
		# Поиск списка данных.
		MediaList = Page.find("div", {"class": "media-info-list paper"})
		# Поиск всех ссылок.
		InfoLinks = MediaList.find_all("a")
		# Год публикации.
		Year = None
		
		# Для каждой ссылки.
		for Link in InfoLinks:
			
			# Если блок содержит год релиза.
			if "Год релиза" in str(Link):
				# Получение года.
				Year = int(Link.get_text().replace("Год релиза", "").strip())
	
		return Year
	
	# Возвращает список серий.
	def __GetSeries(self, Page: str) -> list:
		# Поиск медиа блоков.
		MediaBlocks = Page.find_all("div", {"class": "media-info-list__item"})
		# Список серий.
		Series = list()
		
		# Для каждого блока.
		for Block in MediaBlocks:
			
			# Если блок содержит список серий.
			if "Серия" in str(Block):
				# Поиск ссылок на серии.
				SeriesLinks = Block.find_all("a")
				
				# Для каждой ссылки.
				for Link in SeriesLinks:
					# Запись серии.
					Series.append(Link.get_text().strip())
	
		return Series
	
	# Возвращает словарь серверов изображений.
	def __GetServersList(self, Page: str) -> dict | None:
		# Поиск блоков скриптов.
		Scripts = Page.find_all("script")
		# Словарь серверов.
		Data = None 
		
		# Для каждого блока скрипта.
		for Script in Scripts:
			
			# Если найден нужный блок.
			if "window.__info" in str(Script):
				# Получение строки данных окна.
				WindowInfo = Script.get_text().split("window.__info")[-1].split("window._SITE_COLOR_")[0].strip("[= ;\n]")
				# Преобразование данных окна в словарь.
				Data = json.loads(WindowInfo)["servers"]
		
		return Data
	
	# Возвращает статус.
	def __GetStatus(self, Page: str, Data: dict) -> str:
		# Статус тайтла.
		Status = "UNKNOWN"
		# Статусы тайтлов.
		Statuses = {
			1: "ONGOING",
			2: "COMPLETED",
			3: "ABANDONED",
			4: "ABANDONED"
		}
		# Поиск списка данных.
		MediaList = Page.find("div", {"class": "media-info-list paper"})
		# Поиск всех ссылок.
		InfoLinks = MediaList.find_all("a")
		# Интерпретация статуса.
		if Data["manga"]["status"] in Statuses.keys(): Status = Statuses[Data["manga"]["status"]]
		
		# Для каждой ссылки.
		for Link in InfoLinks:
			
			# Если блок содержит статус анонса, заменить статус.
			if "Статус тайтла" in str(Link) and "Анонс" in str(Link): Status = "ANNOUNCED"

		return Status
	
	# Возвращает список тегов.
	def __GetTags(self, Page: str) -> list[str]:
		# Поиск контейнера тегов.
		TagsContainer = Page.find("div", {"class": "media-tags"})
		# Список ссылок тегов.
		TagsLinks = TagsContainer.find_all("a")
		# Список всех тегов.
		AllTags = list()
		# Список тегов.
		Tags = list()
		
		# Для каждой ссылки сохранить название тега.
		for Link in TagsLinks: AllTags.append(Link.get_text().strip().lower())
		
		# Для каждого тега.
		for Index in range(0, len(AllTags)):
			
			# Если тег не является жанром.
			if AllTags[Index] not in GENRES:
				# Запись тега.
				Tags.append(AllTags[Index])

		return Tags
	
	# Получает тайтл.
	def __GetTitle(self):
		# Запрос страницы описания тайтла.
		Response = self.__Requestor.get(f"https://{self.__Domain}/{self.__Slug}?section=info")
		
		# Если запрос успешен.
		if Response.status_code == 200 and "Данный тайтл недоступно на территории РФ." not in Response.text:
			# Парсинг страницы описания.
			Page = BeautifulSoup(Response.text, "html.parser")
			# Получение данных тайтла.
			self.__Data = self.__GetTitleData(Page)
			# Заполнение описания тайтла.
			self.__Title["site"] = self.__Domain.replace("v1.", "").replace(".org", ".me")
			self.__Title["id"] = self.__Data["manga"]["id"]
			self.__Title["slug"] = self.__Slug
			self.__Title["covers"] = list()
			self.__Title["ru-name"] = self.__Data["manga"]["rusName"] if self.__Data["manga"]["rusName"] != "" else None
			self.__Title["en-name"] = self.__Data["manga"]["engName"] if self.__Data["manga"]["engName"] != "" else None
			self.__Title["another-names"] = self.__Data["manga"]["altNames"]
			self.__Title["author"] = self.__GetAuthor(Page)
			self.__Title["publication-year"] = self.__GetPublicationYear(Page)
			self.__Title["age-rating"] = self.__GetAgeRating(Page)
			self.__Title["description"] = self.__GetDescription(Page)
			self.__Title["type"] = self.__GetType(Page)
			self.__Title["status"] = self.__GetStatus(Page, self.__Data)
			self.__Title["is-licensed"] = self.__CheckLicense(Page)
			self.__Title["series"] = self.__GetSeries(Page)
			self.__Title["genres"] = self.__GetGenres(Page)
			self.__Title["tags"] = self.__GetTags(Page)
			self.__Title["branches"] = self.__BuildBranches(self.__Data)
			self.__Title["chapters"] = self.__BuildChapters(self.__Data)
			
			# Если у тайтла нет ни одного названия, записать главное название.
			if self.__Title["ru-name"] == None and self.__Title["en-name"] == None and self.__Title["another-names"] == list(): self.__Title["another-names"].append(self.__Data["manga"]["name"])
			# Получение данных об обложке.
			self.__Title["covers"].append(self.__GetCover(Page))
			# Запись в лог сообщения: получено описание тайтла.
			logging.info("Title: \"" + self.__Title["slug"] + "\". Request title data... Done.")
			
		elif "Данный тайтл недоступно на территории РФ." in Response.text:
			# Запись в лог ошибки: тайтл недоступен на территории РФ.
			logging.error(f"Title: \"{self.__Slug}\". Not available on the territory of the Russian Federation.")
			# Переключение статуса тайтла.
			self.__IsActive = False
			
		else:
			
			# Если тайтл не найден.
			if Response.status_code == 404:
				# Запись в лог ошибки: тайтл не найден.
				logging.error("Title: \"" + self.__Title["slug"] + "\". Not found. Skipped.")
			
			# Запись в лог ошибки: нет доступа к тайтлу.
			logging.error("Title: \"" + self.__Slug + "\". Not accessed. Skipped.")
			# Переключение статуса тайтла.
			self.__IsActive = False
	
	# Возвращает JavaScript-словарь данных окна.
	def __GetTitleData(self, Page: str) -> dict:
		# Поиск блока скрипта.
		Script = Page.find("script").get_text()
		# Получение строки данных окна.
		WindowData = Script.strip().split("\n")[0].replace("window.__DATA__ = ", "").rstrip(";")
		# Преобразование данных окна в словарь.
		Data = json.loads(WindowData)
		
		return Data
	
	# Возвращает тип тайтла.
	def __GetType(self, Page: str) -> str:
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
		# Поиск списка данных.
		MediaList = Page.find("div", {"class": "media-info-list paper"})
		# Поиск всех ссылок.
		InfoLinks = MediaList.find_all("a")
		
		# Для каждой ссылки.
		for Link in InfoLinks:
			
			# Если блок содержит тип.
			if "Тип" in str(Link):
				# Получение типа.
				Type = Types[Link.get_text().replace("Тип", "").strip()]

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
		if os.path.exists(self.__Settings["titles-directory"] + str(self.__Title["id"]) + ".json"):
			# Чтение локального файла.
			LocalTitle = ReadJSON(self.__Settings["titles-directory"] + str(self.__Title["id"]) + ".json")
			
		# Если существует файл с алиасом в названии.
		elif os.path.exists(self.__Settings["titles-directory"] + self.__Slug + ".json"):
			# Чтение локального файла.
			LocalTitle = ReadJSON(self.__Settings["titles-directory"] + self.__Slug + ".json")
			
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
	
	# Конструктор.
	def __init__(self,
			  Settings: dict,
			  Requestor: WebRequestor,
			  Slug: str,
			  Domain: str = "mangalib.me",
			  Server: str = "compress",
			  ForceMode: bool = False,
			  Message: str = "",
			  Amending: bool = True
		):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Сообщение из внешнего обработчика.
		self.__Message = Message + "Current title: " + Slug + "\n"
		# Состояние: включена ли перезапись файлов.
		self.__ForceMode = ForceMode
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Обработчик навигации.
		self.__Requestor = Requestor
		# Состояние: доступен ли тайтл.
		self.__IsActive = True
		# Домен.
		self.__Domain = Domain
		# Описательная структура тайтла.
		self.__Title = {
			"format": "dmp-v1",
			"site": None,
			"id": None,
			"slug": None,
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
		self.__Slug = Slug
		# Выбранный сервер.
		self.__Server = Server
		
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
			if ForceMode == False:
				# Попытка слияния.
				self.__Merge()
				
			else:
				# Запись в лог сообщения: найден локальный описательный файл тайтла.
				logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Will be overwritten...")
			
			# Если включено дополнение глав, то дополнить.
			if Amending == True: self.__Amend()
		
	# Загружает обложку.
	def downloadCover(self):
		
		# Если тайтл активен.
		if self.__IsActive == True:
			# Используемое имя тайтла.
			UsedName = None
			# Очистка консоли.
			Cls()
		
			# Если вместо алиаса используется ID.
			if self.__Settings["use-id-instead-slug"] == True:
				# Установка имени тайтла.
				UsedName = str(self.__Title["id"])
			
				# Если существует папка для обложек с альтернативным названием алиасом.
				if os.path.exists(self.__Settings["covers-directory"] + self.__Slug) == True:
					# Удаление старой обложки.
					RemoveFolderContent(self.__Settings["covers-directory"] + self.__Slug)
					# Удаление папки с алиасом в названии.
					os.rmdir(self.__Settings["covers-directory"] + self.__Slug)
				
			else:
				# Установка имени тайтла.
				UsedName = str(self.__Slug)
			
				# Если существует папка для обложек с альтернативным названием ID.
				if os.path.exists(self.__Settings["covers-directory"] + str(self.__Title["id"])) == True:
					# Удаление старой обложки.
					RemoveFolderContent(self.__Settings["covers-directory"] + str(self.__Title["id"]))
					# Удаление папки с алиасом в названии.
					os.rmdir(self.__Settings["covers-directory"] + str(self.__Title["id"]))
				
			# Если включен режим перезаписи.
			if self.__ForceMode == True:
			
				try:
					# Удаление следов старой обложки.
					RemoveFolderContent(self.__Settings["covers-directory"] + UsedName)
					os.rmdir(self.__Settings["covers-directory"] + UsedName)
				
				except:
					pass
			
			# Если обложка не загружена.
			if os.path.exists(self.__Settings["covers-directory"] + UsedName + "/" + self.__Title["covers"][0]["filename"]) == False:
				# Если папка не существует, создать папку для обложки.
				if os.path.exists(self.__Settings["covers-directory"] + UsedName) == False: os.mkdir(self.__Settings["covers-directory"] + UsedName)
				# Вывод в консоль: загрузка обложки.
				print(self.__Message + "\nDownloading cover: \"" + self.__Title["covers"][0]["link"] + "\"... ", end = "")
				# Загрузка изображения.
				Response = self.__Requestor.get(self.__Title["covers"][0]["link"])
			
				# Если запрос успешен.
				if Response.status_code == 200:
				
					# Открытие файла для записи.
					with open(self.__Settings["covers-directory"] + UsedName + "/" + self.__Title["covers"][0]["filename"], "wb") as FileWriter:
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
			
	# Пересобирает слайды главы.
	def repairChapter(self, ChapterID: int | str):
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
						self.__Title["chapters"][BranchID][ChapterIndex]["id"],
						self.__Title["chapters"][BranchID][ChapterIndex]["CHAPTER_SLUG"],
						self.__Title["chapters"][BranchID][ChapterIndex]["number"],
						self.__Title["chapters"][BranchID][ChapterIndex]["volume"],
						BranchID[len(str(self.__Title["id"])):]
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
	
	# Сохраняет JSON файл описания.
	def save(self):
		# Используемое имя тайтла.
		UsedName = None
		
		# Для каждой ветви.
		for BranchID in self.__Title["chapters"].keys():
			
			# Для каждый главы.
			for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
				# Если указан алиас главы, удалить его.
				if "CHAPTER_SLUG" in self.__Title["chapters"][BranchID][ChapterIndex].keys(): del self.__Title["chapters"][BranchID][ChapterIndex]["CHAPTER_SLUG"]
		
		# Если вместо алиаса используется ID.
		if self.__Settings["use-id-instead-slug"] == True:
			# Установка имени тайтла.
			UsedName = str(self.__Title["id"])
			# Если существует JSON с альтернативным названием алиасом.
			if os.path.exists(self.__Settings["titles-directory"] + self.__Slug + ".json") == True: os.remove(self.__Settings["titles-directory"] + self.__Slug + ".json")
				
		else:
			# Установка имени тайтла.
			UsedName = str(self.__Slug)
			# Если существует JSON с альтернативным названием ID.
			if os.path.exists(self.__Settings["titles-directory"] + str(self.__Title["id"]) + ".json") == True: os.remove(self.__Settings["titles-directory"] + str(self.__Title["id"]) + ".json")
			
		# Если тайтл активен, записать JSON.
		if self.__IsActive: WriteJSON(self.__Settings["titles-directory"] + UsedName + ".json", self.__Title)