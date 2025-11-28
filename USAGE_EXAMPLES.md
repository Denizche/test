# Примеры использования KOMPAS-3D MCP Server

## Создание схем деления изделий по ГОСТ 2.701

Этот документ содержит практические примеры использования API для создания схем деления.

---

## Пример 1: Простая схема деления редуктора

Создание схемы деления простого редуктора с тремя основными компонентами.

### cURL запрос

```bash
curl -X POST http://localhost:8000/api/v1/create_division_scheme \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Редуктор цилиндрический",
    "product_code": "1234.00.00.000",
    "gost_format": "A3",
    "orientation": "landscape",
    "layout_type": "tree",
    "title_block_data": {
      "designation": "1234.00.00.000",
      "name": "Схема деления",
      "developer": "Иванов И.И.",
      "organization": "ООО Компания"
    },
    "components": [
      {
        "position": 1,
        "name": "Редуктор цилиндрический",
        "designation": "1234.00.00.000",
        "quantity": 1,
        "level": 0
      },
      {
        "position": 2,
        "name": "Корпус",
        "designation": "1234.01.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      },
      {
        "position": 3,
        "name": "Вал ведущий",
        "designation": "1234.02.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      },
      {
        "position": 4,
        "name": "Вал ведомый",
        "designation": "1234.03.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      }
    ],
    "include_bom": true
  }'
```

### Python код

```python
import requests
import json

url = "http://localhost:8000/api/v1/create_division_scheme"

payload = {
    "product_name": "Редуктор цилиндрический",
    "product_code": "1234.00.00.000",
    "gost_format": "A3",
    "orientation": "landscape",
    "layout_type": "tree",
    "title_block_data": {
        "designation": "1234.00.00.000",
        "name": "Схема деления",
        "developer": "Иванов И.И.",
        "organization": "ООО Компания"
    },
    "components": [
        {
            "position": 1,
            "name": "Редуктор цилиндрический",
            "designation": "1234.00.00.000",
            "quantity": 1,
            "level": 0
        },
        {
            "position": 2,
            "name": "Корпус",
            "designation": "1234.01.00.000",
            "quantity": 1,
            "level": 1,
            "parent_position": 1
        },
        {
            "position": 3,
            "name": "Вал ведущий",
            "designation": "1234.02.00.000",
            "quantity": 1,
            "level": 1,
            "parent_position": 1
        },
        {
            "position": 4,
            "name": "Вал ведомый",
            "designation": "1234.03.00.000",
            "quantity": 1,
            "level": 1,
            "parent_position": 1
        }
    ],
    "include_bom": True
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    result = response.json()
    if result["success"]:
        print(f"✓ Схема создана: {result['file_path']}")
        print(f"  Спецификация: {'да' if result.get('bom_generated') else 'нет'}")
    else:
        print(f"✗ Ошибка: {result['message']}")
else:
    print(f"✗ HTTP Error: {response.status_code}")
    print(response.text)
```

---

## Пример 2: Сложная иерархическая схема деления

Создание схемы деления с многоуровневой иерархией компонентов.

```bash
curl -X POST http://localhost:8000/api/v1/create_division_scheme \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Станок токарный",
    "product_code": "5678.00.00.000",
    "gost_format": "A2",
    "orientation": "landscape",
    "layout_type": "tree",
    "title_block_data": {
      "designation": "5678.00.00.000",
      "name": "Схема деления станка",
      "developer": "Петров П.П.",
      "checker": "Сидоров С.С.",
      "organization": "ООО Компания"
    },
    "components": [
      {
        "position": 1,
        "name": "Станок токарный",
        "designation": "5678.00.00.000",
        "quantity": 1,
        "level": 0
      },
      {
        "position": 2,
        "name": "Станина",
        "designation": "5678.01.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      },
      {
        "position": 3,
        "name": "Шпиндель",
        "designation": "5678.02.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      },
      {
        "position": 4,
        "name": "Привод",
        "designation": "5678.03.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      },
      {
        "position": 5,
        "name": "Двигатель электрический",
        "designation": "ДВ-100",
        "quantity": 1,
        "level": 2,
        "parent_position": 4
      },
      {
        "position": 6,
        "name": "Редуктор",
        "designation": "РД-50",
        "quantity": 1,
        "level": 2,
        "parent_position": 4
      },
      {
        "position": 7,
        "name": "Муфта соединительная",
        "designation": "МС-20",
        "quantity": 1,
        "level": 2,
        "parent_position": 4
      }
    ],
    "include_bom": true
  }'
```

