from Source.Core.Formats.Manga import BaseStructs, Manga, Statuses, Types
from Source.Core.ParserSettings import ParserSettings
from Source.Core.Downloader import Downloader
from Source.Core.Objects import Objects
from Source.CLI.Templates import *

from dublib.WebRequestor import Protocols, WebConfig, WebLibs, WebRequestor
from dublib.Methods.Data import RemoveRecurringSubstrings, Zerotify
from datetime import datetime
from time import sleep

#==========================================================================================#
# >>>>> ОПРЕДЕЛЕНИЯ <<<<< #
#==========================================================================================#

VERSION = "3.0.0"
NAME = "mangalib"
SITE = "test-front.mangalib.me"
STRUCT = Manga()

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Parser:
	"""Модульный парсер."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА ТОЛЬКО ДЛЯ ЧТЕНИЯ <<<<< #
	#==========================================================================================#

	@property
	def site(self) -> str:
		"""Домен целевого сайта."""

		return self.__Title["site"]

	@property
	def id(self) -> int:
		"""Целочисленный идентификатор."""

		return self.__Title["id"]

	@property
	def slug(self) -> str:
		"""Алиас."""

		return self.__Title["slug"]

	@property
	def content_language(self) -> str | None:
		"""Код языка контента по стандарту ISO 639-3."""

		return self.__Title["content_language"]

	@property
	def localized_name(self) -> str | None:
		"""Локализованное название."""

		return self.__Title["localized_name"]

	@property
	def en_name(self) -> str | None:
		"""Название на английском."""

		return self.__Title["en_name"]

	@property
	def another_names(self) -> list[str]:
		"""Список альтернативных названий."""

		return self.__Title["another_names"]

	@property
	def covers(self) -> list[dict]:
		"""Список описаний обложки."""

		return self.__Title["covers"]

	@property
	def authors(self) -> list[str]:
		"""Список авторов."""

		return self.__Title["authors"]

	@property
	def publication_year(self) -> int | None:
		"""Год публикации."""

		return self.__Title["publication_year"]

	@property
	def description(self) -> str | None:
		"""Описание."""

		return self.__Title["description"]

	@property
	def age_limit(self) -> int | None:
		"""Возрастное ограничение."""

		return self.__Title["age_limit"]

	@property
	def genres(self) -> list[str]:
		"""Список жанров."""

		return self.__Title["genres"]

	@property
	def tags(self) -> list[str]:
		"""Список тегов."""

		return self.__Title["tags"]

	@property
	def franchises(self) -> list[str]:
		"""Список франшиз."""

		return self.__Title["franchises"]

	@property
	def type(self) -> Types | None:
		"""Тип тайтла."""

		return self.__Title["type"]

	@property
	def status(self) -> Statuses | None:
		"""Статус тайтла."""

		return self.__Title["status"]

	@property
	def is_licensed(self) -> bool | None:
		"""Состояние: лицензирован ли тайтл на данном ресурсе."""

		return self.__Title["is_licensed"]

	@property
	def content(self) -> dict:
		"""Содержимое тайтла."""

		return self.__Title["content"]

	#==========================================================================================#
	# >>>>> СТАНДАРТНЫЕ ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CalculateEmptyChapters(self, content: dict) -> int:
		"""Подсчитывает количество глав без слайдов."""

		ChaptersCount = 0

		for BranchID in content.keys():

			for Chapter in content[BranchID]:
				if not Chapter["slides"]: ChaptersCount += 1

		return ChaptersCount

	def __InitializeRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов."""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.generate_user_agent("pc")
		Config.set_retries_count(self.__Settings.common.retries)
		Config.add_header("Authorization", self.__Settings.custom["token"])
		WebRequestorObject = WebRequestor(Config)
		
		if self.__Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTP,
			host = self.__Settings.proxy.host,
			port = self.__Settings.proxy.port,
			login = self.__Settings.proxy.login,
			password = self.__Settings.proxy.password
		)

		return WebRequestorObject

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ <<<<< #
	#==========================================================================================#

	def __IsSlideLink(self, link: str, servers: list[str]) -> bool:
		"""
		Проверяет, ведёт ли ссылка на слайд.
			link – ссылка на изображение;
			servers – список серверов изображений.
		"""

		for Server in servers:
			if Server in link: return True

		return False
	
	def __ParseSlideLink(self, link: str, servers: list[str]) -> tuple[str]:
		"""
		Парсит ссылку на слайд.
			link – ссылка на изображение;
			servers – список серверов изображений.
		"""

		OriginalServer = None
		URI = None

		for Server in servers:

			if Server in link:
				OriginalServer = Server
				URI = link.replace(OriginalServer, "")

		return (OriginalServer, URI)

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ ПАРСИНГА <<<<< #
	#==========================================================================================#

	def __GetAgeLimit(self, data: dict) -> int:
		"""
		Получает возрастной рейтинг.
			data – словарь данных тайтла.
		"""

		Rating = None
		RatingString = data["ageRestriction"]["label"].split(" ")[0].replace("+", "").replace("Нет", "")
		if RatingString.isdigit(): Rating = int(RatingString)

		return Rating 

	def __GetAuthors(self, data: dict) -> list[str]:
		"""Получает список авторов."""

		Authors = list()
		for Author in data["authors"]: Authors.append(Author["name"])

		return Authors

	def __GetContent(self) -> dict:
		"""Получает содержимое тайтла."""

		Content = dict()
		Response = self.__Requestor.get(f"https://api.lib.social/api/manga/{self.__Slug}/chapters")
		
		if Response.status_code == 200:
			Data = Response.json["data"]
			sleep(self.__Settings.common.delay)

			for Chapter in Data:

				for BranchData in Chapter["branches"]:
					BranchID = str(BranchData["branch_id"])
					if BranchID == "None": BranchID = str(self.__Title["id"]) + "0"
					if BranchID not in Content.keys(): Content[BranchID] = list()
					Translators = [sub["name"] for sub in BranchData["teams"]]
					Buffer = {
						"id": BranchData["id"],
						"volume": Chapter["volume"],
						"number": Chapter["number"],
						"name": Zerotify(Chapter["name"]),
						"is_paid": False,
						"translators": Translators,
						"slides": []	
					}
					Content[BranchID].append(Buffer)

		else:
			self.__SystemObjects.logger.request_error(Response, "Unable to request chapter.")

		return Content

	def __GetCovers(self, data: dict) -> list[str]:
		"""Получает список обложек."""

		Covers = list()

		if data["cover"]:
			Covers.append({
				"link": data["cover"]["default"],
				"filename": data["cover"]["default"].split("/")[-1]
			})

		if self.__Settings.common.sizing_images:
			Covers[0]["width"] = None
			Covers[0]["height"] = None

		return Covers

	def __GetDescription(self, data: dict) -> str | None:
		"""
		Получает описание.
			data – словарь данных тайтла.
		"""

		Description = None
		if "summary" in data.keys(): Description = RemoveRecurringSubstrings(data["summary"], "\n").strip().replace(" \n", "\n")
		Description = Zerotify(Description)

		return Description

	def __GetFranchises(self, data: dict) -> list[str]:
		"""
		Получает список серий.
			data – словарь данных тайтла.
		"""

		Franchises = list()
		for Franchise in data["franchise"]: Franchises.append(Franchise["name"])
		if "Оригинальные работы" in Franchises: Franchises.remove("Оригинальные работы")

		return Franchises

	def __GetGenres(self, data: dict) -> list[str]:
		"""
		Получает список жанров.
			data – словарь данных тайтла.
		"""

		Genres = list()
		for Genre in data["genres"]: Genres.append(Genre["name"])

		return Genres

	def __GetImagesServers(self, server_id: str | None = None, all_sites: bool = False) -> list[str]:
		"""
		Возвращает один или несколько доменов серверов хранения изображений.
			server_id – идентификатор сервера;\n
			all_sites – указывает, что вернуть нужно домены хранилищ изображений для всех сайтов.
		"""

		Servers = list()
		CurrentSiteID = self.__GetSiteID()
		URL = f"https://api.lib.social/api/constants?fields[]=imageServers"
		Headers = {
			"Authorization": self.__Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		Response = self.__Requestor.get(URL, headers = Headers)

		if Response.status_code == 200:
			Data = Response.json["data"]["imageServers"]
			sleep(self.__Settings.common.delay)

			for ServerData in Data:

				if server_id:
					if ServerData["id"] == server_id and CurrentSiteID in ServerData["site_ids"]: Servers.append(ServerData["url"])
					elif ServerData["id"] == server_id and all_sites: Servers.append(ServerData["url"])

				else:
					if CurrentSiteID in ServerData["site_ids"] or all_sites: Servers.append(ServerData["url"])

		else:
			self.__SystemObjects.logger.request_error(Response, "Unable to request site constants.")

		return Servers

	def __GetSiteID(self) -> int:
		"""Возвращает целочисленный идентификатор сайта."""

		SiteID = None
		if "mangalib" in SITE: SiteID = 1
		if "yaoilib" in SITE or "slashlib" in SITE: SiteID = 2
		if "hentailib" in SITE: SiteID = 4
		
		return SiteID

	def __GetSlides(self, number: str, volume: str, branch_id: str) -> list[dict]:
		"""
		Получает данные о слайдах главы.
			number – номер главы;\n
			volume – номер тома;\n
			branch_id – ID ветви.
		"""

		Slides = list()
		Server = self.__GetImagesServers(self.__Settings.custom["server"])[0]
		Branch = "" if branch_id == str(self.__Title["id"]) + "0" else f"&branch_id={branch_id}"
		URL = f"https://api.lib.social/api/manga/{self.__Slug}/chapter?number={number}&volume={volume}{Branch}"
		Headers = {
			"Authorization": self.__Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		Response = self.__Requestor.get(URL, headers = Headers)
		
		if Response.status_code == 200:
			Data = Response.json["data"]["pages"]
			sleep(self.__Settings.common.delay)

			for SlideIndex in range(len(Data)):
				Buffer = {
					"index": SlideIndex + 1,
					"link": Server + Data[SlideIndex]["url"].replace(" ", "%20")
				}

				if self.__Settings.common.sizing_images:
					Buffer["width"] = Data[SlideIndex]["width"]
					Buffer["height"] = Data[SlideIndex]["height"]

				Slides.append(Buffer)

		else:
			self.__SystemObjects.logger.request_error(Response, "Unable to request chapter content.")

		return Slides

	def __GetStatus(self, data: dict) -> str:
		"""
		Получает статус.
			data – словарь данных тайтла.
		"""

		Status = None
		StatusesDetermination = {
			1: Statuses.ongoing,
			2: Statuses.completed,
			3: Statuses.announced,
			4: Statuses.dropped,
			5: Statuses.dropped
		}
		SiteStatusIndex = data["status"]["id"]
		if SiteStatusIndex in StatusesDetermination.keys(): Status = StatusesDetermination[SiteStatusIndex]

		return Status

	def __GetTitleData(self) -> dict | None:
		"""
		Получает данные тайтла.
			slug – алиас.
		"""

		URL = f"https://api.lib.social/api/manga/{self.__Slug}?fields[]=eng_name&fields[]=otherNames&fields[]=summary&fields[]=releaseDate&fields[]=type_id&fields[]=caution&fields[]=genres&fields[]=tags&fields[]=franchise&fields[]=authors&fields[]=manga_status_id&fields[]=status_id"
		Headers = {
			"Authorization": self.__Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		Response = self.__Requestor.get(URL, headers = Headers)

		if Response.status_code == 200:
			Response = Response.json["data"]
			self.__SystemObjects.logger.parsing_start(self.__Slug, Response["id"])
			sleep(self.__Settings.common.delay)

		else:
			self.__SystemObjects.logger.request_error(Response, "Unable to request title data.")
			Response = None

		return Response

	def __GetTags(self, data: dict) -> list[str]:
		"""
		Получает список тегов.
			data – словарь данных тайтла.
		"""

		Tags = list()
		for Tag in data["tags"]: Tags.append(Tag["name"])

		return Tags

	def __GetType(self, data: dict) -> str:
		"""
		Получает тип тайтла.
			data – словарь данных тайтла.
		"""

		Type = None
		TypesDeterminations = {
			"Манга": Types.manga,
			"Манхва": Types.manhwa,
			"Маньхуа": Types.manhua,
			"Руманга": Types.russian_comic,
			"Комикс западный": Types.western_comic,
			"OEL-манга": Types.oel
		}
		SiteType = data["type"]["label"]
		if SiteType in TypesDeterminations.keys(): Type = TypesDeterminations[SiteType]

		return Type

	def __StringToDate(self, date_str: str) -> datetime:
		"""
		Преобразует строковое время в объектную реализацию.
			date_str – строковая интерпретация.
		"""

		DatePattern = "%Y-%m-%dT%H:%M:%S.%fZ"

		return datetime.strptime(date_str, DatePattern)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: Objects, settings: ParserSettings):
		"""
		Модульный парсер.
			system_objects – коллекция системных объектов;\n
			settings – настройки парсера.
		"""

		system_objects.logger.select_parser(NAME)

		#---> Генерация динамических свойств.
		#==========================================================================================#
		self.__Settings = settings
		self.__Requestor = self.__InitializeRequestor()
		self.__Title = None
		self.__Slug = None
		self.__SystemObjects = system_objects

	def amend(self, content: dict | None = None, message: str = "") -> dict:
		"""
		Дополняет каждую главу в кажой ветви информацией о содержимом.
			content – содержимое тайтла для дополнения;\n
			message – сообщение для портов CLI.
		"""

		if content == None: content = self.content
		ChaptersToAmendCount = self.__CalculateEmptyChapters(content)
		AmendedChaptersCount = 0
		ProgressIndex = 0

		for BranchID in content.keys():
			
			for ChapterIndex in range(0, len(content[BranchID])):
				
				if content[BranchID][ChapterIndex]["slides"] == []:
					ProgressIndex += 1
					Slides = self.__GetSlides(
						content[BranchID][ChapterIndex]["number"],
						content[BranchID][ChapterIndex]["volume"],
						BranchID
					)

					if Slides:
						AmendedChaptersCount += 1
						content[BranchID][ChapterIndex]["slides"] = Slides
						self.__SystemObjects.logger.chapter_amended(self.__Slug, self.__Title["id"], content[BranchID][ChapterIndex]["id"], False)

					PrintAmendingProgress(message, ProgressIndex, ChaptersToAmendCount)
					sleep(self.__Settings.common.delay)

		self.__SystemObjects.logger.amending_end(self.__Slug, self.__Title["id"], AmendedChaptersCount)

		return content

	def image(self, url: str) -> str | None:
		"""
		Скачивает изображение с сайта во временный каталог парсера и возвращает его название.
			url – ссылка на изображение.
		Возвращает название файла.
		"""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.requests.enable_proxy_protocol_switching(True)
		WebRequestorObject = WebRequestor(Config)

		if self.__Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTP,
			host = self.__Settings.proxy.host,
			port = self.__Settings.proxy.port,
			login = self.__Settings.proxy.login,
			password = self.__Settings.proxy.password
		)

		Result = Downloader(self.__SystemObjects, WebRequestorObject).temp_image(NAME, url, referer = SITE)
		
		if Result.code not in Config.good_statusses:
			Servers = self.__GetImagesServers(all_sites = True)

			if self.__IsSlideLink(url, Servers):
				OriginalServer, ImageURI = self.__ParseSlideLink(url, Servers)
				Servers.remove(OriginalServer)
				sleep(self.__Settings.common.delay)

				for Server in Servers:
					Link = Server + ImageURI
					Result = Downloader(self.__SystemObjects, WebRequestorObject).temp_image(NAME, Link, referer = SITE)
					
					if Result.code in Config.good_statusses:
						break

					elif Server != Servers[-1]:
						sleep(self.__Settings.common.delay)

		return Result.value

	def parse(self, slug: str, message: str | None = None):
		"""
		Получает основные данные тайтла.
			slug – алиас тайтла, использующийся для идентификации оного в адресе;\n
			message – сообщение для портов CLI.
		"""

		message = message or ""
		self.__Title = BaseStructs().manga
		self.__Slug = slug
		PrintParsingStatus(message)
		Data = self.__GetTitleData()
		self.__Title["site"] = SITE.replace("test-front.", "")
		self.__Title["id"] = Data["id"]
		self.__Title["slug"] = slug
		self.__Title["content_language"] = "rus"
		self.__Title["localized_name"] = Data["rus_name"]
		self.__Title["en_name"] = Data["eng_name"]
		self.__Title["another_names"] = Data["otherNames"]
		self.__Title["covers"] = self.__GetCovers(Data)
		self.__Title["authors"] = self.__GetAuthors(Data)
		self.__Title["publication_year"] = int(Data["releaseDate"]) if Data["releaseDate"] else None
		self.__Title["description"] = self.__GetDescription(Data)
		self.__Title["age_limit"] = self.__GetAgeLimit(Data)
		self.__Title["type"] = self.__GetType(Data)
		self.__Title["status"] = self.__GetStatus(Data)
		self.__Title["is_licensed"] = Data["is_licensed"]
		self.__Title["genres"] = self.__GetGenres(Data)
		self.__Title["tags"] = self.__GetTags(Data)
		self.__Title["franchises"] = self.__GetFranchises(Data)
		self.__Title["content"] = self.__GetContent()
		if Data["name"] not in self.__Title["another_names"] and Data["name"] != self.__Title["another_names"] and Data["name"] != self.__Title["another_names"]: self.__Title["another_names"].append(Data["name"])

	def repair(self, content: dict, chapter_id: int) -> dict:
		"""
		Заново получает данные слайдов главы главы.
			content – содержимое тайтла;\n
			chapter_id – идентификатор главы.
		"""

		for BranchID in content.keys():
			
			for ChapterIndex in range(len(content[BranchID])):
				
				if content[BranchID][ChapterIndex]["id"] == chapter_id:
					Slides = self.__GetSlides(
						content[BranchID][ChapterIndex]["number"],
						content[BranchID][ChapterIndex]["volume"],
						BranchID
					)
					self.__SystemObjects.logger.chapter_repaired(self.__Slug, self.__Title["id"], chapter_id, content[BranchID][ChapterIndex]["is_paid"])
					content[BranchID][ChapterIndex]["slides"] = Slides

		return content
	
	def collect(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> list[str]:
		"""
		Собирает список тайтлов по заданным параметрам.
			period – количество часов до текущего момента, составляющее период получения данных;\n
			filters – строка из URI каталога, описывающая параметры запроса;\n
			pages – количество запрашиваемых страниц.
		"""

		if filters: self.__SystemObjects.logger.collect_filters_ignored()
		if pages: self.__SystemObjects.logger.collect_pages_ignored()

		Updates = list()
		IsUpdatePeriodOut = False
		Page = 1
		UpdatesCount = 0
		Headers = {
			"Site-Id": str(self.__GetSiteID())
		}
		CurrentDate = datetime.utcnow()

		while not IsUpdatePeriodOut:
			Response = self.__Requestor.get(f"https://api.lib.social/api/latest-updates?page={Page}", headers = Headers)
			
			if Response.status_code == 200:
				UpdatesPage = Response.json["data"]

				for UpdateNote in UpdatesPage:
					Delta = CurrentDate - self.__StringToDate(UpdateNote["last_item_at"])
					
					if Delta.total_seconds() / 3600 <= period:
						Updates.append(UpdateNote["slug"])
						UpdatesCount += 1

					else:
						IsUpdatePeriodOut = True

			else:
				IsUpdatePeriodOut = True
				self.__SystemObjects.logger.request_error(Response, f"Unable to request updates page {Page}.")

			if not IsUpdatePeriodOut:
				Page += 1
				sleep(self.__Settings.common.delay)

		self.__SystemObjects.logger.updates_collected(len(Updates))

		return Updates