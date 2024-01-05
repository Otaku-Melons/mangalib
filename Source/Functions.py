from dublib.WebRequestor import WebRequestor
from bs4 import BeautifulSoup

import datetime
import logging

# Выполняет авторизацию.
def Authorizate(Settings: dict, Requestor: WebRequestor, Domain: str):
	
	# Если указаны логин и пароль.
	if type(Settings["login"]) == str and len(Settings["login"]) > 0 and type(Settings["password"]) == str and len(Settings["password"]) > 0:
		
		try:
			# Запрос страницы авторизации.
			Response = Requestor.get(f"https://{Domain}/")
			# Запрос страницы авторизации.
			Response = Requestor.get(f"https://lib.social/login?from=https%3A%2F%2F{Domain}%2F")
			# Получение токена страницы.
			Token = BeautifulSoup(Response.text, "html.parser").find("meta", {"name": "_token"})["content"]
			# Данные авторизации.
			Data = f"_token={Token}&email=" + Settings["login"] + "&password=" + Settings["password"] + f"&remember=on&from=https%3A%2F%2F{Domain}%2F"
			# Заголовки запроса.
			Headers = {
				"Origin": "https://lib.social",
				"Referer": "https://lib.social/login",
				"Content-Type": "application/x-www-form-urlencoded"
			}
			# Запрос авторизации.
			Response = Requestor.post(f"https://lib.social/login?from=https%3A%2F%2F{Domain}%2F", Data = Data, Headers = Headers, TriesCount = 1)
			
		except Exception as ExceptionData:
			# Запись в лог ошибки: не удалось выполнить авторизацию.
			logging.error("Unable to authorizate. Description: \"" + str(ExceptionData).rstrip(".") + "\".")

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