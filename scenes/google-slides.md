# Google Slides как сцена из Google Sheets

В столбце B указывается ссылка на конкретный слайд Google Slides:
`https://docs.google.com/presentation/d/PRESENTATION_ID/edit#slide=id.PAGE_ID`.
Ссылки без выбранного слайда отклоняются: первый слайд не выбирается наугад.
Текущая схема: A текст, B сцена, C указка, D интерактив, E размещение кода,
F голос, G аудио, H видео.

Для статичного слайда C и D должны быть `нет`. После синтеза с `--audio-column G`:

```powershell
C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe -X utf8 scripts/render_sheet_static.py C:/Users/a1ole/OneDrive/coldKode-presenter/output/SCENE
C:/GitHub/google-sheets-mcp/.venv/Scripts/python.exe -X utf8 scripts/publish_static_sheet_scene.py C:/Users/a1ole/OneDrive/coldKode-presenter/output/SCENE --row 23
```

Экспорт использует существующие учётные данные Google-коннектора и
[Slides pages.getThumbnail](https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations.pages/getThumbnail)
с размером LARGE (1600 пикселей по ширине). Для закрытой презентации нужны
доступ сервисного аккаунта к документу и включённый Google Slides API.
Ключи не копируются в Presenter.

Если Slides API отключён, допускается публичный PNG-экспорт выбранного слайда.
Права доступа не меняются. В проверенном документе этот путь дал 960×540:
изображение масштабируется с сохранением пропорций, а не выдаётся за нативное 1600×900.

Локально сохраняются PNG, идентификаторы презентации и страницы, размер, SHA-256
и способ экспорта. Временные подписанные URL не сохраняются. Исходная ссылка
в таблице остаётся прежней; публикация отклоняется, если инструкция строки изменилась.
Экспорт статичный: анимация слайда и переходы презентации не переносятся.
