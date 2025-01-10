# mangalib
**mangalib** – это модуль системы управления парсерами [Melon](https://github.com/Otaku-Melons/Melon), включающий поддержку источников: [MangaLib](https://test-front.mangalib.me/), [HentaiLib](https://hentailib.me/), [SlashLib](https://slashlib.me/).

# Дополнительные настройки
Данный раздел описывает специфичные для этого парсера настройки.
___
```JSON
"token": ""
```
Токен аккаунта [SocialLib](https://lib.social/) для доступа к контенту с ограниченным доступом.
___
```JSON
"server": "main"
```
Идентификатор сервера хранения изображений. 

Принимаемые значения: _main_, _secondary_, _compress_, _download_, _crop_.
___
```JSON
"add_moderation_status": false
```
Указывает, необходимо ли добавлять статус модерации главы в данные о ней.