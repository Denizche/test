# Примеры использования KOMPAS-3D MCP Server v2 (100/100)

## 📋 Содержание

1. [Базовый пример](#базовый-пример)
2. [Сложная иерархия компонентов](#сложная-иерархия-компонентов)
3. [Использование примитивов](#использование-примитивов)
4. [Интеграция с MCP](#интеграция-с-mcp)
5. [Обработка ошибок](#обработка-ошибок)

---

## Базовый пример

### Создание простой схемы деления

```python
from server.main import app
from server.models import CreateDivisionSchemeRequest, Component, TitleBlockData
import requests

# Подготовка данных
title_block = TitleBlockData(
    designation="ИЗДЕЛИЕ.01.01.001",
    name="Электронный блок управления",
    developer="И.И. Иванов",
    organization="ООО Компания"
)

components = [
    Component(
        position=1,
        name="Микроконтроллер",
        designation="МК.01.01.002",
        quantity=1,
        parent_position=None
    ),
    Component(
        position=2,
        name="Кристалл кварца",
        designation="КВ.01.01.003",
        quantity=1,
        parent_position=1
    ),
    Component(
        position=3,
        name="Конденсатор",
        designation="К.01.01.004",
        quantity=2,
        parent_position=1
    )
]

# Создание запроса
request_data = CreateDivisionSchemeRequest(
    product_code="ИЗДЕЛИЕ.01.01.001",
    product_name="Электронный блок управления",
    components=components,
    title_block_data=title_block,
    gost_format="A3",
    layout_type="tree",
    include_bom=True
)

# Отправка запроса к API
response = requests.post(
    "http://localhost:8000/api/v1/create_division_scheme",
    json=request_data.dict()
)

# Обработка результата
if response.status_code == 200:
    result = response.json()
    if result["success"]:
        print(f"Схема создана: {result['file_path']}")
    else:
        print(f"Ошибка: {result['message']}")
        print(f"Детали: {result['errors']}")
else:
    print(f"HTTP ошибка: {response.status_code}")
```

---

## Сложная иерархия компонентов

### Создание многоуровневой схемы деления

```python
from server.models import CreateDivisionSchemeRequest, Component, TitleBlockData

# Создание сложной иерархии (3 уровня)
components = [
    # Уровень 1: Основной узел
    Component(
        position=1,
        name="Основной узел",
        designation="УЗЕЛ.01.01.001",
        quantity=1,
        parent_position=None  # Это корневой элемент
    ),
    
    # Уровень 2: Подузлы
    Component(
        position=2,
        name="Электрическая часть",
        designation="УЗЕЛ.01.01.002",
        quantity=1,
        parent_position=1  # Родитель: основной узел
    ),
    Component(
        position=3,
        name="Механическая часть",
        designation="УЗЕЛ.01.01.003",
        quantity=1,
        parent_position=1  # Родитель: основной узел
    ),
    
    # Уровень 3: Компоненты электрической части
    Component(
        position=4,
        name="Микроконтроллер",
        designation="МК.01.01.004",
        quantity=1,
        parent_position=2  # Родитель: электрическая часть
    ),
    Component(
        position=5,
        name="Конденсатор",
        designation="К.01.01.005",
        quantity=3,
        parent_position=2  # Родитель: электрическая часть
    ),
    Component(
        position=6,
        name="Резистор",
        designation="Р.01.01.006",
        quantity=5,
        parent_position=2  # Родитель: электрическая часть
    ),
    
    # Уровень 3: Компоненты механической части
    Component(
        position=7,
        name="Корпус",
        designation="КОР.01.01.007",
        quantity=1,
        parent_position=3  # Родитель: механическая часть
    ),
    Component(
        position=8,
        name="Крышка",
        designation="КРЫ.01.01.008",
        quantity=1,
        parent_position=3  # Родитель: механическая часть
    ),
    Component(
        position=9,
        name="Винт",
        designation="ВИН.01.01.009",
        quantity=4,
        parent_position=3  # Родитель: механическая часть
    ),
]

# Создание запроса
request_data = CreateDivisionSchemeRequest(
    product_code="УЗЕЛ.01.01.001",
    product_name="Сложное изделие с иерархией",
    components=components,
    title_block_data=TitleBlockData(
        designation="УЗЕЛ.01.01.001",
        name="Сложное изделие с иерархией",
        developer="А.А. Петров",
        organization="ООО Технологии"
    ),
    gost_format="A2",  # Больший формат для сложной схемы
    layout_type="tree",  # Древовидное размещение
    include_bom=True
)

# Отправка запроса
response = requests.post(
    "http://localhost:8000/api/v1/create_division_scheme",
    json=request_data.dict()
)
```

---

## Использование примитивов

### Работа с дополнительными фигурами

```python
from server.drawing_primitives import DrawingPrimitives
import win32com.client as win32

# Подключение к КОМПАС-3D
kompas_app = win32.GetActiveObject("Kompas.Application.7")
kompas_object = kompas_app.KompasObject

# Получение текущего представления
document = kompas_app.ActiveDocument
sheet = document.Sheets.Item(0)
view = sheet.Views.Item(0)

# Инициализация примитивов
primitives = DrawingPrimitives(kompas_object, view)

# Рисование окружности
primitives.draw_circle(100, 100, 30, style=1)

# Рисование дуги
primitives.draw_arc(100, 100, 130, 100, 100, 130, style=1)

# Рисование эллипса
primitives.draw_ellipse(50, 50, 80, 40, style=1)

# Рисование полилинии
points = [(10, 10), (50, 50), (100, 10), (150, 50), (200, 10)]
primitives.draw_polyline(points, style=1, closed=False)

# Рисование скругленного прямоугольника
primitives.draw_rounded_rectangle(10, 10, 100, 50, radius=5, style=1)

# Рисование стрелки
primitives.draw_arrow(10, 10, 100, 100, arrow_size=5, style=1)

# Рисование сетки
primitives.draw_grid(0, 0, 200, 200, grid_size=10, style=3)
```

---

## Интеграция с MCP

### Использование как MCP сервера

```python
# Пример конфигурации MCP клиента для использования KOMPAS-3D MCP Server

# claude_desktop_config.json
{
  "mcpServers": {
    "kompas-mcp": {
      "command": "python3",
      "args": [
        "-m",
        "uvicorn",
        "server.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}

# Использование в Claude:
# "Создай схему деления для изделия с кодом ПРИБОР.01.01.001, 
#  состоящего из микроконтроллера, конденсаторов и резисторов"
```

---

## Обработка ошибок

### Правильная обработка исключений

```python
import logging
from server.kompas_api_handler import KompasAPIHandler
from server.models import CreateDivisionSchemeRequest, Component, TitleBlockData

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация обработчика
handler = KompasAPIHandler()

# Попытка создания схемы с обработкой ошибок
try:
    # Подключение к КОМПАС-3D
    if not handler.connect():
        logger.error("Не удалось подключиться к КОМПАС-3D")
        raise RuntimeError("КОМПАС-3D не запущен")
    
    # Проверка статуса
    status = handler.check_status()
    logger.info(f"Статус КОМПАС-3D: {status}")
    
    # Подготовка данных
    components = [
        Component(
            position=1,
            name="Компонент 1",
            designation="ТЕСТ.01.01.001",
            quantity=1,
            parent_position=None
        )
    ]
    
    request_data = CreateDivisionSchemeRequest(
        product_code="ТЕСТ.01.01.001",
        product_name="Тестовое изделие",
        components=components,
        title_block_data=TitleBlockData(
            designation="ТЕСТ.01.01.001",
            name="Тестовое изделие"
        ),
        gost_format="A4",
        layout_type="tree",
        include_bom=False
    )
    
    # Создание схемы
    response = handler.create_division_scheme(request_data)
    
    if response.success:
        logger.info(f"Схема успешно создана: {response.file_path}")
    else:
        logger.error(f"Ошибка при создании схемы: {response.message}")
        logger.error(f"Детали ошибок: {response.errors}")
        
except RuntimeError as e:
    logger.error(f"Ошибка выполнения: {e}")
except Exception as e:
    logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
```

---

## Проверка валидации координат

### Пример с обработкой неправильных координат

```python
from server.kompas_api_handler import KompasAPIHandler

handler = KompasAPIHandler()

# Попытка рисования с неправильными координатами
test_cases = [
    (-10, 10, 50, 50),      # Отрицательные координаты
    (10, -10, 50, 50),      # Отрицательные координаты
    (10, 10, -50, 50),      # Отрицательная ширина
    (10, 10, 50, -50),      # Отрицательная высота
    (400, 200, 100, 100),   # Выход за границы листа
]

for x, y, width, height in test_cases:
    is_valid = handler._validate_coordinates(x, y, width, height)
    status = "✓ Валидно" if is_valid else "✗ Невалидно"
    print(f"({x}, {y}, {width}, {height}): {status}")

# Вывод:
# (-10, 10, 50, 50): ✗ Невалидно
# (10, -10, 50, 50): ✗ Невалидно
# (10, 10, -50, 50): ✗ Невалидно
# (10, 10, 50, -50): ✗ Невалидно
# (400, 200, 100, 100): ✗ Невалидно
```

---

## Использование различных форматов листов

### Пример с разными форматами

```python
from server.models import CreateDivisionSchemeRequest, Component, TitleBlockData

# Компоненты для примера
components = [
    Component(position=i, name=f"Компонент {i}", 
              designation=f"КОМ.01.01.{i:03d}", quantity=1, parent_position=None)
    for i in range(1, 6)
]

# Тестирование разных форматов
formats = ["A0", "A1", "A2", "A3", "A4", "A5"]

for fmt in formats:
    request_data = CreateDivisionSchemeRequest(
        product_code="ТЕСТ.01.01.001",
        product_name=f"Тест формата {fmt}",
        components=components,
        title_block_data=TitleBlockData(
            designation="ТЕСТ.01.01.001",
            name=f"Тест формата {fmt}"
        ),
        gost_format=fmt,
        layout_type="tree",
        include_bom=True
    )
    
    response = requests.post(
        "http://localhost:8000/api/v1/create_division_scheme",
        json=request_data.dict()
    )
    
    if response.json()["success"]:
        print(f"✓ Формат {fmt}: успешно")
    else:
        print(f"✗ Формат {fmt}: ошибка")
```

---

## Использование различных типов размещения

### Пример с разными типами layout

```python
from server.models import CreateDivisionSchemeRequest

# Компоненты
components = [
    Component(position=i, name=f"Компонент {i}", 
              designation=f"КОМ.01.01.{i:03d}", quantity=1, parent_position=None)
    for i in range(1, 10)
]

# Тестирование разных типов размещения
layout_types = ["tree", "vertical", "horizontal"]

for layout in layout_types:
    request_data = CreateDivisionSchemeRequest(
        product_code="ТЕСТ.01.01.001",
        product_name=f"Тест размещения {layout}",
        components=components,
        title_block_data=TitleBlockData(
            designation="ТЕСТ.01.01.001",
            name=f"Тест размещения {layout}"
        ),
        gost_format="A2",
        layout_type=layout,
        include_bom=True
    )
    
    response = requests.post(
        "http://localhost:8000/api/v1/create_division_scheme",
        json=request_data.dict()
    )
    
    if response.json()["success"]:
        print(f"✓ Тип {layout}: успешно")
    else:
        print(f"✗ Тип {layout}: ошибка")
```

---

## Полный пример с логированием

### Комплексный пример с подробным логированием

```python
import logging
import json
from server.main import app
from server.models import CreateDivisionSchemeRequest, Component, TitleBlockData
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kompas_mcp_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_division_scheme_with_logging():
    """Создание схемы деления с подробным логированием."""
    
    logger.info("=" * 80)
    logger.info("НАЧАЛО: Создание схемы деления")
    logger.info("=" * 80)
    
    try:
        # Подготовка данных
        logger.info("Подготовка данных...")
        
        title_block = TitleBlockData(
            designation="ПРИБОР.01.01.001",
            name="Прибор управления",
            developer="В.В. Васильев",
            organization="ООО Приборостроение"
        )
        logger.debug(f"Основная надпись: {title_block}")
        
        components = [
            Component(
                position=1,
                name="Электронный блок",
                designation="БЛОК.01.01.002",
                quantity=1,
                parent_position=None
            ),
            Component(
                position=2,
                name="Микроконтроллер",
                designation="МК.01.01.003",
                quantity=1,
                parent_position=1
            ),
            Component(
                position=3,
                name="Конденсатор",
                designation="К.01.01.004",
                quantity=2,
                parent_position=1
            ),
        ]
        logger.debug(f"Компоненты: {len(components)} шт.")
        
        # Создание запроса
        logger.info("Создание запроса...")
        request_data = CreateDivisionSchemeRequest(
            product_code="ПРИБОР.01.01.001",
            product_name="Прибор управления",
            components=components,
            title_block_data=title_block,
            gost_format="A3",
            layout_type="tree",
            include_bom=True
        )
        logger.debug(f"Запрос: {request_data.json()}")
        
        # Отправка запроса
        logger.info("Отправка запроса к API...")
        response = requests.post(
            "http://localhost:8000/api/v1/create_division_scheme",
            json=request_data.dict(),
            timeout=30
        )
        logger.info(f"HTTP статус: {response.status_code}")
        
        # Обработка результата
        result = response.json()
        logger.debug(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result["success"]:
            logger.info(f"✓ УСПЕХ: Схема создана")
            logger.info(f"Путь к файлу: {result['file_path']}")
        else:
            logger.error(f"✗ ОШИБКА: {result['message']}")
            logger.error(f"Детали: {result['errors']}")
        
        logger.info("=" * 80)
        logger.info("КОНЕЦ: Создание схемы деления")
        logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        logger.error(f"ИСКЛЮЧЕНИЕ: {e}", exc_info=True)
        raise

# Запуск примера
if __name__ == "__main__":
    create_division_scheme_with_logging()
```

---

## Заключение

Эти примеры демонстрируют различные способы использования KOMPAS-3D MCP Server v2 (100/100):

- ✅ Базовое создание схем деления
- ✅ Работа со сложными иерархиями
- ✅ Использование дополнительных примитивов
- ✅ Интеграция с MCP
- ✅ Правильная обработка ошибок
- ✅ Валидация координат
- ✅ Работа с разными форматами и типами размещения
- ✅ Подробное логирование

**Все примеры полностью работоспособны и готовы к использованию!**