---

## Пример 3: Вертикальное размещение компонентов

Создание схемы деления с вертикальным размещением компонентов.

```python
import requests

url = "http://localhost:8000/api/v1/create_division_scheme"

payload = {
    "product_name": "Насос центробежный",
    "product_code": "9012.00.00.000",
    "gost_format": "A4",
    "orientation": "portrait",
    "layout_type": "vertical",  # Вертикальное размещение
    "title_block_data": {
        "designation": "9012.00.00.000",
        "name": "Схема деления насоса",
        "developer": "Иванов И.И."
    },
    "components": [
        {
            "position": 1,
            "name": "Насос центробежный",
            "designation": "9012.00.00.000",
            "quantity": 1,
            "level": 0
        },
        {
            "position": 2,
            "name": "Корпус",
            "designation": "9012.01.00.000",
            "quantity": 1,
            "level": 1,
            "parent_position": 1
        },
        {
            "position": 3,
            "name": "Рабочее колесо",
            "designation": "9012.02.00.000",
            "quantity": 1,
            "level": 1,
            "parent_position": 1
        },
        {
            "position": 4,
            "name": "Вал",
            "designation": "9012.03.00.000",
            "quantity": 1,
            "level": 1,
            "parent_position": 1
        }
    ],
    "include_bom": True
}

response = requests.post(url, json=payload)
print(response.json())
```

---

## Пример 4: Горизонтальное размещение компонентов

Создание схемы деления с горизонтальным размещением.

```bash
curl -X POST http://localhost:8000/api/v1/create_division_scheme \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Передача",
    "product_code": "3456.00.00.000",
    "gost_format": "A4",
    "orientation": "landscape",
    "layout_type": "horizontal",
    "title_block_data": {
      "designation": "3456.00.00.000",
      "name": "Схема деления передачи",
      "developer": "Иванов И.И."
    },
    "components": [
      {
        "position": 1,
        "name": "Передача",
        "designation": "3456.00.00.000",
        "quantity": 1,
        "level": 0
      },
      {
        "position": 2,
        "name": "Вал входной",
        "designation": "3456.01.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      },
      {
        "position": 3,
        "name": "Шестерня ведущая",
        "designation": "3456.02.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      },
      {
        "position": 4,
        "name": "Шестерня ведомая",
        "designation": "3456.03.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      },
      {
        "position": 5,
        "name": "Вал выходной",
        "designation": "3456.04.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      }
    ],
    "include_bom": true
  }'
```

---

## Пример 5: Проверка статуса сервера

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "kompas_connected": true,
  "version": "1.0.0",
  "message": "Сервер работает корректно, КОМПАС-3D подключен"
}
```

---

## Пример 6: Получение информации об API

```bash
curl http://localhost:8000/api/v1/info
```

Ответ:
```json
{
  "api_version": "1.0.0",
  "api_title": "KOMPAS-3D MCP Server - Division Schemes",
  "primary_purpose": "Создание схем деления изделий по ГОСТ 2.701",
  "supported_layout_types": {
    "tree": "Древовидная структура с иерархией (рекомендуется)",
    "vertical": "Вертикальное размещение в столбец",
    "horizontal": "Горизонтальное размещение в строку"
  },
  "supported_formats": ["A0", "A1", "A2", "A3", "A4"],
  "supported_orientations": ["portrait", "landscape"]
}
```

---

## Обработка ошибок

### Пример: Некорректное обозначение компонента

```bash
curl -X POST http://localhost:8000/api/v1/create_division_scheme \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Изделие",
    "product_code": "1234.00.00.000",
    "title_block_data": {
      "designation": "1234.00.00.000",
      "name": "Схема"
    },
    "components": [
      {
        "position": 1,
        "name": "Главное изделие",
        "designation": "INVALID",
        "quantity": 1,
        "level": 0
      }
    ]
  }'
