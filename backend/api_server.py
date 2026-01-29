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
from snapshot_manager import tomar_snapshot_mes_anterior, obtener_snapshot, listar_snapshots
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
        "version": "1.1.0",
        "endpoints": {
            "/sync-pst": "Sincroniza balance de PST.NET",
            "/snapshot-mes-anterior": "Crea snapshot del mes anterior",
            "/snapshot/{periodo}": "Obtiene snapshot de un periodo (MM-YYYY)",
            "/snapshots": "Lista todos los snapshots disponibles",
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


@app.post("/snapshot-mes-anterior")
async def crear_snapshot():
    """
    Crea un snapshot del mes anterior con los valores actuales de PST.NET.
    
    Este endpoint debe ejecutarse el día 1 de cada mes para preservar
    la historia financiera.
    
    Returns:
        JSONResponse: Resultado del snapshot
    """
    try:
        print("\n" + "="*60)
        print("📸 API REQUEST: /snapshot-mes-anterior")
        print("="*60)
        
        resultado = tomar_snapshot_mes_anterior()
        
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
        print(f"❌ Error en /snapshot-mes-anterior: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            content={
                'success': False,
                'error': str(e),
                'message': 'Error al crear snapshot'
            },
            status_code=500
        )


@app.get("/snapshot/{periodo}")
async def obtener_snapshot_periodo(periodo: str):
    """
    Obtiene el snapshot de un periodo específico.
    
    Args:
        periodo: Periodo en formato MM-YYYY (ej: '12-2025')
    
    Returns:
        JSONResponse: Datos del snapshot o error 404
    """
    try:
        print(f"\n📸 API REQUEST: /snapshot/{periodo}")
        
        snapshot = obtener_snapshot(periodo)
        
        if snapshot:
            return JSONResponse(
                content={
                    'success': True,
                    'snapshot': snapshot
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    'success': False,
                    'error': f'No se encontró snapshot para el periodo {periodo}'
                },
                status_code=404
            )
            
    except Exception as e:
        print(f"❌ Error en /snapshot/{periodo}: {e}")
        
        return JSONResponse(
            content={
                'success': False,
                'error': str(e)
            },
            status_code=500
        )


@app.get("/snapshots")
async def listar_todos_snapshots():
    """
    Lista todos los snapshots disponibles, ordenados por fecha descendente.
    
    Returns:
        JSONResponse: Lista de snapshots
    """
    try:
        print("\n📸 API REQUEST: /snapshots")
        
        snapshots = listar_snapshots()
        
        return JSONResponse(
            content={
                'success': True,
                'count': len(snapshots),
                'snapshots': snapshots
            },
            status_code=200
        )
            
    except Exception as e:
        print(f"❌ Error en /snapshots: {e}")
        
        return JSONResponse(
            content={
                'success': False,
                'error': str(e),
                'snapshots': []
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
