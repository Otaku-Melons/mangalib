from Source.Core.Formats.Manga import Branch, Chapter, Manga, Statuses, Types
from Source.Core.ImagesDownloader import ImagesDownloader
from Source.Core.Base.MangaParser import MangaParser
from Source.Core.Exceptions import TitleNotFound

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
TYPE = Manga

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Parser(MangaParser):
	"""Парсер."""

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _InitializeRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов."""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.generate_user_agent("pc")
		Config.set_retries_count(self._Settings.common.retries)
		Config.add_header("Authorization", self._Settings.custom["token"])
		WebRequestorObject = WebRequestor(Config)
		
		if self._Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTP,
			host = self._Settings.proxy.host,
			port = self._Settings.proxy.port,
			login = self._Settings.proxy.login,
			password = self._Settings.proxy.password
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

	def __GetBranches(self) -> list[Branch]:
		"""Получает содержимое тайтла."""

		Branches = dict()
		Response = self._Requestor.get(f"https://api.lib.social/api/manga/{self._Title.slug}/chapters")
		
		if Response.status_code == 200:
			Data = Response.json["data"]
			sleep(self._Settings.common.delay)

			for CurrentChapterData in Data:

				for BranchData in CurrentChapterData["branches"]:
					BranchID = BranchData["branch_id"]
					if BranchID == None: BranchID = int(str(self._Title.id) + "0")
					if BranchID not in Branches.keys(): Branches[BranchID] = Branch(BranchID)

					Translators = [sub["name"] for sub in BranchData["teams"]]
					Buffer = {
						"id": BranchData["id"],
						"volume": CurrentChapterData["volume"],
						"number": CurrentChapterData["number"],
						"name": Zerotify(CurrentChapterData["name"]),
						"is_paid": False,
						"translators": Translators,
						"slides": []	
					}

					ChapterObject = Chapter(self._SystemObjects)
					ChapterObject.set_dict(Buffer)
					Branches[BranchID].add_chapter(ChapterObject)

		else: self._SystemObjects.logger.request_error(Response, "Unable to request chapter.")

		for CurrentBranch in Branches.values(): self._Title.add_branch(CurrentBranch)

	def __GetCovers(self, data: dict) -> list[str]:
		"""Получает список обложек."""

		Covers = list()

		if data["cover"]:
			Covers.append({
				"link": data["cover"]["default"],
				"filename": data["cover"]["default"].split("/")[-1]
			})

		if self._Settings.common.sizing_images:
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
			"Authorization": self._Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		Response = self._Requestor.get(URL, headers = Headers)

		if Response.status_code == 200:
			Data = Response.json["data"]["imageServers"]
			sleep(self._Settings.common.delay)

			for ServerData in Data:

				if server_id:
					if ServerData["id"] == server_id and CurrentSiteID in ServerData["site_ids"]: Servers.append(ServerData["url"])
					elif ServerData["id"] == server_id and all_sites: Servers.append(ServerData["url"])

				else:
					if CurrentSiteID in ServerData["site_ids"] or all_sites: Servers.append(ServerData["url"])

		else:
			self._SystemObjects.logger.request_error(Response, "Unable to request site constants.")

		return Servers

	def __GetSiteID(self) -> int:
		"""Возвращает целочисленный идентификатор сайта."""

		SiteID = None
		if "mangalib" in SITE: SiteID = 1
		if "yaoilib" in SITE or "slashlib" in SITE: SiteID = 2
		if "hentailib" in SITE: SiteID = 4
		
		return SiteID

	def __GetSlides(self, branch_id: int, chapter: Chapter) -> list[dict]:
		"""
		Получает данные о слайдах главы.
			branch_id – идентификатор ветви;\n
			chapter – данные главы.
		"""

		Slides = list()
		Server = self.__GetImagesServers(self._Settings.custom["server"])[0]
		Branch = "" if branch_id == str(self._Title.id) + "0" else f"&branch_id={branch_id}"
		URL = f"https://api.lib.social/api/manga/{self._Title.slug}/chapter?number={chapter.number}&volume={chapter.volume}{Branch}"
		Headers = {
			"Authorization": self._Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		Response = self._Requestor.get(URL, headers = Headers)
		
		if Response.status_code == 200:
			Data = Response.json["data"]["pages"]
			sleep(self._Settings.common.delay)

			for SlideIndex in range(len(Data)):
				Buffer = {
					"index": SlideIndex + 1,
					"link": Server + Data[SlideIndex]["url"].replace(" ", "%20"),
					"width": Data[SlideIndex]["width"],
					"height": Data[SlideIndex]["height"]
				}
				Slides.append(Buffer)

		else: self._SystemObjects.logger.request_error(Response, "Unable to request chapter content.")

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

		URL = f"https://api.lib.social/api/manga/{self._Title.slug}?fields[]=eng_name&fields[]=otherNames&fields[]=summary&fields[]=releaseDate&fields[]=type_id&fields[]=caution&fields[]=genres&fields[]=tags&fields[]=franchise&fields[]=authors&fields[]=manga_status_id&fields[]=status_id"
		Headers = {
			"Authorization": self._Settings.custom["token"],
			"Referer": f"https://{SITE}/"
		}
		Response = self._Requestor.get(URL, headers = Headers)

		if Response.status_code == 200:
			Response = Response.json["data"]
			self._Title.set_id(Response["id"])
			self._SystemObjects.logger.parsing_start(self._Title)
			sleep(self._Settings.common.delay)

		else:
			self._SystemObjects.logger.request_error(Response, "Unable to request title data.")
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

	def amend(self, branch: Branch, chapter: Chapter):
		"""
		Дополняет главу дайными о слайдах.
			branch – данные ветви;\n
			chapter – данные главы.
		"""

		Slides = self.__GetSlides(branch.id, chapter)
		for Slide in Slides: chapter.add_slide(Slide["link"], Slide["width"], Slide["height"])

	def collect(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> list[str]:
		"""
		Собирает список тайтлов по заданным параметрам.
			period – количество часов до текущего момента, составляющее период получения данных;\n
			filters – строка из URI каталога, описывающая параметры запроса;\n
			pages – количество запрашиваемых страниц.
		"""

		if filters: self._SystemObjects.logger.collect_filters_ignored()
		if pages: self._SystemObjects.logger.collect_pages_ignored()

		Updates = list()
		IsUpdatePeriodOut = False
		Page = 1
		UpdatesCount = 0
		Headers = {
			"Site-Id": str(self.__GetSiteID())
		}
		CurrentDate = datetime.utcnow()

		while not IsUpdatePeriodOut:
			Response = self._Requestor.get(f"https://api.lib.social/api/latest-updates?page={Page}", headers = Headers)
			
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
				self._SystemObjects.logger.request_error(Response, f"Unable to request updates page {Page}.")

			if not IsUpdatePeriodOut:
				Page += 1
				sleep(self._Settings.common.delay)

		self._SystemObjects.logger.titles_collected(len(Updates))

		return Updates

	def image(self, url: str) -> str | None:
		"""
		Скачивает изображение с сайта во временный каталог парсера и возвращает его название.
			url – ссылка на изображение.
		"""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.requests.enable_proxy_protocol_switching(True)
		Config.add_header("Referer", f"https://{SITE}/")
		WebRequestorObject = WebRequestor(Config)

		if self._Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTPS,
			host = self._Settings.proxy.host,
			port = self._Settings.proxy.port,
			login = self._Settings.proxy.login,
			password = self._Settings.proxy.password
		)

		Result = ImagesDownloader(self._SystemObjects, WebRequestorObject).temp_image(url)
		
		if not Result:
			Servers = self.__GetImagesServers(all_sites = True)

			if self.__IsSlideLink(url, Servers):
				OriginalServer, ImageURI = self.__ParseSlideLink(url, Servers)
				Servers.remove(OriginalServer)
				sleep(self._Settings.common.delay)

				for Server in Servers:
					Link = Server + ImageURI
					Result = ImagesDownloader(self._SystemObjects, WebRequestorObject).temp_image(Link)
					
					if Result: break
					elif Server != Servers[-1]: sleep(self._Settings.common.delay)

		return Result

	def parse(self):
		"""Получает основные данные тайтла."""

		Data = self.__GetTitleData()
			
		if Data:

			self._Title.set_site(SITE)
			self._Title.set_id(Data["id"])
			self._Title.set_slug(Data["slug"])
			self._Title.set_content_language("rus")
			self._Title.set_localized_name(Data["rus_name"])
			self._Title.set_eng_name(Data["eng_name"])
			self._Title.set_another_names(Data["otherNames"])
			if Data["name"] not in Data["otherNames"] and Data["name"] != Data["rus_name"] and Data["name"] != Data["eng_name"]: self._Title.add_another_name(Data["name"])
			self._Title.set_covers(self.__GetCovers(Data))
			self._Title.set_authors(self.__GetAuthors(Data))
			self._Title.set_publication_year(int(Data["releaseDate"]) if Data["releaseDate"] else None)
			self._Title.set_description(self.__GetDescription(Data))
			self._Title.set_age_limit(self.__GetAgeLimit(Data))
			self._Title.set_type(self.__GetType(Data))
			self._Title.set_status(self.__GetStatus(Data))
			self._Title.set_is_licensed(Data["is_licensed"])
			self._Title.set_genres(self.__GetGenres(Data))
			self._Title.set_tags(self.__GetTags(Data))
			self._Title.set_franchises(self.__GetFranchises(Data))

			self.__GetBranches()