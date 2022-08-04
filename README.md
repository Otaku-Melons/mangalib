# MangaLib Parser
**MangaLib Parser** – это кроссплатформенный скрипт для получения данных с одноимённого сайта в формате JSON. Он позволяет записать всю информацию о конкретной манге, а также её главах и содержании глав.
## Порядок установки
1. Установить Python версии не старше 3.9.7.
2. Скачать [Google Chrome](https://www.google.by/intl/ru/chrome/) и установить в директорию по умолчанию.
3. В среду исполнения установить следующие пакеты: Selenium, BeautifulSoup4.
```
pip install selenium
pip install beautifulsoup4
```
4. Убедиться в наличии в папке со скриптом драйвера **chromedriver**. При необходимости загрузить [тут](https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/).
5. Настроить скрипт путём редактирования *Settings.json*.
6. Запустить *MangaLib_Parser.py*.
7. Данные сохраняются в файлы формата JSON. Директория зависит от настроек скрипта.
## Settings.json
Задаёт директорию с исполняемым файлом Chrome.
```
"chrome-binary" : ""
```
Устанавливает директорию для сохраенния данных.
```
"data-path" : "manga/"
```
Переключает скрипт между режимами: парсинг всего сайта / конкретной манги / списка манги. 
```
"parcer-target" : ""
"parcer-target" : "martial-peak"
"parcer-target" : [ "martial-peak", "a-house-of-time", "syakeu" ]
```
Включает режим обновления существующего файла JSON путём добавления туда новых данных.
```
"only-update" : true
```
*Evolv Group. Copyright © 2018-2022.*
