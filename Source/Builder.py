from dublib.Methods import Cls, MakeRootDirectories, ReadJSON, RemoveFolderContent
from dublib.WebRequestor import WebRequestor
from time import sleep

import logging
import shutil
import os

#==========================================================================================#
# >>>>> ИСКЛЮЧЕНИЯ <<<<< #
#==========================================================================================#

# Исключение: не найдена цель для сборки.
class BuildTargetNotFound(Exception):

	# Конструктор.
	def __init__(self, Type: str, Value: str):
		# Добавление данных в сообщение об ошибке.
		self.__Message = f"Target \"{Type}\" with value \"{Value}\" not found."
		# Обеспечение доступа к оригиналу наследованного свойства.
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message
	
# Исключение: неподдерживаемый формат.
class UnsupportedFormat(Exception):

	# Конструктор.
	def __init__(self):
		# Добавление данных в сообщение об ошибке.
		self.__Message = f"File format unsupported. Convert it to DMP-V1 or RN-V2."
		# Обеспечение доступа к оригиналу наследованного свойства.
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message

#==========================================================================================#
# >>>>> ОБРАБОТКА КОММАНД <<<<< #
#==========================================================================================#

# Загрузчик контента.
class Builder:
	
	# Возвращает главу с ID.
	def __GetChapterByID(self, ChapterID: int) -> dict:
		
		# Для каждой ветви.
		for BranchID in self.__Title["chapters"].keys():
			
			# Для каждой главы.
			for Chapter in self.__Title["chapters"][BranchID]:
				
				# Если глава найдена, вернуть главу.
				if Chapter["id"] == ChapterID: return Chapter
				
		# Если глава не найдена, выбросить исключение.
		raise BuildTargetNotFound("chapter", ChapterID)
	
	# Возвращает список глав в томе.
	def __GetVolumeChapters(self, BranchID: str, Volume: str) -> list[dict]:
		# Список глав.
		Chapters = list()
		
		# Для каждой главы в ветви.
		for Chapter in self.__Title["chapters"][BranchID]:
			
			# Если глава принадлежит указанному тому.
			if str(Chapter["volume"]) == Volume: Chapters.append(Chapter)
			
		# Если том не найден, выбросить исключение.
		if len(Chapters) > 0: raise BuildTargetNotFound("volume", Volume)
			
		return Chapters
	
	# Возвращает список томов.
	def __GetVolumesList(self, BranchID: str) -> list[int]:
		# Список томов.
		Volumes = list()
		
		# Для каждой главы.
		for Chapter in self.__Title["chapters"][BranchID]:
			
			# Если том не записан, записать.
			if Chapter["volume"] not in Volumes: Volumes.append(Chapter["volume"])
			
		return Volumes
	
	# Загружает слайд.
	def __DownloadSlide(self, URL: str, Directory: str = "Temp/Slides", Filename: str | None = None) -> bool:
		# Очистка краевой черты.
		Directory = Directory.rstrip("/")
		# Заголовки запроса.
		Headers = {
			"Referer": "https://remanga.org/"	
		}
		# Запрос слайда.
		Response = self.__Requestor.get(URL, headers = Headers)
		# Состояние: успешна ли загрузка.
		IsSuccess = False
		# Если не указано имя файла, взять из URL.
		if Filename == None: Filename = URL.split("/")[-1].split(".")[0]
		# Расширение файла.
		Type = URL.split(".")[-1]
		
		# Если запрос успешен.
		if Response.status_code == 200:
			# Переключение статуса.
			IsSuccess = True

			# Если включена фильтрация маленьких слайдов и слайд более 5 KB или фильтрация отключена.
			if self.__EnableFilter == True and len(Response.content) / 1024 > 5 or self.__EnableFilter == False:
					
				# Открытие потока записи.
				with open(f"{Directory}/{Filename}.{Type}", "wb") as FileWriter:
					# Запись файла изображения.
					FileWriter.write(Response.content)
					
			else:
				# Запись в лог: слайд отфильтрован по размеру.
				logging.info("Slide: \"" + URL + "\". Less than 5 KB. Skipped.")
			
			# Запись в лог: слайд загружен.
			logging.info("Slide: \"" + URL + "\". Downloaded.")
		
		else:
			# Запись в лог ошибки: не удалось загрузить слайд.
			logging.error("Unable to download slide: \"" + URL + "\". Response code: " + str(Response.status_code) + ".")
	
		return IsSuccess

	# Конструктор.
	def __init__(self, Settings: dict, Title: str, Message: str = ""):
		# Если файл указан без расширения, добавить расширение.
		if Title.endswith(".json") == False: Title = Title + ".json"
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Запросчик.
		self.__Requestor = WebRequestor()
		# Данные тайтла.
		self.__Title = ReadJSON(self.__Settings["titles-directory"] + Title)
		# Заголовок.
		self.__Header = Message + "Title: " + self.__Title["slug"] + "\n"
		# Алиас тайтла.
		self.__Slug = self.__Title["slug"]
		# Выходной формат.
		self.__Format = "zip"
		# Состояние: фильтровать ли маленькие слайды.
		self.__EnableFilter = True
		# Состояние: использовать ли интервал.
		self.__UseDelay = True
	
		# Создание папок в корневой директории.
		MakeRootDirectories(["Output", "Temp"])
		# Инициализация запросчика.
		self.__Requestor.initialize()
		# Если формат не поддерживается, выбросить исключение.
		if "format" not in self.__Title.keys() or self.__Title["format"].lower() not in ["dmp-v1", "rn-v1"]: raise UnsupportedFormat()
		
	# Загружает главу.
	def buildChapter(self, ChapterID: int, Output: str | None = None, Message: str = "") -> bool:
		# Состояние: успешна ли загрузка.
		IsSuccess = True
		# Получение данных главы.
		Chapter = self.__GetChapterByID(ChapterID)
		# Очистка папки временных файлов.
		RemoveFolderContent("Temp")
		# Создание папок в корневой директории.
		MakeRootDirectories(["Temp/Slides"])
		# Название главы.
		ChapterName = str(Chapter["number"])
		# Если у главы есть название, добавить его.
		if Chapter["name"] != None: ChapterName += ". " + Chapter["name"].rstrip(".?")
		
		# Если не указан выходной каталог.
		if Output == None:
			# Использовать в качестве каталога алиас.
			Output = f"Output/{self.__Slug}"	
			# Если не создана, создать выходную директорию.
			if os.path.exists(f"Output/{self.__Slug}") == False: os.makedirs(f"Output/{self.__Slug}")

		else:
			# Удаление конечной косой черты.
			Output = Output.rstrip("/")
		
		# Для каждого слайда.
		for SlideIndex in range(0, len(Chapter["slides"])):
			# Очистка консоли.
			Cls()
			# Вывод в консоль: прогресс загрузки слайдов.
			print(self.__Header + Message + "Slide: " + str(SlideIndex + 1) + " / " + str(len(Chapter["slides"])))
			# Загрузка слайда.
			Result = self.__DownloadSlide(Chapter["slides"][SlideIndex]["link"], Filename = str(SlideIndex + 1))
			
			# Если не удалось загрузить слайд.
			if Result == False: 
				# Переключение статуса.
				IsSuccess = False
				# Запись в лог ошибки: не удалось загрузить главу.
				logging.error(f"Unable to create chapter {ChapterID}.")
				# Остановка цикла.
				break
			
			# Если используется интервал и слайд не последний, выждать интервал.
			if self.__UseDelay == True and SlideIndex + 1 != len(Chapter["slides"]): sleep(self.__Settings["delay"])
			
		# Если загрузка успешна.
		if IsSuccess == True:
			# Создание архива.
			shutil.make_archive(f"Temp/{ChapterName}", "zip", "Temp/Slides")
			# Если указан нестандартный формат, переименоватьт архив.
			if self.__Format != "zip": os.rename(f"Temp/{ChapterName}.zip", f"Temp/{ChapterName}.{self.__Format}")
			# Если указан выходной каталог, переместить файл.
			if Output != None: os.replace(f"Temp/{ChapterName}.{self.__Format}", f"{Output}/{ChapterName}.{self.__Format}")
			# Запись в лог сообщения: глава загружена.
			logging.info(f"Chapter {ChapterID}. Build complete.")
		
		return IsSuccess
	
	# Загружает том.
	def buildVolume(self, BranchID: str | None, Volume: str, Message: str = "") -> int:
		# Если не указан ID ветви, использовать ветвь с наибольшим количеством глав.
		if BranchID == None: BranchID = str(max(self.__Title["branches"], key = lambda Branch: Branch["chapters-count"])["id"])
		# Количество ошибок.
		ErrorsCount = 0
		# Получение списка глав.
		Chapters = self.__GetVolumeChapters(BranchID, Volume)
		
		# Для каждой главы.
		for ChapterIndex in range(0, len(Chapters)):
			# Обновление сообщения.
			MessageText = Message + "Chapter: " + str(ChapterIndex + 1) + " / " + str(len(Chapters)) + "\n"
			# Если не создана, создать выходную директорию.
			if os.path.exists(f"Output/{self.__Slug}/Том " + Volume) == False: os.makedirs(f"Output/{self.__Slug}/Том " + Volume)
			# Загрузка главы.
			Result = self.buildChapter(Chapters[ChapterIndex]["id"], Output = f"Output/{self.__Slug}/Том " + Volume, Message = MessageText)
			# Если не удалось загрузить главу, выполнить инкремент ошибок.
			if Result == False: ErrorsCount += 1
			
		# Сообщение об ошибках.
		ErrorsMessage = "" if ErrorsCount == 0 else f" Errors: {ErrorsCount}."
		# Запись в лог сообщения: том построен.
		logging.info(f"Volume {Volume}. Build complete.{ErrorsMessage}")

		return ErrorsCount
	
	# Загружает ветку.
	def buildBranch(self, BranchID: str | None = None) -> int:
		# Если не указан ID ветви, использовать ветвь с наибольшим количеством глав.
		if BranchID == None: BranchID = str(max(self.__Title["branches"], key = lambda Branch: Branch["chapters-count"])["id"])
		# Количество ошибок.
		ErrorsCount = 0
		# Если ветвь не найдена, выбросить исключение.
		if BranchID not in self.__Title["chapters"].keys(): raise BuildTargetNotFound("branch", BranchID)
		
		# Для каждого тома.
		for Volume in self.__GetVolumesList(BranchID):
			# Обновление сообщения.
			MessageText = "Volume: " + str(Volume) + "\n"
			# Загрузка тома.
			Result = self.buildVolume(BranchID, str(Volume), MessageText)
			# Инкремент количества ошибок.
			ErrorsCount += Result
			
		# Сообщение об ошибках.
		ErrorsMessage = "" if ErrorsCount == 0 else f" Errors: {ErrorsCount}."
		# Запись в лог сообщения: том построен.
		logging.info(f"Branch {BranchID}. Build complete.{ErrorsMessage}")

		return ErrorsCount
	
	# Задаёт статус использования интервала.
	def setDelayStatus(self, Status: bool):
		self.__UseDelay = Status
	
	# Задаёт выходной формат.
	def setOutputFormat(self, Format: str | None):
		self.__Format = Format
		
	# Задаёт статус фильтрации.
	def setFilterStatus(self, Status: bool):
		self.__EnableFilter = Status