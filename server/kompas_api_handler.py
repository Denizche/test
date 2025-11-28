"""
Обработчик API КОМПАС-3D для создания схем деления.

Этот модуль содержит класс KompasAPIHandler для управления экземпляром КОМПАС-3D
и выполнения команд через COM-интерфейс для создания схем деления изделий по ГОСТ 2.701.

ТРЕБОВАНИЯ:
- Windows OS
- КОМПАС-3D установлен и доступен
- pywin32 установлен (pip install pywin32)
"""

import os
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import uuid

try:
    import win32com.client
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logging.warning("win32com.client недоступен. Сервер работает в режиме эмуляции.")

from models import CreateDivisionSchemeRequest, Component
from layout_engine import layout_engine
from gost_validator import gost_validator

# Настройка логирования
logger = logging.getLogger(__name__)

# --- КОНСТАНТЫ API КОМПАС-3D ---
ksDocumentDrawing = 1           # Тип документа: Чертеж
ksFormatA3 = 3                  # Формат листа: A3
ksFormatA4 = 4                  # Формат листа: A4
ksFormatA2 = 2                  # Формат листа: A2
ksFormatA1 = 1                  # Формат листа: A1
ksFormatA0 = 0                  # Формат листа: A0

ksLineTypeSolid = 1             # Тип линии: сплошная
ksLineTypeThick = 2             # Тип линии: толстая
ksLineTypeThin = 3              # Тип линии: тонкая

ksOrientationPortrait = 0       # Ориентация: портрет
ksOrientationLandscape = 1      # Ориентация: ландшафт


