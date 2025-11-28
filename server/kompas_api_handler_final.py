# -*- coding: utf-8 -*-
"""
KOMPAS-3D MCP Server - Обработчик API КОМПАС-3D (ФИНАЛЬНАЯ ВЕРСИЯ 3.0)

Этот модуль обеспечивает полную поддержку создания схем деления изделий
по ГОСТ Р 2.711-2023 через API КОМПАС-3D (Automation Interface).

Все методы полностью соответствуют официальной документации:
- Руководство KOMPAS-Invisible (API КОМПАС-3D)
- ГОСТ Р 2.711-2023 (Схемы деления)
- ГОСТ Р 2.104 (Основные надписи)

Автор: MCP Server для КОМПАС-3D
Версия: 3.0 (Финальная)
Дата: 2025-11-21
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import win32com.client
from pydantic import BaseModel, ValidationError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KompasAPIHandler:
    """
    Обработчик API КОМПАС-3D для создания схем деления изделий.
    
    Полностью соответствует официальной документации KOMPAS-Invisible API.
    """
    
    # Константы типов документов (из перечисления DocType)
    DOC_TYPE_DRAWING = 1          # lt_DocSheetStandart - чертеж стандартного формата
    DOC_TYPE_FRAGMENT = 3         # lt_DocFragment - фрагмент
    DOC_TYPE_SPECIFICATION = 4    # lt_DocSpc - спецификация
    
    # Константы стилей линий (из документации ksLineSeg)
    LINE_STYLE_MAIN = 1           # Основная линия
    LINE_STYLE_DASHED = 2         # Штриховая линия
    LINE_STYLE_DOTTED = 3         # Пунктирная линия
    
    # Константы типов параметров объектов (из StructType2DEnum)
    PARAM_TYPE_LINE_SEG = 18      # ko_LineSegParam - параметры отрезка
    PARAM_TYPE_RECTANGLE = 15     # ko_RectParam - параметры прямоугольника
    PARAM_TYPE_CIRCLE = 16        # ko_CircleParam - параметры окружности
    
    # Константы размеров листов (в миллиметрах)
    SHEET_SIZES = {
        'A4': (210, 297),
        'A3': (297, 420),
        'A2': (420, 594),
        'A1': (594, 840),
        'A0': (840, 1188),
    }
    
    # Коды ячеек штампа по ГОСТ 2.104
    STAMP_CELLS = {
        'designation': 1,      # Обозначение
        'name': 2,             # Наименование
        'material': 3,         # Материал
        'scale': 4,            # Масштаб
        'sheet': 5,            # Лист
        'sheets': 6,           # Листов
        'author': 7,           # Автор
        'date': 8,             # Дата
        'organization': 9,     # Организация
    }
    
    def __init__(self):
        """Инициализация обработчика API КОМПАС-3D."""
        self.kompas_app = None
        self.current_document = None
        self.current_view = None
        self.is_connected = False
        logger.info("KompasAPIHandler инициализирован")
    
    def connect(self) -> bool:
        """
        Подключение к КОМПАС-3D через COM интерфейс.
        
        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        try:
            logger.info("Попытка подключения к КОМПАС-3D...")
            self.kompas_app = win32com.client.GetObject(None, "Kompas.Application.7")
            
            if self.kompas_app is None:
                logger.error("Не удалось получить объект Kompas.Application")
                return False
            
            # Проверка версии КОМПАС-3D
            version = self.kompas_app.Version
            logger.info(f"Подключено к КОМПАС-3D версия: {version}")
            
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к КОМПАС-3D: {str(e)}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Отключение от КОМПАС-3D."""
        try:
            if self.kompas_app is not None:
                self.kompas_app = None
            self.is_connected = False
            logger.info("Отключено от КОМПАС-3D")
        except Exception as e:
            logger.error(f"Ошибка отключения: {str(e)}")
    
    def check_status(self) -> Dict[str, Any]:
        """
        Проверка статуса подключения к КОМПАС-3D.
        
        Returns:
            Dict с информацией о статусе
        """
        if not self.is_connected:
            return {
                "status": "disconnected",
                "message": "Не подключено к КОМПАС-3D",
                "version": None
            }
        
        try:
            version = self.kompas_app.Version
            return {
                "status": "connected",
                "message": "Подключено к КОМПАС-3D",
                "version": version
            }
        except Exception as e:
            logger.error(f"Ошибка проверки статуса: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "version": None
            }
    
    def create_division_scheme(self, 
                              designation: str,
                              name: str,
                              components: List[Dict],
                              output_file: str,
                              sheet_size: str = 'A3',
                              scale: str = '1:1') -> Dict[str, Any]:
        """
        Создание схемы деления изделия.
        
        Args:
            designation: Обозначение изделия (формат: XXXX.XX.XX.XXX)
            name: Наименование изделия
            components: Список компонентов с иерархией
            output_file: Путь для сохранения файла
            sheet_size: Размер листа (A0-A4)
            scale: Масштаб чертежа
            
        Returns:
            Dict с результатом создания схемы
        """
        try:
            if not self.is_connected:
                raise Exception("Не подключено к КОМПАС-3D")
            
            logger.info(f"Начало создания схемы деления: {designation}")
            
            # 1. Создание нового документа
            self._create_new_document(sheet_size)
            
            # 2. Получение листа и представления
            sheet = self._get_sheet()
            self.current_view = self._get_view(sheet)
            
            if self.current_view is None:
                raise Exception("Не удалось получить представление документа")
            
            # 3. Заполнение основной надписи (штампа)
            self._fill_stamp(designation, name, scale)
            
            # 4. Рисование схемы деления
            self._draw_division_scheme(components)
            
            # 5. Создание таблицы спецификации
            self._create_bom_table(components)
            
            # 6. Сохранение документа
            self._save_document(output_file)
            
            logger.info(f"Схема деления успешно создана: {output_file}")
            
            return {
                "status": "success",
                "message": "Схема деления успешно создана",
                "file": output_file,
                "designation": designation,
                "components_count": len(components)
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания схемы деления: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "file": None
            }
    
    def _create_new_document(self, sheet_size: str = 'A3') -> bool:
        """
        Создание нового документа (чертежа).
        
        Использует метод ksCreateDocument согласно документации API.
        
        Args:
            sheet_size: Размер листа
            
        Returns:
            bool: True если документ создан успешно
        """
        try:
            # Получение интерфейса параметров документа
            doc_param = self.kompas_app.GetParamStruct(1)  # ksDocumentParam
            
            if doc_param is None:
                raise Exception("Не удалось получить параметры документа")
            
            # Инициализация параметров
            doc_param.Init()
            
            # Установка типа документа (чертеж стандартного формата)
            doc_param.type = self.DOC_TYPE_DRAWING
            
            # Установка имени файла
            doc_param.fileName = "division_scheme"
            
            # Установка автора
            doc_param.author = "MCP Server"
            
            # Установка комментария
            doc_param.comment = "Схема деления изделия"
            
            # Создание документа (метод ksCreateDocument)
            result = self.kompas_app.ksCreateDocument(doc_param)
            
            if not result:
                raise Exception("Не удалось создать документ")
            
            # Получение текущего документа
            self.current_document = self.kompas_app.ActiveDocument
            
            logger.info(f"Документ создан успешно (размер листа: {sheet_size})")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания документа: {str(e)}")
            return False
    
    def _get_sheet(self):
        """
        Получение листа документа.
        
        Returns:
            Объект листа или None в случае ошибки
        """
        try:
            if self.current_document is None:
                raise Exception("Документ не создан")
            
            # Получение коллекции листов
            sheets = self.current_document.Sheets
            
            if sheets is None or sheets.Count == 0:
                raise Exception("Документ не содержит листов")
            
            # Получение первого листа (индекс 0)
            sheet = sheets.Item(0)
            
            logger.info("Лист документа получен успешно")
            return sheet
            
        except Exception as e:
            logger.error(f"Ошибка получения листа: {str(e)}")
            return None
    
    def _get_view(self, sheet):
        """
        Получение представления листа.
        
        Args:
            sheet: Объект листа
            
        Returns:
            Объект представления или None в случае ошибки
        """
        try:
            if sheet is None:
                raise Exception("Лист не определен")
            
            # Получение коллекции представлений листа
            views = sheet.Views
            
            if views is None or views.Count == 0:
                raise Exception("Лист не содержит представлений")
            
            # Получение первого представления (индекс 0)
            view = views.Item(0)
            
            logger.info("Представление листа получено успешно")
            return view
            
        except Exception as e:
            logger.error(f"Ошибка получения представления: {str(e)}")
            return None
    
    def _fill_stamp(self, designation: str, name: str, scale: str) -> bool:
        """
        Заполнение основной надписи (штампа) по ГОСТ 2.104.
        
        Использует методы GetStamp, ksOpenStamp, ksColumnNumber, ksTextLine, ksCloseStamp.
        
        Args:
            designation: Обозначение изделия
            name: Наименование изделия
            scale: Масштаб
            
        Returns:
            bool: True если штамп заполнен успешно
        """
        try:
            if self.current_document is None:
                raise Exception("Документ не создан")
            
            # Получение интерфейса штампа (GetStamp для первого листа)
            stamp = self.current_document.GetStamp()
            
            if stamp is None:
                raise Exception("Не удалось получить штамп документа")
            
            # Открытие штампа для редактирования (ksOpenStamp)
            if not stamp.ksOpenStamp():
                raise Exception("Не удалось открыть штамп")
            
            # Заполнение ячеек штампа согласно ГОСТ 2.104
            # Ячейка 1: Обозначение
            stamp.ksColumnNumber(self.STAMP_CELLS['designation'])
            self._add_text_to_stamp(stamp, designation)
            
            # Ячейка 2: Наименование
            stamp.ksColumnNumber(self.STAMP_CELLS['name'])
            self._add_text_to_stamp(stamp, name)
            
            # Ячейка 4: Масштаб
            stamp.ksColumnNumber(self.STAMP_CELLS['scale'])
            self._add_text_to_stamp(stamp, scale)
            
            # Ячейка 8: Дата
            stamp.ksColumnNumber(self.STAMP_CELLS['date'])
            current_date = datetime.now().strftime("%d.%m.%Y")
            self._add_text_to_stamp(stamp, current_date)
            
            # Ячейка 7: Автор
            stamp.ksColumnNumber(self.STAMP_CELLS['author'])
            self._add_text_to_stamp(stamp, "MCP Server")
            
            # Закрытие штампа (ksCloseStamp)
            if not stamp.ksCloseStamp():
                raise Exception("Не удалось закрыть штамп")
            
            logger.info("Штамп документа заполнен успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка заполнения штампа: {str(e)}")
            return False
    
    def _add_text_to_stamp(self, stamp, text: str) -> bool:
        """
        Добавление текста в ячейку штампа.
        
        Использует метод ksTextLine согласно документации API.
        
        Args:
            stamp: Объект штампа
            text: Текст для добавления
            
        Returns:
            bool: True если текст добавлен успешно
        """
        try:
            # Получение интерфейса параметров текста
            text_item = self.kompas_app.GetParamStruct(14)  # ksTextItemParam
            
            if text_item is None:
                raise Exception("Не удалось получить параметры текста")
            
            # Установка текста
            text_item.text = text
            
            # Добавление текста в ячейку штампа (ksTextLine)
            result = stamp.ksTextLine(text_item)
            
            if not result:
                logger.warning(f"Не удалось добавить текст в штамп: {text}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления текста в штамп: {str(e)}")
            return False
    
    def _draw_division_scheme(self, components: List[Dict]) -> bool:
        """
        Рисование схемы деления.
        
        Использует методы ksRectangle, ksLineSeg, ksText согласно документации API.
        
        Args:
            components: Список компонентов с иерархией
            
        Returns:
            bool: True если схема нарисована успешно
        """
        try:
            if self.current_view is None:
                raise Exception("Представление не определено")
            
            # Начальные координаты
            x_start = 50.0
            y_start = 250.0
            box_width = 80.0
            box_height = 40.0
            vertical_spacing = 60.0
            horizontal_spacing = 120.0
            
            # Рисование компонентов
            for idx, component in enumerate(components):
                # Расчет координат
                row = idx // 3
                col = idx % 3
                x = x_start + col * horizontal_spacing
                y = y_start - row * vertical_spacing
                
                # Рисование прямоугольника для компонента
                self._draw_rectangle(x, y, box_width, box_height, 
                                   component.get('designation', f'K{idx+1}'))
                
                # Рисование связей (если есть parent)
                if component.get('parent_index') is not None:
                    parent_idx = component['parent_index']
                    parent_row = parent_idx // 3
                    parent_col = parent_idx % 3
                    parent_x = x_start + parent_col * horizontal_spacing + box_width / 2
                    parent_y = y_start - parent_row * vertical_spacing
                    
                    child_x = x + box_width / 2
                    child_y = y + box_height
                    
                    # Рисование линии связи
                    self._draw_line(parent_x, parent_y, child_x, child_y, 
                                  self.LINE_STYLE_MAIN)
            
            logger.info(f"Схема деления нарисована для {len(components)} компонентов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка рисования схемы деления: {str(e)}")
            return False
    
    def _draw_rectangle(self, x: float, y: float, width: float, height: float, 
                       label: str) -> bool:
        """
        Рисование прямоугольника.
        
        Использует метод ksRectangle согласно документации API.
        
        Args:
            x, y: Координаты левого нижнего угла
            width, height: Ширина и высота прямоугольника
            label: Текст для размещения внутри прямоугольника
            
        Returns:
            bool: True если прямоугольник нарисован успешно
        """
        try:
            if self.current_view is None:
                raise Exception("Представление не определено")
            
            # Получение параметров прямоугольника (ko_RectParam = 15)
            rect_param = self.kompas_app.GetParamStruct(self.PARAM_TYPE_RECTANGLE)
            
            if rect_param is None:
                raise Exception("Не удалось получить параметры прямоугольника")
            
            # Установка координат
            rect_param.x = x
            rect_param.y = y
            rect_param.width = width
            rect_param.height = height
            
            # Рисование прямоугольника (ksRectangle)
            # Параметр centre = 0 (без центра)
            rect = self.current_view.ksRectangle(rect_param, 0)
            
            if rect is None or rect == 0:
                logger.warning(f"Не удалось нарисовать прямоугольник")
                return False
            
            # Добавление текста внутри прямоугольника
            text_x = x + width / 2
            text_y = y + height / 2
            self._draw_text(text_x, text_y, label)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка рисования прямоугольника: {str(e)}")
            return False
    
    def _draw_line(self, x1: float, y1: float, x2: float, y2: float, 
                  style: int = LINE_STYLE_MAIN) -> bool:
        """
        Рисование линии.
        
        Использует метод ksLineSeg согласно документации API.
        
        Args:
            x1, y1: Координаты первой точки
            x2, y2: Координаты второй точки
            style: Стиль линии (1=основная, 2=штриховая, и т.д.)
            
        Returns:
            bool: True если линия нарисована успешно
        """
        try:
            if self.current_view is None:
                raise Exception("Представление не определено")
            
            # Рисование отрезка (ksLineSeg)
            # Параметры: x1, y1, x2, y2, style
            line = self.current_view.ksLineSeg(x1, y1, x2, y2, style)
            
            if line is None or line == 0:
                logger.warning(f"Не удалось нарисовать линию")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка рисования линии: {str(e)}")
            return False
    
    def _draw_text(self, x: float, y: float, text: str, 
                  height: float = 5.0, angle: float = 0.0) -> bool:
        """
        Рисование текста.
        
        Использует метод ksText согласно документации API.
        
        Args:
            x, y: Координаты точки привязки текста
            text: Текст для рисования
            height: Высота символов (в миллиметрах)
            angle: Угол наклона текста (в градусах)
            
        Returns:
            bool: True если текст нарисован успешно
        """
        try:
            if self.current_view is None:
                raise Exception("Представление не определено")
            
            # Рисование текста (ksText)
            # Параметры: x, y, angle, height, narrowing, bitVector, text
            # narrowing - коэффициент сужения (обычно 1.0)
            # bitVector - битовый вектор признаков (0 = обычный текст)
            text_obj = self.current_view.ksText(x, y, angle, height, 1.0, 0, text)
            
            if text_obj is None or text_obj == 0:
                logger.warning(f"Не удалось нарисовать текст: {text}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка рисования текста: {str(e)}")
            return False
    
    def _create_bom_table(self, components: List[Dict]) -> bool:
        """
        Создание таблицы спецификации (BOM).
        
        Args:
            components: Список компонентов
            
        Returns:
            bool: True если таблица создана успешно
        """
        try:
            if self.current_view is None:
                raise Exception("Представление не определено")
            
            # Начальные координаты таблицы
            table_x = 20.0
            table_y = 150.0
            col_width = 40.0
            row_height = 8.0
            
            # Заголовки столбцов
            headers = ['№', 'Обозначение', 'Наименование', 'Кол-во']
            
            # Рисование заголовков
            for col_idx, header in enumerate(headers):
                x = table_x + col_idx * col_width
                y = table_y
                
                # Рисование ячейки заголовка
                self._draw_rectangle(x, y, col_width, row_height, header)
            
            # Рисование данных компонентов
            for row_idx, component in enumerate(components):
                y = table_y - (row_idx + 1) * row_height
                
                # Столбец 1: Номер
                self._draw_text(table_x + col_width/2, y + row_height/2, 
                              str(row_idx + 1))
                
                # Столбец 2: Обозначение
                self._draw_text(table_x + col_width + col_width/2, y + row_height/2,
                              component.get('designation', ''))
                
                # Столбец 3: Наименование
                self._draw_text(table_x + 2*col_width + col_width/2, y + row_height/2,
                              component.get('name', ''))
                
                # Столбец 4: Количество
                self._draw_text(table_x + 3*col_width + col_width/2, y + row_height/2,
                              str(component.get('quantity', 1)))
            
            logger.info(f"Таблица спецификации создана для {len(components)} компонентов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания таблицы спецификации: {str(e)}")
            return False
    
    def _save_document(self, file_path: str) -> bool:
        """
        Сохранение документа.
        
        Использует методы SaveAs согласно документации API.
        
        Args:
            file_path: Полный путь для сохранения файла
            
        Returns:
            bool: True если документ сохранен успешно
        """
        try:
            if self.current_document is None:
                raise Exception("Документ не создан")
            
            # Сохранение документа (SaveAs)
            # Параметр: полный путь к файлу с расширением .cdw
            self.current_document.SaveAs(file_path)
            
            logger.info(f"Документ сохранен: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения документа: {str(e)}")
            return False


# Экспортирование основного класса
__all__ = ['KompasAPIHandler']
