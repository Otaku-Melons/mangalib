from dublib.WebRequestor import WebRequestor
from bs4 import BeautifulSoup
from time import sleep

import datetime
import logging

# Выполняет авторизацию.
def Authorizate(Settings: dict, Requestor: WebRequestor, Domain: str):
	
	# Если указаны логин и пароль.
	if type(Settings["login"]) == str and len(Settings["login"]) > 0 and type(Settings["password"]) == str and len(Settings["password"]) > 0:
		# Код первого запроса.
		ResponseCode = 0
		# Ответ.
		Response = None
		# Индекс повтора авторизации.
		AuthIndex = 0
		# Заголовки запроса.
		Headers = {
			"Referer": f"https://lib.social/login?from=https%3A%2F%2F{Domain}%2F",
			"Accept": "*/*",
			"Accept-Encoding": "gzip, deflate, br",
			"Connection": "keep-alive"
		}
		
		try:
			
			# Пока запрос не будет успешно выполнен.
			while ResponseCode != 200:
				# Запрос главной страницы.
				Response = Requestor.get(f"https://{Domain}/", headers = Headers)
				# Выжидание интервала.
				sleep(Settings["delay"])
				# Запрос страницы авторизации.
				Response = Requestor.get(f"https://lib.social/login?from=https%3A%2F%2F{Domain}%2F", headers = Headers)
				# Добавление заголовков.
				Headers["Content-Type"] = "application/x-www-form-urlencoded"
				Headers["Origin"] = "https://lib.social"
				
				# Если запрос успешен.
				if Response.status_code == 200:
					# Получение токена страницы.
					Token = BeautifulSoup(Response.text, "html.parser").find("meta", {"name": "_token"})["content"]
					# Данные авторизации.
					Data = f"_token={Token}&email=" + Settings["login"] + "&password=" + Settings["password"]
					# Запрос авторизации.
					Response = Requestor.post(f"https://lib.social/login", data = Data, headers = Headers)
					# Запись кода.
					ResponseCode = Response.status_code
					
				# Выжидание интервала.
				sleep(Settings["delay"])
				# Инкремент индекса попытки.
				AuthIndex += 1
				# Если индекс повтора превышает максимальное количество, выбросить исключение.
				if AuthIndex > 2: raise Exception("The maximum number of authorization attempts has been reached.")
			
		except Exception as ExceptionData:
			# Запись в лог критической ошибки: не удалось выполнить авторизацию.
			logging.critical("Unable to authorizate. Description: \"" + str(ExceptionData).rstrip(".") + "\".")
			# Завершение процесса.
			exit(1)
			
		# Запись в лог сообщения: авторизация успешна.
		logging.info("Successfully authorized.")
		
# Проевращает число секунд в строку-дескриптор времени по формату [<x> hours <y> minuts <z> seconds].
def SecondsToTimeString(Seconds: float) -> str:
	# Количество часов.
	Hours = int(Seconds / 3600.0)
	Seconds -= Hours * 3600
	# Количество минут.
	Minutes = int(Seconds / 60.0)
	Seconds -= Minutes * 60
	# Количество секунд.
	Seconds = ToFixedFloat(Seconds, 2)
	# Строка-дескриптор времени.
	TimeString = ""

	# Генерация строки.
	if Hours > 0:
		TimeString += str(Hours) + " hours "
	if Minutes > 0:
		TimeString += str(Minutes) + " minutes "
	if Seconds > 0:
		TimeString += str(Seconds) + " seconds"

	return TimeString

# Усекает число до определённого количества знаков после запятой.
def ToFixedFloat(FloatNumber: float, Digits: int = 0) -> float:
	return float(f"{FloatNumber:.{Digits}f}")

# Переобразует значение в int.
def ToInt(Value: int | None) -> int:
	# Приведение к int.
	Value = 0 if Value == None else int(Value)

	return Value

# Преобразует строку времени в объект datetime.
def TimeToDatetime(Time: str) -> datetime.datetime:
	# Парсинг строки в объект времени.
	Object = datetime.datetime(
		year = int(Time.split("-")[0]),
		month = int(Time.split("-")[1]),
		day = int(Time.split("-")[2].split("T")[0]),
		hour = int(Time.split("T")[-1].split(":")[0])
	)	
	
	return Object