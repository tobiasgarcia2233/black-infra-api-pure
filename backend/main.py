#!/usr/bin/env python3
"""
Main Entry Point - BLACK INFRASTRUCTURE
========================================
Punto de entrada principal para Uvicorn en Render.

Este archivo importa la aplicación FastAPI de api_server.py
para que Render pueda ejecutar: uvicorn main:app

Autor: Senior Backend Developer
Fecha: 28/01/2026
Versión: 1.1.0
"""

# Importar la aplicación FastAPI desde api_server
from api_server import app

# Uvicorn buscará la variable 'app' en este archivo
# Todos los endpoints están definidos en api_server.py

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "="*70)
    print("🚀 BLACK INFRASTRUCTURE API SERVER")
    print("="*70)
    print(f"📡 Puerto: {port}")
    print(f"🌐 URL: http://0.0.0.0:{port}")
    print(f"📚 Docs: http://0.0.0.0:{port}/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
