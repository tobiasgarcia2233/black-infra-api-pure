#!/usr/bin/env python3
"""
API Server - BLACK INFRASTRUCTURE
==================================
Servidor FastAPI para endpoints de sincronización

Autor: Senior Backend Developer
Fecha: 23/01/2026
Versión: 1.0.0
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pst_sync_balances import sincronizar_balance_pst
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# CONFIGURACIÓN DE FASTAPI
# ============================================================================

app = FastAPI(
    title="BLACK Infrastructure API",
    description="API para sincronización con servicios externos",
    version="1.0.0"
)

# Configurar CORS para permitir llamadas desde Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.vercel.app",
        "http://localhost:3000",
        os.getenv("WEBAPP_URL", "*")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    Endpoint raíz - Health check
    """
    return {
        "status": "ok",
        "service": "BLACK Infrastructure API",
        "version": "1.0.0",
        "endpoints": {
            "/sync-pst": "Sincroniza balance de PST.NET",
            "/health": "Health check",
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


@app.get("/sync-pst")
@app.post("/sync-pst")
async def sync_pst():
    """
    Sincroniza el balance USDT desde PST.NET y calcula la regla del 50%.
    
    Returns:
        JSONResponse: Resultado de la sincronización
    """
    try:
        print("\n" + "="*60)
        print("🔄 API REQUEST: /sync-pst")
        print("="*60)
        
        resultado = sincronizar_balance_pst()
        
        if resultado.get('success'):
            return JSONResponse(
                content=resultado,
                status_code=200
            )
        else:
            return JSONResponse(
                content=resultado,
                status_code=500
            )
            
    except Exception as e:
        print(f"❌ Error en /sync-pst: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            content={
                'success': False,
                'error': str(e),
                'message': 'Error interno del servidor'
            },
            status_code=500
        )


# ============================================================================
# COMANDO DE INICIO
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "="*70)
    print("🚀 BLACK INFRASTRUCTURE API SERVER")
    print("="*70)
    print(f"📡 Puerto: {port}")
    print(f"🌐 URL: http://0.0.0.0:{port}")
    print(f"📚 Docs: http://0.0.0.0:{port}/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
