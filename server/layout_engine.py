"""
Движок размещения компонентов для схем деления.

Этот модуль содержит класс LayoutEngine для автоматического расчета позиций
компонентов на чертеже в зависимости от выбранного типа размещения
(древовидная, вертикальная, горизонтальная).
"""

import logging
from typing import Dict, List, Tuple, Optional
from models import Component

logger = logging.getLogger(__name__)


class LayoutEngine:
    """
    Движок для автоматического размещения компонентов на схеме деления.
    
    Поддерживает три типа размещения:
    - tree: Древовидная структура с иерархией
    - vertical: Вертикальное размещение в столбец
    - horizontal: Горизонтальное размещение в строку
    """
    
    # Стандартные размеры элементов по ГОСТ
    COMPONENT_WIDTH = 60      # Ширина прямоугольника компонента (мм)
    COMPONENT_HEIGHT = 20     # Высота прямоугольника компонента (мм)
    
    # Расстояния между элементами
    HORIZONTAL_SPACING = 20   # Горизонтальное расстояние между элементами (мм)
    VERTICAL_SPACING = 40     # Вертикальное расстояние между элементами (мм)
    LEVEL_SPACING = 80        # Расстояние между уровнями иерархии (мм)
    
    # Отступы от краев листа
    MARGIN_TOP = 40           # Отступ сверху (мм)
    MARGIN_LEFT = 40          # Отступ слева (мм)
    MARGIN_RIGHT = 40         # Отступ справа (мм)
    MARGIN_BOTTOM = 40        # Отступ снизу (мм)
    
    # Размеры листов по ГОСТ (мм)
    PAGE_SIZES = {
        "A0": (1189, 841),
        "A1": (841, 594),
        "A2": (594, 420),
        "A3": (420, 297),
        "A4": (297, 210),
    }
    
    def __init__(self):
        """Инициализация движка размещения."""
        logger.info("LayoutEngine инициализирован")
    
    def calculate_positions(
        self,
        components: List[Component],
        layout_type: str = "tree",
        page_format: str = "A3",
        orientation: str = "landscape"
    ) -> Dict[int, Tuple[float, float]]:
        """
        Расчет позиций компонентов на листе.
        
        Args:
            components: Список компонентов для размещения
            layout_type: Тип размещения (tree, vertical, horizontal)
            page_format: Формат листа (A0-A4)
            orientation: Ориентация листа (portrait, landscape)
            
        Returns:
            Dict[int, Tuple[float, float]]: Словарь {position: (x, y)}
        """
        logger.info(f"Расчет позиций для {len(components)} компонентов, тип: {layout_type}")
        
        # Получение размеров листа
        page_width, page_height = self._get_page_size(page_format, orientation)
        logger.debug(f"Размер листа: {page_width}x{page_height} мм")
        
        # Выбор метода размещения
        if layout_type == "tree":
            positions = self._layout_tree(components, page_width, page_height)
        elif layout_type == "vertical":
            positions = self._layout_vertical(components, page_width, page_height)
        elif layout_type == "horizontal":
            positions = self._layout_horizontal(components, page_width, page_height)
        else:
            logger.warning(f"Неизвестный тип размещения: {layout_type}, используется tree")
            positions = self._layout_tree(components, page_width, page_height)
        
        logger.info(f"Расчет позиций завершен, размещено {len(positions)} компонентов")
        return positions
    
    def _get_page_size(self, page_format: str, orientation: str) -> Tuple[float, float]:
        """
        Получение размеров листа по формату и ориентации.
        
        Args:
            page_format: Формат листа (A0-A4)
            orientation: Ориентация (portrait, landscape)
            
        Returns:
            Tuple[float, float]: (ширина, высота) в мм
        """
        width, height = self.PAGE_SIZES.get(page_format, self.PAGE_SIZES["A3"])
        
        if orientation == "portrait":
            return (min(width, height), max(width, height))
        else:  # landscape
            return (max(width, height), min(width, height))
    
    def _layout_tree(
        self,
        components: List[Component],
        page_width: float,
        page_height: float
    ) -> Dict[int, Tuple[float, float]]:
        """
        Древовидная схема размещения с иерархией.
        
        Args:
            components: Список компонентов
            page_width: Ширина листа
            page_height: Высота листа
            
        Returns:
            Dict[int, Tuple[float, float]]: Позиции компонентов
        """
        logger.debug("Применение древовидного размещения")
        
        positions = {}
        
        # Группировка компонентов по уровням
        levels = self._group_by_level(components)
        logger.debug(f"Компоненты сгруппированы по {len(levels)} уровням")
        
        # Расчет доступной ширины для размещения
        available_width = page_width - self.MARGIN_LEFT - self.MARGIN_RIGHT
        available_height = page_height - self.MARGIN_TOP - self.MARGIN_BOTTOM
        
        # Размещение по уровням
        y = self.MARGIN_TOP
        
        for level_num in sorted(levels.keys()):
            items = levels[level_num]
            logger.debug(f"Размещение уровня {level_num}: {len(items)} компонентов")
            
            # Расчет количества компонентов в строке
            items_per_row = max(1, int(available_width / (self.COMPONENT_WIDTH + self.HORIZONTAL_SPACING)))
            
            # Расчет горизонтального смещения для центрирования
            total_width = len(items) * (self.COMPONENT_WIDTH + self.HORIZONTAL_SPACING)
            x_offset = (available_width - total_width) / 2 + self.MARGIN_LEFT
            
            x = x_offset
            row = 0
            
            for idx, component in enumerate(items):
                if idx > 0 and idx % items_per_row == 0:
                    row += 1
                    x = x_offset
                    y += self.COMPONENT_HEIGHT + self.VERTICAL_SPACING
                
                positions[component.position] = (x, y)
                x += self.COMPONENT_WIDTH + self.HORIZONTAL_SPACING
            
            # Переход на следующий уровень
            y += self.LEVEL_SPACING
        
        return positions
    
    def _layout_vertical(
        self,
        components: List[Component],
        page_width: float,
        page_height: float
    ) -> Dict[int, Tuple[float, float]]:
        """
        Вертикальное размещение компонентов в столбец.
        
        Args:
            components: Список компонентов
            page_width: Ширина листа
            page_height: Высота листа
            
        Returns:
            Dict[int, Tuple[float, float]]: Позиции компонентов
        """
        logger.debug("Применение вертикального размещения")
        
        positions = {}
        
        # Центрирование по горизонтали
        x = (page_width - self.COMPONENT_WIDTH) / 2
        y = self.MARGIN_TOP
        
        for component in components:
            positions[component.position] = (x, y)
            y += self.COMPONENT_HEIGHT + self.VERTICAL_SPACING
        
        return positions
    
    def _layout_horizontal(
        self,
        components: List[Component],
        page_width: float,
        page_height: float
    ) -> Dict[int, Tuple[float, float]]:
        """
        Горизонтальное размещение компонентов в строку.
        
        Args:
            components: Список компонентов
            page_width: Ширина листа
            page_height: Высота листа
            
        Returns:
            Dict[int, Tuple[float, float]]: Позиции компонентов
        """
        logger.debug("Применение горизонтального размещения")
        
        positions = {}
        
        # Центрирование по вертикали
        y = (page_height - self.COMPONENT_HEIGHT) / 2
        x = self.MARGIN_LEFT
        
        available_width = page_width - self.MARGIN_LEFT - self.MARGIN_RIGHT
        
        for idx, component in enumerate(components):
            # Проверка выхода за границы листа
            if x + self.COMPONENT_WIDTH > page_width - self.MARGIN_RIGHT:
                logger.warning(f"Компонент {component.position} выходит за границы листа по горизонтали")
            
            positions[component.position] = (x, y)
            x += self.COMPONENT_WIDTH + self.HORIZONTAL_SPACING
        
        return positions
    
    def _group_by_level(self, components: List[Component]) -> Dict[int, List[Component]]:
        """
        Группировка компонентов по уровню иерархии.
        
        Args:
            components: Список компонентов
            
        Returns:
            Dict[int, List[Component]]: Компоненты, сгруппированные по уровням
        """
        levels = {}
        
        for component in components:
            level = component.level
            if level not in levels:
                levels[level] = []
            levels[level].append(component)
        
        logger.debug(f"Компоненты сгруппированы: {[(k, len(v)) for k, v in levels.items()]}")
        return levels
    
    def validate_layout(
        self,
        positions: Dict[int, Tuple[float, float]],
        page_width: float,
        page_height: float
    ) -> List[str]:
        """
        Проверка корректности размещения компонентов.
        
        Args:
            positions: Словарь позиций компонентов
            page_width: Ширина листа
            page_height: Высота листа
            
        Returns:
            List[str]: Список предупреждений (если есть)
        """
        warnings = []
        
        for position, (x, y) in positions.items():
            # Проверка выхода за границы листа
            if x < 0 or y < 0:
                warnings.append(f"Компонент {position} выходит за левую/верхнюю границу листа")
            
            if x + self.COMPONENT_WIDTH > page_width:
                warnings.append(f"Компонент {position} выходит за правую границу листа")
            
            if y + self.COMPONENT_HEIGHT > page_height:
                warnings.append(f"Компонент {position} выходит за нижнюю границу листа")
        
        if warnings:
            logger.warning(f"Обнаружены проблемы с размещением: {len(warnings)} предупреждений")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        return warnings


# Глобальный экземпляр движка размещения
layout_engine = LayoutEngine()
