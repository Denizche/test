"""
Модуль для рисования примитивов в КОМПАС-3D.

Содержит методы для рисования:
- Окружностей (circles)
- Дуг (arcs)
- Полилиний (polylines)
- Эллипсов (ellipses)
- Скругленных прямоугольников (rounded rectangles)

Все методы используют правильный API КОМПАС-3D через GetParamStruct().
"""

import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class DrawingPrimitives:
    """Класс для рисования примитивов в КОМПАС-3D."""
    
    # Коды типов параметров для GetParamStruct()
    PARAM_TYPES = {
        'line_seg': 11,
        'math_point': 14,
        'rect': 15,
        'circle': 20,
        'arc': 21,
        'ellipse': 22,
        'polyline': 23,
    }
    
    def __init__(self, kompas_object, current_view):
        """
        Инициализация примитивов.
        
        Args:
            kompas_object: Интерфейс KompasObject для создания параметров
            current_view: Представление (View) для рисования
        """
        self.kompas_object = kompas_object
        self.current_view = current_view
    
    def draw_circle(self, x: float, y: float, radius: float, style: int = 1) -> bool:
        """
        Рисование окружности.
        
        Args:
            x, y: Координаты центра
            radius: Радиус окружности
            style: Стиль линии (1=основная, 2=штриховая, 3=пунктирная, и т.д.)
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Создание параметров окружности (код 20 = ko_CircleParam)
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
            
            logger.debug(f"Окружность успешно нарисована: ({x}, {y}), r={radius}")
            return True
            
        except Exception as e:
            logger.error(f"Исключение при рисовании окружности: {e}")
            return False
    
    def draw_arc(
        self,
        xc: float,
        yc: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        style: int = 1
    ) -> bool:
        """
        Рисование дуги.
        
        Args:
            xc, yc: Координаты центра дуги
            x1, y1: Координаты начальной точки дуги
            x2, y2: Координаты конечной точки дуги
            style: Стиль линии
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Создание параметров дуги (код 21 = ko_ArcParam)
            arc_param = self.kompas_object.GetParamStruct(self.PARAM_TYPES['arc'])
            
            # Установка центра дуги
            arc_param.xc = xc
            arc_param.yc = yc
            
            # Установка начальной точки
            arc_param.x1 = x1
            arc_param.y1 = y1
            
            # Установка конечной точки
            arc_param.x2 = x2
            arc_param.y2 = y2
            
            # Установка стиля линии
            arc_param.style = style
            
            # Рисование дуги
            result = self.current_view.ksArc(arc_param)
            
            if result == 0:
                logger.error(f"Ошибка при рисовании дуги: центр=({xc}, {yc}), от ({x1}, {y1}) к ({x2}, {y2})")
                return False
            
            logger.debug(f"Дуга успешно нарисована: центр=({xc}, {yc})")
            return True
            
        except Exception as e:
            logger.error(f"Исключение при рисовании дуги: {e}")
            return False
    
    def draw_ellipse(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        style: int = 1
    ) -> bool:
        """
        Рисование эллипса.
        
        Args:
            x, y: Координаты левого нижнего угла ограничивающего прямоугольника
            width: Ширина эллипса
            height: Высота эллипса
            style: Стиль линии
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Создание параметров эллипса (код 22 = примерный)
            ellipse_param = self.kompas_object.GetParamStruct(self.PARAM_TYPES['ellipse'])
            
            # Получение точек диагонали ограничивающего прямоугольника
            p_bot = ellipse_param.GetpBot()
            p_top = ellipse_param.GetpTop()
            
            # Установка координат левой нижней точки
            p_bot.x = x
            p_bot.y = y
            
            # Установка координат правой верхней точки
            p_top.x = x + width
            p_top.y = y + height
            
            # Установка стиля линии
            ellipse_param.style = style
            
            # Рисование эллипса
            result = self.current_view.ksEllipse(ellipse_param)
            
            if result == 0:
                logger.error(f"Ошибка при рисовании эллипса: ({x}, {y}), размер={width}x{height}")
                return False
            
            logger.debug(f"Эллипс успешно нарисован: ({x}, {y}), размер={width}x{height}")
            return True
            
        except Exception as e:
            logger.error(f"Исключение при рисовании эллипса: {e}")
            return False
    
    def draw_polyline(
        self,
        points: List[Tuple[float, float]],
        style: int = 1,
        closed: bool = False
    ) -> bool:
        """
        Рисование полилинии (ломаной линии).
        
        Args:
            points: Список точек (x, y)
            style: Стиль линии
            closed: Замкнутая ли полилиния
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            if len(points) < 2:
                logger.error("Полилиния должна содержать минимум 2 точки")
                return False
            
            # Создание параметров полилинии (код 23 = примерный)
            polyline_param = self.kompas_object.GetParamStruct(self.PARAM_TYPES['polyline'])
            
            # Установка количества точек
            polyline_param.count = len(points)
            
            # Установка стиля линии
            polyline_param.style = style
            
            # Установка флага замкнутости
            if closed:
                polyline_param.closed = True
            
            # Добавление точек в полилинию
            for idx, (x, y) in enumerate(points):
                # Получение точки из параметров
                point = polyline_param.GetPoint(idx)
                point.x = x
                point.y = y
            
            # Рисование полилинии
            result = self.current_view.ksPolyline(polyline_param)
            
            if result == 0:
                logger.error(f"Ошибка при рисовании полилинии с {len(points)} точками")
                return False
            
            logger.debug(f"Полилиния успешно нарисована: {len(points)} точек")
            return True
            
        except Exception as e:
            logger.error(f"Исключение при рисовании полилинии: {e}")
            return False
    
    def draw_rounded_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float,
        style: int = 1
    ) -> bool:
        """
        Рисование скругленного прямоугольника.
        
        Args:
            x, y: Координаты левого нижнего угла
            width, height: Ширина и высота
            radius: Радиус скругления углов
            style: Стиль линии
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Рисование основного прямоугольника
            rect_param = self.kompas_object.GetParamStruct(self.PARAM_TYPES['rect'])
            
            p_bot = rect_param.GetpBot()
            p_top = rect_param.GetpTop()
            
            p_bot.x = x + radius
            p_bot.y = y
            
            p_top.x = x + width - radius
            p_top.y = y + height
            
            rect_param.style = style
            
            result = self.current_view.ksRectangle(rect_param, 0)
            if result == 0:
                logger.warning("Ошибка при рисовании основного прямоугольника")
            
            # Рисование вертикальных линий
            self.current_view.ksLineSeg(x, y + radius, x, y + height - radius, style)
            self.current_view.ksLineSeg(x + width, y + radius, x + width, y + height - radius, style)
            
            # Рисование дуг в углах
            # Левый нижний угол
            self.draw_arc(x + radius, y + radius, x + radius, y, x, y + radius, style)
            
            # Правый нижний угол
            self.draw_arc(x + width - radius, y + radius, x + width, y + radius, x + width - radius, y, style)
            
            # Левый верхний угол
            self.draw_arc(x + radius, y + height - radius, x, y + height - radius, x + radius, y + height, style)
            
            # Правый верхний угол
            self.draw_arc(x + width - radius, y + height - radius, x + width - radius, y + height, x + width, y + height - radius, style)
            
            logger.debug(f"Скругленный прямоугольник успешно нарисован: ({x}, {y}), размер={width}x{height}, r={radius}")
            return True
            
        except Exception as e:
            logger.error(f"Исключение при рисовании скругленного прямоугольника: {e}")
            return False
    
    def draw_arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        arrow_size: float = 5,
        style: int = 1
    ) -> bool:
        """
        Рисование стрелки (линия с наконечником).
        
        Args:
            x1, y1: Координаты начала стрелки
            x2, y2: Координаты конца стрелки
            arrow_size: Размер наконечника
            style: Стиль линии
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            import math
            
            # Рисование основной линии
            result = self.current_view.ksLineSeg(x1, y1, x2, y2, style)
            if result == 0:
                logger.warning("Ошибка при рисовании линии стрелки")
            
            # Расчет угла стрелки
            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx*dx + dy*dy)
            
            if length == 0:
                logger.warning("Стрелка имеет нулевую длину")
                return False
            
            # Нормализация направления
            dx /= length
            dy /= length
            
            # Расчет точек наконечника
            angle = math.pi / 6  # 30 градусов
            
            # Левая точка наконечника
            x_left = x2 - arrow_size * (dx * math.cos(angle) + dy * math.sin(angle))
            y_left = y2 - arrow_size * (dy * math.cos(angle) - dx * math.sin(angle))
            
            # Правая точка наконечника
            x_right = x2 - arrow_size * (dx * math.cos(angle) - dy * math.sin(angle))
            y_right = y2 - arrow_size * (dy * math.cos(angle) + dx * math.sin(angle))
            
            # Рисование наконечника
            self.current_view.ksLineSeg(x2, y2, x_left, y_left, style)
            self.current_view.ksLineSeg(x2, y2, x_right, y_right, style)
            
            logger.debug(f"Стрелка успешно нарисована: от ({x1}, {y1}) к ({x2}, {y2})")
            return True
            
        except Exception as e:
            logger.error(f"Исключение при рисовании стрелки: {e}")
            return False
    
    def draw_grid(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        grid_size: float,
        style: int = 3  # Пунктирная линия
    ) -> bool:
        """
        Рисование сетки.
        
        Args:
            x, y: Координаты левого нижнего угла
            width, height: Ширина и высота сетки
            grid_size: Размер ячейки сетки
            style: Стиль линии
            
        Returns:
            bool: True если успешно, False иначе
        """
        try:
            # Вертикальные линии
            x_pos = x
            while x_pos <= x + width:
                self.current_view.ksLineSeg(x_pos, y, x_pos, y + height, style)
                x_pos += grid_size
            
            # Горизонтальные линии
            y_pos = y
            while y_pos <= y + height:
                self.current_view.ksLineSeg(x, y_pos, x + width, y_pos, style)
                y_pos += grid_size
            
            logger.debug(f"Сетка успешно нарисована: ({x}, {y}), размер={width}x{height}, ячейка={grid_size}")
            return True
            
        except Exception as e:
            logger.error(f"Исключение при рисовании сетки: {e}")
            return False
