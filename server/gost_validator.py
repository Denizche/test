"""
Валидатор соответствия ГОСТ 2.701 для схем деления.

Этот модуль содержит класс GOSTValidator для проверки соответствия
создаваемых схем деления требованиям ГОСТ 2.701.

ГОСТ 2.701 - Единая система конструкторской документации.
Схемы деления изделий.
"""

import logging
import re
from typing import List, Dict, Tuple, Optional
from models import Component, CreateDivisionSchemeRequest

logger = logging.getLogger(__name__)


class GOSTValidator:
    """
    Валидатор для проверки соответствия схем деления ГОСТ 2.701.
    
    Проверяет:
    - Формат обозначений компонентов (XXXX.XX.XX.XXX)
    - Уникальность позиционных номеров
    - Корректность иерархии компонентов
    - Наличие обязательных полей в основной надписи
    - Соответствие форматов листов и ориентации
    """
    
    # Регулярное выражение для проверки обозначения по ГОСТ
    DESIGNATION_PATTERN = r'^\d{4}\.\d{2}\.\d{2}\.\d{3}$'
    
    # Обязательные поля в основной надписи
    REQUIRED_TITLE_BLOCK_FIELDS = ['designation', 'name']
    
    # Поддерживаемые форматы листов
    SUPPORTED_FORMATS = ["A0", "A1", "A2", "A3", "A4"]
    
    # Поддерживаемые ориентации
    SUPPORTED_ORIENTATIONS = ["portrait", "landscape"]
    
    # Поддерживаемые типы размещения
    SUPPORTED_LAYOUT_TYPES = ["tree", "vertical", "horizontal"]
    
    def __init__(self):
        """Инициализация валидатора."""
        logger.info("GOSTValidator инициализирован")
    
    def validate_request(
        self,
        request: CreateDivisionSchemeRequest
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Полная проверка запроса на соответствие ГОСТ 2.701.
        
        Args:
            request: Запрос на создание схемы деления
            
        Returns:
            Tuple[bool, List[str], List[str]]: (валидно, ошибки, предупреждения)
        """
        logger.info(f"Валидация запроса для изделия '{request.product_name}'")
        
        errors = []
        warnings = []
        
        # Проверка основной надписи
        title_errors, title_warnings = self._validate_title_block(request.title_block_data)
        errors.extend(title_errors)
        warnings.extend(title_warnings)
        
        # Проверка компонентов
        comp_errors, comp_warnings = self._validate_components(request.components)
        errors.extend(comp_errors)
        warnings.extend(comp_warnings)
        
        # Проверка формата листа
        format_errors = self._validate_format(request.gost_format)
        errors.extend(format_errors)
        
        # Проверка ориентации
        orientation_errors = self._validate_orientation(request.orientation)
        errors.extend(orientation_errors)
        
        # Проверка типа размещения
        layout_errors = self._validate_layout_type(request.layout_type)
        errors.extend(layout_errors)
        
        # Проверка иерархии компонентов
        hierarchy_errors = self._validate_hierarchy(request.components)
        errors.extend(hierarchy_errors)
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Запрос валиден по ГОСТ 2.701")
        else:
            logger.error(f"Обнаружены ошибки валидации: {len(errors)}")
        
        if warnings:
            logger.warning(f"Обнаружены предупреждения: {len(warnings)}")
        
        return is_valid, errors, warnings
    
    def _validate_title_block(self, title_block) -> Tuple[List[str], List[str]]:
        """
        Проверка данных основной надписи.
        
        Args:
            title_block: Данные основной надписи
            
        Returns:
            Tuple[List[str], List[str]]: (ошибки, предупреждения)
        """
        logger.debug("Проверка основной надписи")
        
        errors = []
        warnings = []
        
        if not title_block:
            errors.append("Основная надпись не может быть пустой")
            return errors, warnings
        
        # Проверка обязательных полей
        if not title_block.designation:
            errors.append("Обозначение изделия (designation) обязательно")
        elif not re.match(self.DESIGNATION_PATTERN, title_block.designation):
            errors.append(f"Обозначение '{title_block.designation}' не соответствует формату ГОСТ (XXXX.XX.XX.XXX)")
        
        if not title_block.name:
            errors.append("Наименование изделия (name) обязательно")
        
        # Предупреждения
        if not title_block.developer:
            warnings.append("Рекомендуется указать разработчика (developer)")
        
        if not title_block.organization:
            warnings.append("Рекомендуется указать организацию (organization)")
        
        return errors, warnings
    
    def _validate_components(self, components: List[Component]) -> Tuple[List[str], List[str]]:
        """
        Проверка компонентов.
        
        Args:
            components: Список компонентов
            
        Returns:
            Tuple[List[str], List[str]]: (ошибки, предупреждения)
        """
        logger.debug(f"Проверка {len(components)} компонентов")
        
        errors = []
        warnings = []
        
        if not components:
            errors.append("Список компонентов не может быть пустым")
            return errors, warnings
        
        # Проверка уникальности позиционных номеров
        positions = [c.position for c in components]
        if len(positions) != len(set(positions)):
            duplicates = [p for p in positions if positions.count(p) > 1]
            errors.append(f"Дублирующиеся позиционные номера: {duplicates}")
        
        # Проверка каждого компонента
        for component in components:
            comp_errors, comp_warnings = self._validate_single_component(component)
            errors.extend(comp_errors)
            warnings.extend(comp_warnings)
        
        return errors, warnings
    
    def _validate_single_component(self, component: Component) -> Tuple[List[str], List[str]]:
        """
        Проверка одного компонента.
        
        Args:
            component: Компонент для проверки
            
        Returns:
            Tuple[List[str], List[str]]: (ошибки, предупреждения)
        """
        errors = []
        warnings = []
        
        # Проверка обозначения
        if not re.match(self.DESIGNATION_PATTERN, component.designation):
            errors.append(f"Компонент {component.position}: обозначение '{component.designation}' не соответствует формату ГОСТ (XXXX.XX.XX.XXX)")
        
        # Проверка количества
        if component.quantity < 1:
            errors.append(f"Компонент {component.position}: количество должно быть >= 1")
        
        # Проверка уровня
        if component.level < 0:
            errors.append(f"Компонент {component.position}: уровень не может быть отрицательным")
        
        # Предупреждения
        if not component.name:
            warnings.append(f"Компонент {component.position}: рекомендуется указать наименование")
        
        return errors, warnings
    
    def _validate_format(self, gost_format: str) -> List[str]:
        """
        Проверка формата листа.
        
        Args:
            gost_format: Формат листа
            
        Returns:
            List[str]: Список ошибок
        """
        logger.debug(f"Проверка формата листа: {gost_format}")
        
        errors = []
        
        if gost_format not in self.SUPPORTED_FORMATS:
            errors.append(f"Неподдерживаемый формат листа: {gost_format}. Поддерживаемые: {', '.join(self.SUPPORTED_FORMATS)}")
        
        return errors
    
    def _validate_orientation(self, orientation: str) -> List[str]:
        """
        Проверка ориентации листа.
        
        Args:
            orientation: Ориентация листа
            
        Returns:
            List[str]: Список ошибок
        """
        logger.debug(f"Проверка ориентации: {orientation}")
        
        errors = []
        
        if orientation not in self.SUPPORTED_ORIENTATIONS:
            errors.append(f"Неподдерживаемая ориентация: {orientation}. Поддерживаемые: {', '.join(self.SUPPORTED_ORIENTATIONS)}")
        
        return errors
    
    def _validate_layout_type(self, layout_type: str) -> List[str]:
        """
        Проверка типа размещения.
        
        Args:
            layout_type: Тип размещения
            
        Returns:
            List[str]: Список ошибок
        """
        logger.debug(f"Проверка типа размещения: {layout_type}")
        
        errors = []
        
        if layout_type not in self.SUPPORTED_LAYOUT_TYPES:
            errors.append(f"Неподдерживаемый тип размещения: {layout_type}. Поддерживаемые: {', '.join(self.SUPPORTED_LAYOUT_TYPES)}")
        
        return errors
    
    def _validate_hierarchy(self, components: List[Component]) -> List[str]:
        """
        Проверка корректности иерархии компонентов.
        
        Args:
            components: Список компонентов
            
        Returns:
            List[str]: Список ошибок
        """
        logger.debug("Проверка иерархии компонентов")
        
        errors = []
        
        # Получение всех доступных позиций
        valid_positions = {c.position for c in components}
        
        # Проверка ссылок на родительские компоненты
        for component in components:
            if component.parent_position is not None:
                if component.parent_position not in valid_positions:
                    errors.append(f"Компонент {component.position} ссылается на несуществующий родитель {component.parent_position}")
                
                # Проверка, что родитель имеет меньший уровень
                parent = next((c for c in components if c.position == component.parent_position), None)
                if parent and parent.level >= component.level:
                    errors.append(f"Компонент {component.position}: родитель должен иметь меньший уровень иерархии")
        
        # Проверка, что есть главное изделие (level=0)
        main_components = [c for c in components if c.level == 0]
        if len(main_components) != 1:
            errors.append(f"Должно быть ровно одно главное изделие (level=0), найдено: {len(main_components)}")
        
        return errors
    
    def get_validation_report(
        self,
        request: CreateDivisionSchemeRequest
    ) -> Dict[str, any]:
        """
        Получить подробный отчет валидации.
        
        Args:
            request: Запрос на создание схемы деления
            
        Returns:
            Dict: Подробный отчет валидации
        """
        is_valid, errors, warnings = self.validate_request(request)
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "product_name": request.product_name,
            "product_code": request.product_code,
            "component_count": len(request.components),
            "layout_type": request.layout_type,
            "gost_format": request.gost_format
        }


# Глобальный экземпляр валидатора
gost_validator = GOSTValidator()
