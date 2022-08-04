import re

#Перечисление областей тегов HTML.
TagsHTML = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

#Удаляет теги HTML из строки.
def RemoveHTML(TextHTML):
  CleanText = re.sub(TagsHTML, '', str(TextHTML))
  return str(CleanText)

#Удаляет из строки символы: новой строки, табуляции, пробелы из начала и конца.
def RemoveSpaceSymbols(Text):
    Text = Text.replace('\n', '')
    Text = Text.replace('\t', '')
    Text = ' '.join(Text.split())
    return Text.strip()

#Заменяет символ новой строки на запятую с пробелом.
def ReplaceEndlToComma(Text):
    Text = Text.strip()
    Text = Text.replace('\n', ', ')
    return Text






















#Получает строку с количеством загруженных глав.
def GetChaptersCount(Soup):
    Divs = Soup.find_all('div', {'class': 'media-info-list__value text-capitalize'})
    ChaptersCount = RemoveHTML(Divs[1])
    return ChaptersCount

#Получает список названий отображаемых глав.
def GetCurrentChapters(Soup):
    BodyHTML = Browser.execute_script("return document.body.innerHTML;")
    Soup = BeautifulSoup(BodyHTML, "html.parser")
    ChaptersLinks = Soup.find_all('div', {'class': 'media-chapter__name text-truncate'})
    return ChaptersLinks

#Удаляет одинаковые строки в списке.
def RemoveSameStrings(Array):

    return 0

#Плавная прокрутка и получение списка глав.
def SmoothScrollAndGetChapters(ChaptersCount, Soup):
    CurrentChapter = 0
    CodeJS = "window.scrollTo(0, "
    CurrentChapters = GetCurrentChapters(Soup)
    while CurrentChapter < ChaptersCount * 40 + 100:
        #Сон для подгрузки глав во время остановки скролла.
        if CurrentChapter % 1000 == 0:
            sleep(2);
            NewChapters = GetCurrentChapters(Soup)
            for InObj in NewChapters:
                print(InObj)
            CurrentChapters.extend(NewChapters)
        CurrentChapter += 5
        FullCodeJS = CodeJS + str(CurrentChapter) + ");"
        Browser.execute_script(FullCodeJS)
        PreResult = []
        Result = []
        #Приведение к строкам.
        for InObj in CurrentChapters:
            PreResult.append(str(InObj))
        #Удаление повторов.
        for InObj in PreResult:
            if InObj not in Result:
                Result.append(InObj)
    return Result