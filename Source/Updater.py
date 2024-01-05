from dublib.WebRequestor import WebRequestor
from Source.Functions import TimeToDatetime
from dublib.Methods import Cls
from bs4 import BeautifulSoup
from time import sleep

import datetime
import logging
import json

# Словарь ID сайтов.
SITES_ID = {
	"mangalib.me": "1",	
	"hentailib.me": "4",	
	"yaoilib.me": "2",	
}

# Модуль получения обновлений.
class Updater:
    
    # Конструктор.
	def __init__(self,  Settings: dict, Requestor: WebRequestor, Domain: str):

		#---> Генерация динамичкских свойств.
		#==========================================================================================#
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Обработчик навигации.
		self.__Requestor = Requestor
		# Домен.
		self.__Domain = Domain
		
	# Возвращает список алиасов обновлённых тайтлов.
	def getUpdatesList(self) -> list:
		# Список алиасов обновлённых тайтлов.
		Updates = list()
		# Счётчик страницы.
		Page = 0
		# Состояние: достигнут ли конец проверяемого диапазона.
		IsTimeElapse = False
		# Счётчик обновлённых тайтлов.
		UpdatesCounter = 0
		# Загрузка страницы каталога.
		Response = self.__Requestor.get(f"https://{self.__Domain}/manga-list")
		# Получение токена страницы.
		Token = BeautifulSoup(Response.text, "html.parser").find("meta", {"name": "_token"})["content"]
		# Текущее время.
		Now = datetime.datetime.now()
		
		# Проверка обновлений за указанный промежуток времени.
		while IsTimeElapse == False:
			# Инкремент страницы.
			Page += 1
			# JSON запроса списка.
			RequestJSON = {
				"sort": "last_chapter_at",
				"dir": "desc",
				"page": Page,
				"site_id": SITES_ID[self.__Domain],
				"type": "manga",
				"caution_list": ["Отсутствует", "16+", "18+"]
			}
			# Заголовки запроса.
			RequestHeaders = {"X-Csrf-Token": Token}
			# Выполнение запроса.
			Response = self.__Requestor.post(f"https://{self.__Domain}/api/list", JSON = RequestJSON, Headers = RequestHeaders)
			
			# Проверка успешности запроса.
			if Response.status_code == 200:
				# Конвертирование данных в словарь.
				Data = json.loads(Response.text)
				
				# Проход по всем записям об обновлениях.
				for UpdateNote in Data["items"]["data"]:
					# Разница двух временных точек.
					Delta = Now - TimeToDatetime(UpdateNote["updated_at"])
					
					# Если разница меньше указанной настройками.
					if Delta.seconds <= self.__Settings["check-updates-period"] * 3600:
						# Сохранение алиаса обновлённого тайтла.
						Updates.append(UpdateNote["slug"])
						# Инкремент счётчика.
						UpdatesCounter += 1

					else:
						# Завершение цикла обновления.
						IsTimeElapse = True
						
					# Очистка консоли.
					Cls()
					# Вывод в консоль: прогресс.
					print(f"On {Page} pages updates notes found: {UpdatesCounter}.")

			else:
				# Завершение цикла обновления.
				IsTimeElapse = True
				# Запись в лог ошибки: не удалось запросить обновления.
				logging.error("Unable to fetch titles updates.")
				
			# Проверка: завершён ли цикл.
			if IsTimeElapse == False:
				# Выжидание указанного интервала.
				sleep(self.__Settings["delay"])

			elif Response.status_code == 200:
				# Запись в лог сообщения: количество полученных обновлений.
				logging.info("On " + str(Page) + " pages updates notes found: " + str(UpdatesCounter) + ".")

		return Updates