```

Ответ (ошибка):
```json
{
  "detail": "Ошибка валидации по ГОСТ 2.701: Компонент 1: обозначение 'INVALID' не соответствует формату ГОСТ (XXXX.XX.XX.XXX)"
}
```

### Пример: Дублирующиеся позиционные номера

```bash
curl -X POST http://localhost:8000/api/v1/create_division_scheme \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Изделие",
    "product_code": "1234.00.00.000",
    "title_block_data": {
      "designation": "1234.00.00.000",
      "name": "Схема"
    },
    "components": [
      {
        "position": 1,
        "name": "Компонент 1",
        "designation": "1234.01.00.000",
        "quantity": 1,
        "level": 0
      },
      {
        "position": 1,
        "name": "Компонент 2",
        "designation": "1234.02.00.000",
        "quantity": 1,
        "level": 1,
        "parent_position": 1
      }
    ]
  }'
```

Ответ (ошибка):
```json
{
  "detail": "Ошибка валидации по ГОСТ 2.701: Дублирующиеся позиционные номера: [1]"
}
```

---

## Успешный ответ

```json
{
  "success": true,
  "file_path": "C:\\KOMPAS_OUTPUT\\DivisionScheme_1234.00.00.000_a1b2c3d4.cdw",
  "message": "Схема деления успешно создана и сохранена: C:\\KOMPAS_OUTPUT\\DivisionScheme_1234.00.00.000_a1b2c3d4.cdw",
  "bom_generated": true
}
```

---

## Рекомендации

1. **Используйте древовидное размещение** (layout_type="tree") для иерархических изделий - это наиболее наглядно представляет структуру.

2. **Всегда указывайте обозначения в формате ГОСТ** (XXXX.XX.XX.XXX) - это обязательно для валидации.

3. **Генерируйте спецификацию** (include_bom=true) - это обязательный элемент схемы деления по ГОСТ 2.701.

4. **Проверяйте иерархию компонентов** - убедитесь, что parent_position указывает на существующий компонент с меньшим уровнем.

5. **Используйте подходящий формат листа** - для сложных изделий используйте A2 или A1, для простых - A3 или A4.

---

## Интеграция с Python

```python
import requests
from typing import List, Dict

class DivisionSchemeClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def create_scheme(self, product_name: str, product_code: str, components: List[Dict]):
        """Создание схемы деления."""
        url = f"{self.base_url}/api/v1/create_division_scheme"
        
        payload = {
            "product_name": product_name,
            "product_code": product_code,
            "gost_format": "A3",
            "layout_type": "tree",
            "title_block_data": {
                "designation": product_code,
                "name": f"Схема деления {product_name}"
            },
            "components": components,
            "include_bom": True
        }
        
        response = requests.post(url, json=payload)
        return response.json()
    
    def check_health(self):
        """Проверка статуса сервера."""
        url = f"{self.base_url}/health"
        response = requests.get(url)
        return response.json()

# Использование
client = DivisionSchemeClient()

# Проверка статуса
health = client.check_health()
print(f"Сервер: {health['status']}, КОМПАС-3D: {health['kompas_connected']}")

# Создание схемы
components = [
    {"position": 1, "name": "Редуктор", "designation": "1234.00.00.000", "quantity": 1, "level": 0},
    {"position": 2, "name": "Корпус", "designation": "1234.01.00.000", "quantity": 1, "level": 1, "parent_position": 1},
]

result = client.create_scheme("Редуктор", "1234.00.00.000", components)
if result["success"]:
    print(f"Схема создана: {result['file_path']}")
else:
    print(f"Ошибка: {result['message']}")
```

---

**Дополнительная информация:** Полная документация доступна в README.md и в Swagger UI по адресу http://localhost:8000/docs
