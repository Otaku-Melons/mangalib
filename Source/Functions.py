from dublib.WebRequestor import WebRequestor
from bs4 import BeautifulSoup

import logging

# Выполняет авторизацию.
def Authorizate(Settings: dict, Requestor: WebRequestor):
	
	# Если указаны логин и пароль.
	if type(Settings["email"]) == str and len(Settings["email"]) > 0 and type(Settings["password"]) == str and len(Settings["password"]) > 0:
		
		try:
			# Запрос страницы авторизации.
			Response = Requestor.get("https://lib.social/login")
			# Получение токена страницы.
			Token = BeautifulSoup(Response.text, "html.parser").find("meta", {"name": "_token"})["content"]
			# Данные авторизации.
			Data = f"_token={Token}&email=" + Settings["email"] + "&password=" + Settings["password"] + "&remember=on"
			# Заголовки запроса.
			Headers = {
				"Origin": "https://lib.social",
				"Referer": "https://lib.social/login",
				"Content-Type": "application/x-www-form-urlencoded"
			}
			# Запрос авторизации.
			Response = Requestor.post("https://lib.social/login?from=https%3A%2F%2Fmangalib.me%2Fadabana%3Fsection%3Dinfo", Data = Data, Headers = Headers, TriesCount = 1)
			
		except Exception as ExceptionData:
			# Запись в лог ошибки: не удалось выполнить авторизацию.
			logging.error("Unable to authorizate. Description: \"" + str(ExceptionData).rstrip(".") + "\".")

# Усекает число до определённого количества знаков после запятой.
def ToFixedFloat(FloatNumber: float, Digits: int = 0) -> float:
	return float(f"{FloatNumber:.{Digits}f}")

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

# Переобразует значение в int.
def ToInt(Value: int | None) -> int:
	# Приведение к int.
	Value = 0 if Value == None else int(Value)

	return Value
