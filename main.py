#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE API
========================
API simple para sincronización con PST.NET

Endpoints:
- GET /sync-pst: Sincroniza balance USDT y cashback aprobado desde PST.NET
- GET /ip: Obtiene la IP pública del servidor

Autor: Senior Backend Developer
Fecha: 23/01/2026
Versión: 1.1.0
"""

import os
import sys
from datetime import datetime
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client

# Agregar backend al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Importar módulo blindado de PST.NET
from pst_sync_balances import sincronizar_balance_pst

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

app = FastAPI(
    title="BLACK Infrastructure API",
    description="API para sincronización con PST.NET",
    version="1.1.0"
)

# CORS - Permitir frontend de Vercel (todos los dominios de Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://black-infra-webapp-pure.vercel.app",
        "https://black-infra-dashboard.vercel.app",
        "https://*.vercel.app",
        "http://localhost:3000",  # Para desarrollo local
        "http://localhost:8000",  # Para testing local
        "*"  # Fallback temporal para debugging
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Variables de entorno
PST_API_KEY = os.getenv("PST_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check básico"""
    return {
        "status": "ok",
        "service": "BLACK Infrastructure API",
        "version": "1.1.0",
        "endpoints": {
            "/sync-pst": "Sincroniza balance y cashback aprobado de PST.NET",
            "/ip": "Obtiene IP pública del servidor"
        }
    }


@app.get("/ip")
async def get_ip():
    """
    Obtiene la IP pública del servidor
    Útil para configurar lista blanca de PST.NET
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.ipify.org?format=json", timeout=10)
            data = response.json()
            ip = data.get("ip")
            
            return {
                "ip": ip,
                "whitelist_format": f"{ip}/32",
                "message": f"Agregar esta IP a la lista blanca de PST.NET: {ip}/32"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener IP: {str(e)}")


@app.options("/sync-pst")
async def sync_pst_options():
    """
    Handler para preflight CORS request
    """
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/sync-pst")
@app.post("/sync-pst")
async def sync_pst():
    """
    Sincroniza el balance USDT y cashback aprobado desde PST.NET
    - Consulta /api/v1/balances para obtener balance y cashback pendiente
    - Consulta /api/v1/subscriptions/info para obtener cashback aprobado
    - Aplica la regla del 50% al balance total
    - Guarda todo en Supabase
    """
    print('🚀🚀🚀 INICIANDO SUPER-SYNC V33 - ESTA ES LA VERSION NUEVA 🚀🚀🚀')
    
    try:
        # USAR MÓDULO BLINDADO v2.1.0 - backend/pst_sync_balances.py
        print("📦 Usando módulo blindado: backend/pst_sync_balances.py v2.1.0")
        resultado = sincronizar_balance_pst()
        
        # Verificar si hubo error (aunque siempre retorna success=True en modo seguro)
        if not resultado.get('success'):
            raise HTTPException(status_code=500, detail=resultado.get('error', 'Error desconocido'))
        
        # Retornar resultado
        return JSONResponse(content=resultado, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ Error en endpoint /sync-pst: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


# ============================================================================
# COMANDO DE INICIO
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "="*70)
    print("🚀 BLACK INFRASTRUCTURE API")
    print("="*70)
    print(f"📡 Puerto: {port}")
    print(f"🌐 URL: http://0.0.0.0:{port}")
    print(f"📚 Docs: http://0.0.0.0:{port}/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