class KompasAPIHandler:
    """
    Класс для управления экземпляром КОМПАС-3D и выполнения команд через API.
    
    Этот класс обеспечивает подключение к КОМПАС-3D, создание документов,
    черчение схем деления по ГОСТ 2.701 и сохранение результатов.
    """
    
    # Форматы листов по ГОСТ
    FORMAT_MAP = {
        "A0": ksFormatA0,
        "A1": ksFormatA1,
        "A2": ksFormatA2,
        "A3": ksFormatA3,
        "A4": ksFormatA4,
    }
    
    # Ориентация листа
    ORIENTATION_MAP = {
        "portrait": ksOrientationPortrait,
        "landscape": ksOrientationLandscape,
    }
    
    # Стандартные размеры элементов по ГОСТ
    COMPONENT_WIDTH = 60          # Ширина прямоугольника компонента (мм)
    COMPONENT_HEIGHT = 20         # Высота прямоугольника компонента (мм)
    TEXT_HEIGHT_DESIGNATION = 3.5 # Высота текста позиционного обозначения (мм)
    TEXT_HEIGHT_NAME = 2.5        # Высота текста наименования (мм)
    
    def __init__(self):
        """Инициализация обработчика API КОМПАС-3D."""
        self.kompas = None
        self.kompas_api7 = None
        self.connected = False
        self.version = "1.0.0"
        logger.info("KompasAPIHandler инициализирован")

    def connect(self) -> bool:
        """
        Подключение к КОМПАС-3D.
        
        Попытается подключиться к запущенному экземпляру КОМПАС-3D
        или запустить новый экземпляр.
        
        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        if not WINDOWS_AVAILABLE:
            logger.warning("win32com.client недоступен. Работа в режиме эмуляции.")
            self.connected = False
            return False
            
        try:
            # Попытка подключения к запущенному КОМПАС-3D
            self.kompas = win32com.client.Dispatch("Kompas.Application.7")
            self.kompas.Visible = True
            
            # Получение интерфейса API7
            self.kompas_api7 = self.kompas.GetInterface("IKompasAPIObject")
            
            self.connected = True
            logger.info("Успешное подключение к КОМПАС-3D")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к КОМПАС-3D: {e}")
            self.connected = False
            return False

    def get_status(self) -> str:
        """
        Проверка статуса подключения к КОМПАС-3D.
        
        Returns:
            str: "Connected" если подключено, "Disconnected" если нет
        """
        if self.connected and self.kompas:
            try:
                _ = self.kompas.Visible
                logger.debug("Статус подключения: Connected")
                return "Connected"
            except Exception as e:
                logger.error(f"Ошибка проверки статуса: {e}")
                self.connected = False
                return "Disconnected"
        
        logger.debug("Статус подключения: Disconnected")
        return "Disconnected"

    def _draw_rectangle(
        self,
        doc2d,
        x: float,
        y: float,
        width: float,
        height: float,
        line_type: int = ksLineTypeSolid
    ) -> None:
        """
        Рисование прямоугольника на чертеже.
        
        Args:
            doc2d: Интерфейс документа 2D
            x: Координата X левого верхнего угла
            y: Координата Y левого верхнего угла
            width: Ширина прямоугольника
            height: Высота прямоугольника
            line_type: Тип линии
        """
        try:
            if doc2d:
                doc2d.DrawRectangle(x, y, x + width, y - height, line_type)
        except Exception as e:
            logger.warning(f"Ошибка рисования прямоугольника: {e}")

    def _draw_line(
        self,
        doc2d,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        line_type: int = ksLineTypeSolid
    ) -> None:
        """
        Рисование линии на чертеже.
        
        Args:
            doc2d: Интерфейс документа 2D
            x1, y1: Начальные координаты
            x2, y2: Конечные координаты
            line_type: Тип линии
        """
        try:
            if doc2d:
                doc2d.DrawLine(x1, y1, x2, y2, line_type)
        except Exception as e:
            logger.warning(f"Ошибка рисования линии: {e}")

    def _add_text(
        self,
        doc2d,
        x: float,
        y: float,
        text: str,
        height: float = 3.5
    ) -> None:
        """
        Добавление текста на чертеж.
        
        Args:
            doc2d: Интерфейс документа 2D
            x: Координата X
            y: Координата Y
            text: Текст для добавления
            height: Высота текста
        """
        try:
            if doc2d:
                text_style = doc2d.TextStyles.Add()
                text_style.Height = height
                doc2d.Text(x, y, text, text_style)
        except Exception as e:
            logger.warning(f"Ошибка добавления текста: {e}")

    def _draw_division_scheme(
        self,
        doc2d,
        request: CreateDivisionSchemeRequest,
        positions: Dict[int, Tuple[float, float]]
    ) -> None:
        """
        Черчение схемы деления по ГОСТ 2.701.
        
        Args:
            doc2d: Интерфейс документа 2D
            request: Запрос с данными схемы деления
            positions: Словарь позиций компонентов {position: (x, y)}
        """
        logger.info("Выполнение логики черчения схемы деления (ГОСТ 2.701)")
        
        try:
            # Рисование компонентов
            for component in request.components:
                if component.position not in positions:
                    logger.warning(f"Позиция {component.position} не найдена в расчетных позициях")
                    continue
                
                x, y = positions[component.position]
                logger.debug(f"Рисование компонента {component.position} на позицию ({x}, {y})")
                
                # 1. Рисование прямоугольника компонента
                self._draw_rectangle(doc2d, x, y, self.COMPONENT_WIDTH, self.COMPONENT_HEIGHT)
                
                # 2. Добавление позиционного обозначения (номера)
                self._add_text(
                    doc2d,
                    x + 5,
                    y - 5,
                    str(component.position),
                    self.TEXT_HEIGHT_DESIGNATION
                )
                
                # 3. Добавление наименования компонента
                if component.name:
                    self._add_text(
                        doc2d,
                        x + 5,
                        y - 12,
                        component.name[:20],  # Ограничение длины текста
                        self.TEXT_HEIGHT_NAME
                    )
            
            # 4. Рисование связей между компонентами (иерархия)
            self._draw_hierarchy_connections(doc2d, request.components, positions)
            
            logger.info("Черчение схемы деления завершено успешно")
            
        except Exception as e:
            logger.error(f"Ошибка при черчении схемы деления: {e}")
            raise

    def _draw_hierarchy_connections(
        self,
        doc2d,
        components: List[Component],
        positions: Dict[int, Tuple[float, float]]
    ) -> None:
        """
        Рисование линий связи между компонентами (иерархия).
        
        Args:
            doc2d: Интерфейс документа 2D
            components: Список компонентов
            positions: Словарь позиций компонентов
        """
        logger.debug("Рисование иерархических связей между компонентами")
        
        try:
            for component in components:
                if component.parent_position is None:
                    continue
                
                if component.position not in positions or component.parent_position not in positions:
                    logger.warning(f"Не удалось найти позиции для связи {component.parent_position} -> {component.position}")
                    continue
                
                parent_x, parent_y = positions[component.parent_position]
                child_x, child_y = positions[component.position]
                
                # Рисование линии от центра родителя к центру потомка
                parent_center_x = parent_x + self.COMPONENT_WIDTH / 2
                parent_center_y = parent_y - self.COMPONENT_HEIGHT / 2
                
                child_center_x = child_x + self.COMPONENT_WIDTH / 2
                child_center_y = child_y - self.COMPONENT_HEIGHT / 2
                
                logger.debug(f"Связь: компонент {component.parent_position} -> {component.position}")
                self._draw_line(doc2d, parent_center_x, parent_center_y, child_center_x, child_center_y, ksLineTypeThin)
                
        except Exception as e:
            logger.warning(f"Ошибка при рисовании иерархических связей: {e}")

    def _generate_bom(
        self,
        doc2d,
        components: List[Component],
        start_y: float = 200
    ) -> None:
        """
        Генерация спецификации (таблицы компонентов) на чертеже.
        
        Args:
            doc2d: Интерфейс документа 2D
            components: Список компонентов
            start_y: Начальная координата Y для таблицы
        """
        logger.info("Генерация спецификации (BOM)")
        
        try:
            # Заголовки таблицы
            headers = ["Поз.", "Обозначение", "Наименование", "Кол."]
            col_widths = [15, 50, 80, 15]
            
            x = 40
            y = start_y
            
            # Рисование заголовков
            for idx, header in enumerate(headers):
                self._add_text(doc2d, x, y, header, 3.0)
                x += col_widths[idx]
            
            # Рисование строк таблицы
            y -= 10
            for component in sorted(components, key=lambda c: c.position):
                x = 40
                
                # Позиция
                self._add_text(doc2d, x, y, str(component.position), 2.5)
                x += col_widths[0]
                
                # Обозначение
                self._add_text(doc2d, x, y, component.designation, 2.5)
                x += col_widths[1]
                
                # Наименование
                self._add_text(doc2d, x, y, component.name[:30], 2.5)
                x += col_widths[2]
                
                # Количество
                self._add_text(doc2d, x, y, str(component.quantity), 2.5)
                
                y -= 8
            
            logger.info(f"Спецификация сгенерирована для {len(components)} компонентов")
            
        except Exception as e:
            logger.warning(f"Ошибка при генерации спецификации: {e}")

    def create_division_scheme(self, request: CreateDivisionSchemeRequest) -> Dict[str, Any]:
        """
        Основная функция для создания схемы деления изделия по ГОСТ 2.701.
        
        Args:
            request: Объект CreateDivisionSchemeRequest с параметрами схемы
            
        Returns:
            Dict с результатом операции (success, file_path, message)
        """
        logger.info(f"Начало создания схемы деления для изделия '{request.product_name}'")
        
        # Валидация запроса по ГОСТ 2.701
        logger.debug("Валидация запроса по ГОСТ 2.701")
        is_valid, errors, warnings = gost_validator.validate_request(request)
        
        if not is_valid:
            error_msg = "Ошибка валидации по ГОСТ 2.701: " + "; ".join(errors)
            logger.error(error_msg)
            return {
                "success": False,
                "file_path": None,
                "message": "Ошибка валидации",
                "error_details": error_msg
            }
        
        if warnings:
            logger.warning(f"Предупреждения при валидации: {warnings}")
        
        # Расчет позиций компонентов
        logger.debug("Расчет позиций компонентов")
        positions = layout_engine.calculate_positions(
            request.components,
            request.layout_type,
            request.gost_format,
            request.orientation
        )
        
        # Проверка подключения к КОМПАС-3D
        if not self.connect():
            error_msg = "Не удалось подключиться к КОМПАС-3D. Убедитесь, что он установлен и доступен."
            logger.error(error_msg)
            return {
                "success": False,
                "file_path": None,
                "message": error_msg,
                "error_details": "COM-интерфейс КОМПАС-3D недоступен"
            }

        doc = None
        try:
            # 1. Создание нового документа (Чертеж)
            logger.debug("Создание нового документа чертежа")
            documents = self.kompas.Documents
            doc = documents.Add(ksDocumentDrawing)
            
            # Получение интерфейса документа 2D
            doc2d = self.kompas_api7.Document2D(doc) if self.kompas_api7 else None
            
            # 2. Установка формата листа по ГОСТ
            logger.debug(f"Установка формата листа '{request.gost_format}'")
            if doc2d:
                try:
                    layout = doc2d.Layout
                    format_code = self.FORMAT_MAP.get(request.gost_format, ksFormatA3)
                    layout.Format = format_code
                    
                    # Установка ориентации
                    orientation_code = self.ORIENTATION_MAP.get(request.orientation, ksOrientationLandscape)
                    layout.Orientation = orientation_code
                except Exception as e:
                    logger.warning(f"Ошибка установки формата листа: {e}")
            
            # 3. Заполнение основной надписи (штампа)
            logger.debug("Заполнение основной надписи")
            if doc2d:
                try:
                    stamp = doc2d.Stamp
                    if stamp and request.title_block_data:
                        if request.title_block_data.designation:
                            stamp.SetText("Обозначение", request.title_block_data.designation)
                        if request.title_block_data.name:
                            stamp.SetText("Наименование", request.title_block_data.name)
                        if request.title_block_data.developer:
                            stamp.SetText("Разработал", request.title_block_data.developer)
                        if request.title_block_data.checker:
                            stamp.SetText("Проверил", request.title_block_data.checker)
                        if request.title_block_data.approver:
                            stamp.SetText("Утвердил", request.title_block_data.approver)
                except Exception as e:
                    logger.warning(f"Ошибка заполнения штампа: {e}")
            
            # 4. Черчение схемы деления
            logger.debug("Выполнение черчения схемы деления")
            self._draw_division_scheme(doc2d, request, positions)
            
            # 5. Генерация спецификации (если требуется)
            if request.include_bom:
                logger.debug("Генерация спецификации")
                self._generate_bom(doc2d, request.components)
            
            # 6. Сохранение файла
            logger.debug("Сохранение файла чертежа")
            output_dir = request.output_path or "C:\\KOMPAS_OUTPUT"
            
            # Создание директории если её нет
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    logger.debug(f"Создана директория: {output_dir}")
                except Exception as e:
                    logger.error(f"Ошибка создания директории: {e}")
                    output_dir = "."
            
            # Генерация уникального имени файла
            unique_id = uuid.uuid4().hex[:8]
            safe_code = request.product_code.replace(".", "_")
            file_name = f"DivisionScheme_{safe_code}_{unique_id}.cdw"
            file_path = os.path.join(output_dir, file_name)
            
            logger.debug(f"Сохранение файла: {file_path}")
            doc.SaveAs(file_path)
            doc.Close(0)
            
            success_msg = f"Схема деления успешно создана и сохранена: {file_path}"
            logger.info(success_msg)
            
            return {
                "success": True,
                "file_path": file_path,
                "message": success_msg,
                "bom_generated": request.include_bom
            }

        except Exception as e:
            error_msg = f"Ошибка при создании схемы деления: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Попытка закрыть документ при ошибке
            try:
                if doc:
                    doc.Close(0)
            except Exception as close_error:
                logger.warning(f"Ошибка закрытия документа: {close_error}")
            
            return {
                "success": False,
                "file_path": None,
                "message": "Ошибка при создании схемы деления",
                "error_details": error_msg
            }
        
        finally:
            logger.debug("Завершение операции создания схемы деления")


# Глобальный экземпляр обработчика
kompas_handler = KompasAPIHandler()
