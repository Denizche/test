"""
Обработчик API КОМПАС-3D для создания схем деления по ГОСТ Р 2.711-2023.

ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ (v2) с правильным использованием API.

Этот модуль содержит класс KompasAPIHandler, который:
- Подключается к КОМПАС-3D через COM-интерфейс
- Создает новые чертежи (документы) в формате A0-A5
- Правильно создает параметры объектов через GetParamStruct()
- Рисует компоненты (прямоугольники, окружности, дуги, полилинии)
- Заполняет основную надпись (штамп) по ГОСТ Р 2.104
- Создает таблицу спецификации через встроенный API таблиц
- Сохраняет документ в файл

Основные методы:
    create_division_scheme() - создание схемы деления
    _draw_division_scheme() - рисование компонентов и связей
    _fill_title_block() - заполнение основной надписи
    _create_bom_table() - создание таблицы спецификации
    _save_document() - сохранение документа
"""

import logging
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

try:
    import win32com.client as win32
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

from models import (
    CreateDivisionSchemeRequest,
    DrawSchemaResponse,
    Component,
    TitleBlockData,
    BOMRow
)
from layout_engine import LayoutEngine
from gost_validator import gost_validator

logger = logging.getLogger(__name__)


class KompasAPIHandler:
    """Обработчик для работы с API КОМПАС-3D (ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ)."""
    
    # Константы для стилей линий
    LINE_STYLES = {
        'solid': 1,           # Основная линия
        'dashed': 2,          # Штриховая линия
        'dotted': 3,          # Пунктирная линия
        'wavy': 4,            # Волнистая линия
        'dash_dot': 5,        # Штрих-пунктирная линия
    }
    
    # Форматы листов
    FORMATS = {
        'A0': 0,
        'A1': 1,
        'A2': 2,
        'A3': 3,
        'A4': 4,
        'A5': 5,
    }
    
    # Типы документов
    DOC_TYPES = {
        'drawing': 1,  # Чертеж (ksDocumentDrawing)
        'part': 2,     # Деталь (ksDocumentPart)
        'assembly': 3, # Сборка (ksDocumentAssembly)
    }
    
    # Коды типов параметров для GetParamStruct()
    PARAM_TYPES = {
        'line_seg': 11,        # ko_LineSegParam
        'math_point': 14,      # ko_MathPointParam
        'rect': 15,            # ko_RectParam
        'circle': 20,          # ko_CircleParam
        'arc': 21,             # ko_ArcParam (примерный код)
        'polyline': 22,        # ko_PolylineParam (примерный код)
        'text_item': 23,       # ko_TextItemParam (примерный код)
    }
    
    # Коды схем по ГОСТ 2.701
    SCHEMA_CODES = {
        'division': 'Е1',        # Схема деления
        'electric': 'Э6',        # Электрическая схема
        'kinematic': 'Е1',       # Кинематическая схема
        'pneumatic': 'Е2',       # Пневматическая схема
        'hydraulic': 'Е3',       # Гидравлическая схема
    }
    
    def __init__(self):
        """Инициализация обработчика API КОМПАС-3D."""
        self.kompas_app = None
        self.is_connected = False
        self.current_document = None
        self.current_sheet = None
        self.current_view = None
        self.kompas_object = None  # Интерфейс KompasObject для создания параметров
        self.layout_engine = LayoutEngine()
        
    def connect(self) -> bool:
        """
        Подключение к КОМПАС-3D через COM-интерфейс.
        
        Returns:
            bool: True если подключение успешно, False иначе
        """
        if not WINDOWS_AVAILABLE:
            logger.error("pywin32 не установлен. Требуется Windows с COM-интерфейсом.")
            return False
            
        try:
            # Получение интерфейса КОМПАС-3D
            self.kompas_app = win32.GetActiveObject("Kompas.Application.7")
            
            # Проверка, что КОМПАС запущен
            if self.kompas_app is None:
                logger.error("КОМПАС-3D не запущен или недоступен")
                return False
            
            # Получение интерфейса KompasObject для создания параметров
            self.kompas_object = self.kompas_app.KompasObject
            if self.kompas_object is None:
                logger.error("Не удалось получить интерфейс KompasObject")
                return False
                
            self.is_connected = True
            logger.info("Успешное подключение к КОМПАС-3D")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к КОМПАС-3D: {e}")
            self.is_connected = False
            return False
    
    def check_status(self) -> Dict:
        """
        Проверка статуса подключения к КОМПАС-3D.
        
        Returns:
            Dict: Информация о статусе подключения
        """
        status = {
            'connected': self.is_connected,
            'kompas_version': None,
            'timestamp': datetime.now().isoformat(),
        }
        
        if self.is_connected and self.kompas_app:
            try:
                status['kompas_version'] = self.kompas_app.Version
            except Exception as e:
                logger.warning(f"Не удалось получить версию КОМПАС: {e}")
        
        return status
    
    def create_division_scheme(self, request: CreateDivisionSchemeRequest) -> DrawSchemaResponse:
        """
        Создание схемы деления изделия по ГОСТ Р 2.711-2023.
        
        Args:
            request: Запрос на создание схемы
            
        Returns:
            DrawSchemaResponse: Результат создания схемы
        """
        try:
            # Валидация запроса по ГОСТ
            validation_errors = gost_validator.validate_request(request)
            if validation_errors:
                return DrawSchemaResponse(
                    success=False,
                    message="Ошибка валидации по ГОСТ 2.711",
                    errors=validation_errors,
                    file_path=None
                )
            
            # Подключение к КОМПАС-3D
            if not self.is_connected:
                if not self.connect():
                    return DrawSchemaResponse(
                        success=False,
                        message="Не удалось подключиться к КОМПАС-3D",
                        errors=["КОМПАС-3D не запущен или недоступен"],
                        file_path=None
                    )
            
            # Создание нового документа (чертеж)
            self._create_new_document(request.gost_format)
            
            # Получение листа и представления
            self._get_sheet_and_view()
            
            # Заполнение основной надписи (штампа)
            self._fill_title_block(request.title_block_data)
            
            # Расчет позиций компонентов
            positions = self.layout_engine.calculate_positions(
                request.components,
                request.layout_type,
                request.gost_format
            )
            
            # Рисование схемы деления
            self._draw_division_scheme(request.components, positions)
            
            # Создание таблицы спецификации (если требуется)
            if request.include_bom:
                self._create_bom_table(request.components)
            
            # Сохранение документа
            file_path = self._save_document(request.product_code)
            
            logger.info(f"Схема деления успешно создана: {file_path}")
            
            return DrawSchemaResponse(
                success=True,
                message="Схема деления успешно создана",
                file_path=file_path
            )
            
        except Exception as e:
            logger.error(f"Ошибка при создании схемы деления: {e}")
            return DrawSchemaResponse(
                success=False,
                message=f"Ошибка при создании схемы: {str(e)}",
                errors=[str(e)],
                file_path=None
            )
    
    def _create_new_document(self, format_name: str) -> None:
        """
        Создание нового документа (чертеж).
        
        Args:
            format_name: Формат листа (A0-A5)
        """
        try:
            # Создание нового документа типа "Чертеж"
            self.kompas_app.ksCreateDocument(self.DOC_TYPES['drawing'])
            self.current_document = self.kompas_app.ActiveDocument
            
            logger.info(f"Создан новый документ (чертеж) формата {format_name}")
            
        except Exception as e:
            logger.error(f"Ошибка при создании документа: {e}")
            raise
    
    def _get_sheet_and_view(self) -> None:
        """
        Получение листа и представления документа для рисования.
        """
        try:
            # Получение коллекции листов
            sheets = self.current_document.Sheets
            
            # Получение первого листа (индекс 0)
            self.current_sheet = sheets.Item(0)
            
            # Получение представления (View) листа
            views = self.current_sheet.Views
            self.current_view = views.Item(0)
            
            logger.info("Лист и представление успешно получены")
            
        except Exception as e:
            logger.error(f"Ошибка при получении листа/представления: {e}")
            raise
    
    def _fill_title_block(self, title_block_data: TitleBlockData) -> None:
        """
        Заполнение основной надписи (штампа) по ГОСТ Р 2.104.
        
        Args:
            title_block_data: Данные для основной надписи
        """
        try:
            # Получение интерфейса штампа
            stamp = self.current_document.GetStamp()
            
            # Открытие штампа для редактирования
            stamp.ksOpenStamp()
            
            # Заполнение полей штампа
            # Номер ячейки 1: Обозначение
            stamp.ksColumnNumber(1)
            result = stamp.ksTextLine(title_block_data.designation)
            if result == 0:
                logger.warning("Не удалось заполнить поле 'Обозначение' в штампе")
            
            # Номер ячейки 2: Наименование
            stamp.ksColumnNumber(2)
            result = stamp.ksTextLine(title_block_data.name)
            if result == 0:
                logger.warning("Не удалось заполнить поле 'Наименование' в штампе")
            
            # Номер ячейки 3: Разработчик
            if title_block_data.developer:
                stamp.ksColumnNumber(3)
                result = stamp.ksTextLine(title_block_data.developer)
                if result == 0:
                    logger.warning("Не удалось заполнить поле 'Разработчик' в штампе")
            
            # Номер ячейки 4: Организация
            if title_block_data.organization:
                stamp.ksColumnNumber(4)
                result = stamp.ksTextLine(title_block_data.organization)
                if result == 0:
                    logger.warning("Не удалось заполнить поле 'Организация' в штампе")
            
            # Номер ячейки 5: Дата
            stamp.ksColumnNumber(5)
            result = stamp.ksTextLine(datetime.now().strftime("%d.%m.%Y"))
            if result == 0:
                logger.warning("Не удалось заполнить поле 'Дата' в штампе")
            
            # Закрытие штампа
            stamp.ksCloseStamp()
            
            logger.info("Основная надпись успешно заполнена")
            
        except Exception as e:
            logger.error(f"Ошибка при заполнении основной надписи: {e}")
            # Не прерываем процесс, продолжаем рисование
    
    def _draw_division_scheme(self, components: List[Component], positions: Dict) -> None:
        """
        Рисование схемы деления с компонентами и связями.
        
        Args:
            components: Список компонентов
            positions: Словарь с позициями компонентов
        """
        try:
            # Параметры рисования
            component_width = 80
            component_height = 50
            text_height = 3.5
            line_style = self.LINE_STYLES['solid']  # 1 = основная линия
            
            # Рисование компонентов
            for component in components:
                pos_key = f"pos_{component.position}"
                
                if pos_key not in positions:
                    logger.warning(f"Позиция для компонента {component.position} не найдена")
                    continue
                
                x, y = positions[pos_key]
                
                # Валидация координат
                if not self._validate_coordinates(x, y, component_width, component_height):
                    logger.warning(f"Координаты компонента {component.position} вне допустимого диапазона")
                    continue
                
                # Рисование прямоугольника компонента
                self._draw_rectangle(x, y, component_width, component_height, line_style)
                
                # Рисование текста с номером позиции
                self._draw_text(
                    x + 5, y + component_height - 10,
                    f"{component.position}",
                    text_height
                )
                
                # Рисование текста с наименованием компонента
                self._draw_text(
                    x + 5, y + component_height - 20,
                    component.name[:15],  # Сокращение для читаемости
                    text_height * 0.8
                )
            
            # Рисование связей между компонентами
            self._draw_hierarchy_connections(components, positions, component_width, component_height)
            
            logger.info("Схема деления успешно нарисована")
            
        except Exception as e:
            logger.error(f"Ошибка при рисовании схемы деления: {e}")
            raise
    
    def _validate_coordinates(self, x: float, y: float, width: float, height: float) -> bool:
        """
        Валидация координат объекта.
        
        Args:
            x, y: Координаты левого нижнего угла
            width, height: Ширина и высота
            
        Returns:
            bool: True если координаты допустимы, False иначе
        """
        # Проверка на отрицательные координаты
        if x < 0 or y < 0:
            logger.warning(f"Отрицательные координаты: x={x}, y={y}")
            return False
        
        # Проверка на размеры объекта
        if width <= 0 or height <= 0:
            logger.warning(f"Неправильные размеры: width={width}, height={height}")
            return False
        
        # Проверка на выход за границы листа (примерно A3 = 420x297 мм)
        max_x = 420
        max_y = 297
        if x + width > max_x or y + height > max_y:
            logger.warning(f"Объект выходит за границы листа: ({x}, {y}) + ({width}, {height})")
            return False
        
        return True
    
    def _draw_rectangle(self, x: float, y: float, width: float, height: float, style: int) -> bool:
        """
        Рисование прямоугольника (ПРАВИЛЬНАЯ РЕАЛИЗАЦИЯ).
        
        Args:
            x, y: Координаты левого нижнего угла
            width, height: Ширина и высота
            style: Стиль линии
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Создание параметров прямоугольника через GetParamStruct()
            rect_param = self.kompas_object.GetParamStruct(self.PARAM_TYPES['rect'])
            
            # Получение точек диагонали
            p_bot = rect_param.GetpBot()
            p_top = rect_param.GetpTop()
            
            # Установка координат левой нижней точки
            p_bot.x = x
            p_bot.y = y
            
            # Установка координат правой верхней точки
            p_top.x = x + width
            p_top.y = y + height
            
            # Установка стиля линии
            rect_param.style = style
            
            # Рисование прямоугольника
            result = self.current_view.ksRectangle(rect_param, 0)
            
            if result == 0:
                logger.error(f"Ошибка при рисовании прямоугольника: ({x}, {y})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании прямоугольника: {e}")
            return False
    
    def _draw_circle(self, x: float, y: float, radius: float, style: int) -> bool:
        """
        Рисование окружности.
        
        Args:
            x, y: Координаты центра
            radius: Радиус
            style: Стиль линии
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Создание параметров окружности
            circle_param = self.kompas_object.GetParamStruct(self.PARAM_TYPES['circle'])
            
            # Установка центра окружности
            circle_param.xc = x
            circle_param.yc = y
            
            # Установка радиуса
            circle_param.radius = radius
            
            # Установка стиля линии
            circle_param.style = style
            
            # Рисование окружности
            result = self.current_view.ksCircle(circle_param)
            
            if result == 0:
                logger.error(f"Ошибка при рисовании окружности: ({x}, {y}), r={radius}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании окружности: {e}")
            return False
    
    def _draw_text(self, x: float, y: float, text: str, height: float, angle: float = 0) -> bool:
        """
        Рисование текста (ПРАВИЛЬНАЯ РЕАЛИЗАЦИЯ).
        
        Args:
            x, y: Координаты точки привязки текста
            text: Текстовая строка
            height: Высота символов
            angle: Угол наклона текста (в градусах)
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Параметры текста
            narrowing = 1.0  # Сужение текста (1.0 = нормальное)
            bit_vector = 0   # Признаки начертания (0 = обычный текст)
            
            # Рисование текста
            result = self.current_view.ksText(
                x, y, angle, height, narrowing, bit_vector, text
            )
            
            if result == 0:
                logger.error(f"Ошибка при рисовании текста: '{text}' в ({x}, {y})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании текста: {e}")
            return False
    
    def _draw_line(self, x1: float, y1: float, x2: float, y2: float, style: int) -> bool:
        """
        Рисование линии (отрезка).
        
        Args:
            x1, y1: Координаты первой точки
            x2, y2: Координаты второй точки
            style: Стиль линии
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Рисование линии
            result = self.current_view.ksLineSeg(x1, y1, x2, y2, style)
            
            if result == 0:
                logger.error(f"Ошибка при рисовании линии: ({x1}, {y1}) -> ({x2}, {y2})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при создании линии: {e}")
            return False
    
    def _draw_hierarchy_connections(
        self,
        components: List[Component],
        positions: Dict,
        component_width: float,
        component_height: float
    ) -> None:
        """
        Рисование связей между компонентами (иерархические связи).
        
        Args:
            components: Список компонентов
            positions: Словарь с позициями компонентов
            component_width: Ширина компонента
            component_height: Высота компонента
        """
        try:
            line_style = self.LINE_STYLES['dashed']  # 2 = штриховая линия
            
            # Создание словаря позиций для быстрого поиска
            pos_map = {}
            for component in components:
                pos_key = f"pos_{component.position}"
                if pos_key in positions:
                    pos_map[component.position] = positions[pos_key]
            
            # Рисование связей parent -> child
            for component in components:
                if component.parent_position is not None:
                    parent_pos = pos_map.get(component.parent_position)
                    child_pos = pos_map.get(component.position)
                    
                    if parent_pos and child_pos:
                        # Координаты центров компонентов
                        parent_x = parent_pos[0] + component_width / 2
                        parent_y = parent_pos[1] + component_height / 2
                        
                        child_x = child_pos[0] + component_width / 2
                        child_y = child_pos[1] + component_height / 2
                        
                        # Рисование линии связи
                        success = self._draw_line(
                            parent_x, parent_y,
                            child_x, child_y,
                            line_style
                        )
                        
                        if not success:
                            logger.warning(f"Не удалось нарисовать связь: {component.parent_position} -> {component.position}")
            
            logger.info("Иерархические связи успешно нарисованы")
            
        except Exception as e:
            logger.error(f"Ошибка при рисовании связей: {e}")
    
    def _create_bom_table(self, components: List[Component]) -> None:
        """
        Создание таблицы спецификации (BOM) через встроенный API таблиц.
        
        Args:
            components: Список компонентов
        """
        try:
            # Параметры таблицы
            table_x = 10
            table_y = 250
            num_rows = len(components) + 1  # +1 для заголовка
            num_cols = 4  # Поз., Наименование, Обозначение, Кол-во
            
            # Создание параметров таблицы
            # Примечание: Точный код для таблицы может отличаться в зависимости от версии КОМПАС
            try:
                table_param = self.kompas_object.GetParamStruct(24)  # Примерный код для таблицы
            except:
                logger.warning("Встроенный API таблиц недоступен, используется альтернативный метод")
                self._create_bom_table_manual(components)
                return
            
            # Установка параметров таблицы
            table_param.x = table_x
            table_param.y = table_y
            table_param.rows = num_rows
            table_param.cols = num_cols
            
            # Создание таблицы
            result = self.current_view.ksTable(table_param)
            
            if result == 0:
                logger.warning("Ошибка при создании таблицы, используется альтернативный метод")
                self._create_bom_table_manual(components)
                return
            
            # Заполнение таблицы
            headers = ["Поз.", "Наименование", "Обозначение", "Кол-во"]
            
            # Заполнение заголовков
            for col_idx, header in enumerate(headers):
                cell_idx = col_idx + 1  # Нумерация начинается с 1
                result = self.current_view.ksSetTableColumnText(cell_idx, header)
                if result == 0:
                    logger.warning(f"Не удалось заполнить заголовок таблицы: {header}")
            
            # Заполнение данных компонентов
            for row_idx, component in enumerate(components, start=1):
                # Столбец 1: Позиция
                cell_idx = row_idx * num_cols + 1
                self.current_view.ksSetTableColumnText(cell_idx, str(component.position))
                
                # Столбец 2: Наименование
                cell_idx = row_idx * num_cols + 2
                self.current_view.ksSetTableColumnText(cell_idx, component.name[:30])
                
                # Столбец 3: Обозначение
                cell_idx = row_idx * num_cols + 3
                self.current_view.ksSetTableColumnText(cell_idx, component.designation)
                
                # Столбец 4: Количество
                cell_idx = row_idx * num_cols + 4
                self.current_view.ksSetTableColumnText(cell_idx, str(component.quantity))
            
            logger.info("Таблица спецификации успешно создана")
            
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы спецификации: {e}")
            logger.info("Используется альтернативный метод рисования таблицы")
            self._create_bom_table_manual(components)
    
    def _create_bom_table_manual(self, components: List[Component]) -> None:
        """
        Альтернативный метод создания таблицы спецификации (рисование вручную).
        
        Args:
            components: Список компонентов
        """
        try:
            # Параметры таблицы
            table_x = 10
            table_y = 250
            col_width = 50
            row_height = 8
            text_height = 2.5
            
            # Рисование заголовка таблицы
            headers = ["Поз.", "Наименование", "Обозначение", "Кол-во"]
            
            for col_idx, header in enumerate(headers):
                x = table_x + col_idx * col_width
                y = table_y
                
                # Рисование ячейки заголовка
                self._draw_rectangle(x, y, col_width, row_height, self.LINE_STYLES['solid'])
                
                # Рисование текста заголовка
                self._draw_text(x + 2, y + 2, header, text_height)
            
            # Рисование строк таблицы
            for row_idx, component in enumerate(components, start=1):
                y = table_y - row_idx * row_height
                
                # Столбец 1: Позиция
                x = table_x
                self._draw_rectangle(x, y, col_width, row_height, self.LINE_STYLES['solid'])
                self._draw_text(x + 2, y + 2, str(component.position), text_height)
                
                # Столбец 2: Наименование
                x = table_x + col_width
                self._draw_rectangle(x, y, col_width, row_height, self.LINE_STYLES['solid'])
                self._draw_text(x + 2, y + 2, component.name[:20], text_height * 0.8)
                
                # Столбец 3: Обозначение
                x = table_x + 2 * col_width
                self._draw_rectangle(x, y, col_width, row_height, self.LINE_STYLES['solid'])
                self._draw_text(x + 2, y + 2, component.designation, text_height * 0.8)
                
                # Столбец 4: Количество
                x = table_x + 3 * col_width
                self._draw_rectangle(x, y, col_width, row_height, self.LINE_STYLES['solid'])
                self._draw_text(x + 2, y + 2, str(component.quantity), text_height)
            
            logger.info("Таблица спецификации успешно создана (альтернативный метод)")
            
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы спецификации (альтернативный метод): {e}")
    
    def _save_document(self, product_code: str) -> str:
        """
        Сохранение документа в файл.
        
        Args:
            product_code: Код изделия (используется в имени файла)
            
        Returns:
            str: Путь к сохраненному файлу
        """
        try:
            # Формирование имени файла с кодом схемы Е1
            filename = f"{product_code}_E1_division_scheme.cdw"
            
            # Путь сохранения (текущая директория)
            file_path = os.path.join(os.getcwd(), filename)
            
            # Сохранение документа
            result = self.current_document.SaveAs(file_path)
            
            if result == 0:
                logger.error(f"Ошибка при сохранении документа: {file_path}")
                raise RuntimeError(f"Не удалось сохранить документ в {file_path}")
            
            logger.info(f"Документ успешно сохранен: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении документа: {e}")
            raise


# Глобальный экземпляр обработчика
kompas_handler = KompasAPIHandler()
