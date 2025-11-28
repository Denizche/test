# -*- coding: utf-8 -*-
"""
KOMPAS-3D MCP Server - FastAPI приложение (ФИНАЛЬНАЯ ВЕРСИЯ 3.0)

Основной FastAPI сервер для создания схем деления изделий через API КОМПАС-3D.

Все endpoints полностью соответствуют спецификации MCP и документации API КОМПАС-3D.

Автор: MCP Server для КОМПАС-3D
Версия: 3.0 (Финальная)
Дата: 2025-11-21
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import sys
import os

# Добавление пути к модулям
sys.path.insert(0, os.path.dirname(__file__))

from models import (
    Component,
    CreateDivisionSchemeRequest,
    DrawSchemaResponse,
    TitleBlockData
)
from kompas_api_handler_final import KompasAPIHandler
from gost_validator import GOSTValidator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI приложения
app = FastAPI(
    title="KOMPAS-3D MCP Server",
    description="MCP сервер для создания схем деления изделий по ГОСТ Р 2.711-2023",
    version="3.0"
)

# Глобальные переменные
kompas_handler: Optional[KompasAPIHandler] = None
gost_validator: Optional[GOSTValidator] = None


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения."""
    global kompas_handler, gost_validator
    
    logger.info("Запуск KOMPAS-3D MCP Server v3.0...")
    
    # Инициализация обработчика API КОМПАС-3D
    kompas_handler = KompasAPIHandler()
    
    # Инициализация валидатора ГОСТ
    gost_validator = GOSTValidator()
    
    logger.info("KOMPAS-3D MCP Server готов к работе")


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке приложения."""
    global kompas_handler
    
    if kompas_handler is not None:
        kompas_handler.disconnect()
    
    logger.info("KOMPAS-3D MCP Server остановлен")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Проверка статуса сервера и подключения к КОМПАС-3D.
    
    Returns:
        Dict с информацией о статусе
    """
    if kompas_handler is None:
        raise HTTPException(status_code=500, detail="Обработчик API не инициализирован")
    
    # Попытка подключения к КОМПАС-3D
    if not kompas_handler.is_connected:
        if not kompas_handler.connect():
            return {
                "status": "disconnected",
                "message": "Не удалось подключиться к КОМПАС-3D",
                "version": None,
                "ready": False
            }
    
    # Проверка статуса подключения
    status = kompas_handler.check_status()
    status["ready"] = status["status"] == "connected"
    
    return status


@app.get("/api/v1/info")
async def api_info() -> Dict[str, Any]:
    """
    Получение информации об API.
    
    Returns:
        Dict с информацией об API
    """
    return {
        "name": "KOMPAS-3D MCP Server",
        "version": "3.0",
        "description": "MCP сервер для создания схем деления изделий по ГОСТ Р 2.711-2023",
        "endpoints": {
            "/health": "Проверка статуса сервера",
            "/api/v1/info": "Информация об API",
            "/api/v1/create_division_scheme": "Создание схемы деления"
        },
        "standards": [
            "ГОСТ Р 2.711-2023 (Схемы деления)",
            "ГОСТ Р 2.104 (Основные надписи)",
            "ГОСТ 2.701 (Виды и типы схем)"
        ],
        "supported_document_types": [
            "Чертеж (Drawing)",
            "Фрагмент (Fragment)",
            "Спецификация (Specification)"
        ]
    }


@app.post("/api/v1/create_division_scheme", response_model=DrawSchemaResponse)
async def create_division_scheme(request: CreateDivisionSchemeRequest) -> DrawSchemaResponse:
    """
    Создание схемы деления изделия.
    
    Основной endpoint для создания схем деления по ГОСТ Р 2.711-2023.
    
    Args:
        request: Запрос на создание схемы
        
    Returns:
        DrawSchemaResponse с результатом создания
        
    Raises:
        HTTPException: При ошибке создания схемы
    """
    try:
        logger.info(f"Получен запрос на создание схемы деления: {request.designation}")
        
        # Проверка подключения к КОМПАС-3D
        if kompas_handler is None:
            raise HTTPException(status_code=500, detail="Обработчик API не инициализирован")
        
        if not kompas_handler.is_connected:
            if not kompas_handler.connect():
                raise HTTPException(
                    status_code=503,
                    detail="Не удалось подключиться к КОМПАС-3D. Убедитесь, что КОМПАС-3D установлен и запущен."
                )
        
        # Валидация запроса по ГОСТ
        if gost_validator is not None:
            validation_errors = gost_validator.validate_request(request)
            if validation_errors:
                logger.warning(f"Ошибки валидации ГОСТ: {validation_errors}")
                # Не прерываем, но логируем предупреждения
        
        # Подготовка компонентов
        components = []
        for idx, comp in enumerate(request.components):
            component_data = {
                'designation': comp.designation,
                'name': comp.name,
                'quantity': comp.quantity,
                'parent_index': comp.parent_index if hasattr(comp, 'parent_index') else None
            }
            components.append(component_data)
        
        # Создание схемы деления
        result = kompas_handler.create_division_scheme(
            designation=request.designation,
            name=request.name,
            components=components,
            output_file=request.output_file,
            sheet_size=request.sheet_size,
            scale=request.scale
        )
        
        # Проверка результата
        if result["status"] != "success":
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка создания схемы: {result['message']}"
            )
        
        logger.info(f"Схема деления успешно создана: {request.output_file}")
        
        return DrawSchemaResponse(
            status="success",
            message="Схема деления успешно создана",
            file_path=result["file"],
            designation=result["designation"],
            components_count=result["components_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании схемы деления: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработчик общих исключений."""
    logger.error(f"Необработанное исключение: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Внутренняя ошибка сервера",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Запуск сервера
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
