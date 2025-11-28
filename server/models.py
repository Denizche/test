"""
Модели данных для MCP-сервера КОМПАС-3D.

Этот модуль содержит Pydantic-модели для валидации входящих запросов
к API КОМПАС-3D, с приоритизацией на создание схем деления изделий по ГОСТ 2.701.
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, validator


class Component(BaseModel):
    """Компонент в составе изделия (для схемы деления)."""
    position: int = Field(
        ...,
        ge=1,
        description="Позиционный номер компонента в схеме деления"
    )
    name: str = Field(
        ...,
        description="Наименование компонента (Корпус, Вал ведущий, Шестерня и т.д.)"
    )
    designation: str = Field(
        ...,
        description="Обозначение компонента (XXXX.XX.XX.XXX по ГОСТ)"
    )
    quantity: int = Field(
        default=1,
        ge=1,
        description="Количество компонентов"
    )
    level: int = Field(
        default=0,
        ge=0,
        description="Уровень иерархии (0 - главное изделие, 1+ - составные части)"
    )
    parent_position: Optional[int] = Field(
        None,
        description="Позиционный номер родительского компонента (для иерархии)"
    )
    notes: Optional[str] = Field(
        None,
        description="Примечания к компоненту"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "position": 1,
                "name": "Корпус",
                "designation": "1234.01.00.000",
                "quantity": 1,
                "level": 0
            }
        }


class BOMRow(BaseModel):
    """Строка спецификации (Bill of Materials)."""
    position: int = Field(..., description="Позиционный номер")
    designation: str = Field(..., description="Обозначение")
    name: str = Field(..., description="Наименование")
    quantity: int = Field(..., description="Количество")
    notes: Optional[str] = Field(None, description="Примечания")

    class Config:
        json_schema_extra = {
            "example": {
                "position": 1,
                "designation": "1234.01.00.000",
                "name": "Корпус",
                "quantity": 1
            }
        }


class TitleBlockData(BaseModel):
    """Данные основной надписи (штампа) чертежа по ГОСТ."""
    designation: Optional[str] = Field(
        None,
        description="Обозначение изделия (XXXX.XX.XX.XXX)"
    )
    name: Optional[str] = Field(
        None,
        description="Наименование изделия"
    )
    developer: Optional[str] = Field(
        None,
        description="Разработал"
    )
    checker: Optional[str] = Field(
        None,
        description="Проверил"
    )
    approver: Optional[str] = Field(
        None,
        description="Утвердил"
    )
    organization: Optional[str] = Field(
        None,
        description="Организация"
    )
    scale: Optional[str] = Field(
        None,
        description="Масштаб (1:1, 1:2 и т.д.)"
    )
    sheet_number: Optional[int] = Field(
        None,
        description="Номер листа"
    )
    total_sheets: Optional[int] = Field(
        None,
        description="Всего листов"
    )
    date: Optional[str] = Field(
        None,
        description="Дата (YYYY-MM-DD)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "designation": "1234.00.00.000",
                "name": "Редуктор цилиндрический",
                "developer": "Иванов И.И.",
                "organization": "ООО Компания"
            }
        }


class CreateDivisionSchemeRequest(BaseModel):
    """Запрос на создание схемы деления изделия."""
    product_name: str = Field(
        ...,
        description="Наименование главного изделия (Редуктор, Станок и т.д.)"
    )
    product_code: str = Field(
        ...,
        description="Обозначение главного изделия (XXXX.XX.XX.XXX по ГОСТ)"
    )
    components: List[Component] = Field(
        ...,
        min_items=1,
        description="Список компонентов в составе изделия"
    )
    gost_format: Literal["A3", "A4", "A2", "A1", "A0"] = Field(
        "A3",
        description="Формат листа по ГОСТ"
    )
    orientation: Literal["portrait", "landscape"] = Field(
        "landscape",
        description="Ориентация листа"
    )
    layout_type: Literal["tree", "vertical", "horizontal"] = Field(
        "tree",
        description="Тип размещения компонентов: tree (древовидная), vertical (вертикальная), horizontal (горизонтальная)"
    )
    title_block_data: TitleBlockData = Field(
        ...,
        description="Данные основной надписи"
    )
    include_bom: bool = Field(
        True,
        description="Включить спецификацию (таблицу компонентов) на чертеж"
    )
    output_path: Optional[str] = Field(
        None,
        description="Путь для сохранения файла (если не указан, используется C:\\KOMPAS_OUTPUT)"
    )

    @validator('product_code')
    def validate_product_code(cls, v):
        """Проверка формата обозначения по ГОСТ (XXXX.XX.XX.XXX)."""
        import re
        pattern = r'^\d{4}\.\d{2}\.\d{2}\.\d{3}$'
        if not re.match(pattern, v):
            raise ValueError("Обозначение должно соответствовать формату ГОСТ: XXXX.XX.XX.XXX")
        return v

    @validator('components')
    def validate_components_hierarchy(cls, v):
        """Проверка корректности иерархии компонентов."""
        # Проверка уникальности позиционных номеров
        positions = [c.position for c in v]
        if len(positions) != len(set(positions)):
            raise ValueError("Позиционные номера компонентов должны быть уникальными")
        
        # Проверка ссылок на родительские компоненты
        valid_positions = set(positions)
        for component in v:
            if component.parent_position is not None and component.parent_position not in valid_positions:
                raise ValueError(f"Компонент {component.position} ссылается на несуществующий родитель {component.parent_position}")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Редуктор цилиндрический",
                "product_code": "1234.00.00.000",
                "gost_format": "A3",
                "orientation": "landscape",
                "layout_type": "tree",
                "title_block_data": {
                    "designation": "1234.00.00.000",
                    "name": "Схема деления",
                    "developer": "Иванов И.И."
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
                    }
                ],
                "include_bom": True
            }
        }


class DrawSchemaResponse(BaseModel):
    """Ответ на запрос создания схемы."""
    success: bool = Field(
        ...,
        description="Статус выполнения операции"
    )
    file_path: Optional[str] = Field(
        None,
        description="Полный путь к созданному файлу чертежа"
    )
    message: str = Field(
        ...,
        description="Сообщение о результате операции"
    )
    error_details: Optional[str] = Field(
        None,
        description="Детали ошибки (если операция не удалась)"
    )
    bom_generated: Optional[bool] = Field(
        None,
        description="Была ли сгенерирована спецификация"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "file_path": "C:\\KOMPAS_OUTPUT\\DivisionScheme_1234.00.00.000_a1b2c3d4.cdw",
                "message": "Схема деления успешно создана и сохранена",
                "bom_generated": True
            }
        }


class HealthCheckResponse(BaseModel):
    """Ответ на запрос проверки здоровья сервера."""
    status: Literal["healthy", "unhealthy"] = Field(
        ...,
        description="Статус сервера"
    )
    kompas_connected: bool = Field(
        ...,
        description="Статус подключения к КОМПАС-3D"
    )
    version: str = Field(
        ...,
        description="Версия API сервера"
    )
    message: str = Field(
        ...,
        description="Описание статуса"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "kompas_connected": True,
                "version": "1.0.0",
                "message": "Сервер работает корректно, КОМПАС-3D подключен"
            }
        }
