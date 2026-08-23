# OrdPaint

**OrdPaint** — настольный растровый графический редактор на Python 3 и PySide6/Qt 6.

Проект строится как полноценное desktop-приложение: отдельное core-ядро, Qt-интерфейс, многослойный документ, собственный формат проектов, Undo/Redo, растровые инструменты и автоматические проверки качества.

## Возможности

### Рисование
- кисть и ластик;
- линия, прямоугольник и эллипс;
- заливка с tolerance;
- пипетка;
- размер и непрозрачность инструмента;
- прозрачный холст с checkerboard-фоном;
- zoom и pan.

### Слои
- создание и удаление;
- дублирование;
- изменение порядка;
- переименование;
- visibility и lock;
- opacity;
- blend modes;
- merge down и merge visible.

### Выделение и буфер
- прямоугольное выделение;
- replace/add/subtract/intersect;
- Select All / Deselect;
- copy/cut/paste;
- вставка содержимого отдельным слоем;
- ограничение растровых операций областью выделения.

### Проекты
- собственный формат `.ordpaint`;
- versioned project schema;
- безопасное атомарное сохранение;
- проверка структуры и размеров при загрузке;
- импорт PNG/JPEG/WebP/BMP;
- экспорт PNG/JPEG/WebP/BMP;
- dirty-state и Undo/Redo.

## Архитектура

```text
ordpaint/
├── core/
│   ├── document.py    # документ, слои и композиция
│   ├── layer.py       # модель слоя
│   ├── history.py     # Undo/Redo и транзакции
│   ├── raster.py      # растровые операции
│   ├── selection.py   # модель выделения
│   ├── clipboard.py   # данные буфера обмена
│   ├── project.py     # .ordpaint и импорт/экспорт
│   ├── settings.py    # настройки приложения
│   └── tools.py       # единая модель инструментов
└── ui/
    ├── canvas.py      # viewport, input и rendering
    └── main_window.py # меню, docks и application UI
```

Главный принцип — не смешивать Qt-взаимодействие с растровой бизнес-логикой. `core` отвечает за состояние и операции документа, `ui` — за взаимодействие пользователя и визуализацию.

## Установка

Требуется Python 3.12+.

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Проверка качества

```bash
ruff check .
ruff format --check .
pytest -q
```

CI выполняет эти проверки автоматически на push и pull request.

## Горячие клавиши

| Клавиша | Действие |
|---|---|
| `B` | Кисть |
| `E` | Ластик |
| `L` | Линия |
| `R` | Прямоугольник |
| `O` | Эллипс |
| `G` | Заливка |
| `I` | Пипетка |
| `M` | Выделение |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+C` | Copy |
| `Ctrl+X` | Cut |
| `Ctrl+V` | Paste |
| `Ctrl+S` | Save |
| `Ctrl+O` | Open |
| `Ctrl+N` | New |
| `Ctrl+колесо` | Zoom |
| `Space + ЛКМ` | Pan |
| `Средняя кнопка` | Pan |

## Статус

OrdPaint находится в активной разработке. Core уже покрывает базовую архитектуру редактора; дальнейшая работа сосредоточена на полноценном selection/transform workflow, polished UI/UX, производительности больших документов, расширении тестов и финальной стабилизации.

## Лицензия

MIT — см. `LICENSE`.
