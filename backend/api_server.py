#!/usr/bin/env python3
"""
API Server - BLACK INFRASTRUCTURE (DEPRECATED)
===============================================
Este archivo está deprecado. Todos los endpoints están ahora en main.py.

Para mantener compatibilidad, este archivo simplemente importa
la aplicación desde main.py.

Autor: Senior Backend Developer
Fecha: 28/01/2026
Versión: 1.2.0 - DEPRECATED (Use main.py)
"""

# Importar todo desde main.py
from main import app

# Uvicorn buscará 'app' aquí si se ejecuta api_server:app
# Pero el comando correcto es: uvicorn main:app

__all__ = ['app']
