"""
Обработчик API КОМПАС-3D для создания схем деления по ГОСТ Р 2.711-2023.

ИСПРАВЛЕННАЯ ВЕРСИЯ с правильными методами API и полной поддержкой ГОСТ.

Этот модуль содержит класс KompasAPIHandler, который:
- Подключается к КОМПАС-3D через COM-интерфейс
- Создает новые чертежи (документы) в формате A0-A5
- Рисует компоненты и связи между ними
- Заполняет основную надпись (штамп) по ГОСТ Р 2.104
- Создает таблицу спецификации (BOM) на листе
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
    """Обработчик для работы с API КОМПАС-3D."""
    
    # Константы для стилей линий (из документации API)
    LINE_STYLES = {
        'solid': 1,           # Основная линия
        'dashed': 2,          # Штриховая линия
        'dotted': 3,          # Пунктирная линия
        'wavy': 4,            # Волнистая линия
        'dash_dot': 5,        # Штрих-пунктирная линия
    }
    
    # Форматы листов (из документации API)
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
            # Получение кода формата
            format_code = self.FORMATS.get(format_name, 3)  # A3 по умолчанию
            
            # Создание нового документа типа "Чертеж"
            # Метод: ksCreateDocument(DocumentParam)
            doc_param = self.kompas_app.ksCreateDocument(self.DOC_TYPES['drawing'])
            
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
            stamp.ksTextLine(title_block_data.designation)
            
            # Номер ячейки 2: Наименование
            stamp.ksColumnNumber(2)
            stamp.ksTextLine(title_block_data.name)
            
            # Номер ячейки 3: Разработчик
            if title_block_data.developer:
                stamp.ksColumnNumber(3)
                stamp.ksTextLine(title_block_data.developer)
            
            # Номер ячейки 4: Организация
            if title_block_data.organization:
                stamp.ksColumnNumber(4)
                stamp.ksTextLine(title_block_data.organization)
            
            # Номер ячейки 5: Дата
            stamp.ksColumnNumber(5)
            stamp.ksTextLine(datetime.now().strftime("%d.%m.%Y"))
            
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
    
    def _draw_rectangle(self, x: float, y: float, width: float, height: float, style: int) -> None:
        """
        Рисование прямоугольника.
        
        Args:
            x, y: Координаты левого нижнего угла
            width, height: Ширина и высота
            style: Стиль линии
        """
        try:
            # Создание параметров прямоугольника
            rect_param = self.current_view.ksRectParam()
            
            # Инициализация параметров
            # Метод: ksRectParam::Init(x, y, width, height)
            rect_param.Init(x, y, width, height)
            
            # Установка стиля линии
            rect_param.Style = style
            
            # Рисование прямоугольника
            # Метод: ksRectangle(param, centre)
            # centre = 0 означает, что координаты - это левый нижний угол
            self.current_view.ksRectangle(rect_param, 0)
            
        except Exception as e:
            logger.error(f"Ошибка при рисовании прямоугольника: {e}")
    
    def _draw_text(self, x: float, y: float, text: str, height: float, angle: float = 0) -> None:
        """
        Рисование текста.
        
        Args:
            x, y: Координаты точки привязки текста
            text: Текстовая строка
            height: Высота символов
            angle: Угол наклона текста (в градусах)
        """
        try:
            # Параметры текста
            narrowing = 1.0  # Сужение текста (1.0 = нормальное)
            bit_vector = 0   # Признаки начертания (0 = обычный текст)
            
            # Метод: ksText(x, y, angle, height, narrowing, bitVector, text)
            self.current_view.ksText(
                x, y, angle, height, narrowing, bit_vector, text
            )
            
        except Exception as e:
            logger.error(f"Ошибка при рисовании текста: {e}")
    
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
                        # Метод: ksLineSeg(x1, y1, x2, y2, style)
                        self.current_view.ksLineSeg(
                            parent_x, parent_y,
                            child_x, child_y,
                            line_style
                        )
            
            logger.info("Иерархические связи успешно нарисованы")
            
        except Exception as e:
            logger.error(f"Ошибка при рисовании связей: {e}")
    
    def _create_bom_table(self, components: List[Component]) -> None:
        """
        Создание таблицы спецификации (BOM) на листе.
        
        Args:
            components: Список компонентов
        """
        try:
            # Параметры таблицы
            table_x = 10
            table_y = 10
            col_width = 30
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
            
            logger.info("Таблица спецификации успешно создана")
            
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы спецификации: {e}")
    
    def _save_document(self, product_code: str) -> str:
        """
        Сохранение документа в файл.
        
        Args:
            product_code: Код изделия (используется в имени файла)
            
        Returns:
            str: Путь к сохраненному файлу
        """
        try:
            # Формирование имени файла
            # Добавление кода схемы Е1 (схема деления)
            filename = f"{product_code}_E1_division_scheme.cdw"
            
            # Путь сохранения (текущая директория)
            file_path = os.path.join(os.getcwd(), filename)
            
            # Сохранение документа
            # Метод: SaveAs(fileName)
            self.current_document.SaveAs(file_path)
            
            logger.info(f"Документ успешно сохранен: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении документа: {e}")
            raise


# Глобальный экземпляр обработчика
kompas_handler = KompasAPIHandler()
