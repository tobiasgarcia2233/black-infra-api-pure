#!/usr/bin/env python3
"""
Main API Server - BLACK INFRASTRUCTURE
=======================================
Servidor FastAPI consolidado con todos los endpoints.

⚠️  ESTE ES EL ARCHIVO PRINCIPAL - Render ejecuta: uvicorn main:app

Autor: Senior Backend Developer
Fecha: 28/01/2026
Versión: 1.2.0 - CONSOLIDADO

ENDPOINTS:
- GET  / - Root con lista de endpoints
- GET  /health - Health check
- POST /sync-pst - Sincronizar balance PST.NET
- POST /snapshot-mes-anterior - Crear snapshot del mes anterior
- GET  /snapshot/{periodo} - Obtener snapshot específico
- GET  /snapshots - Listar todos los snapshots
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="BLACK Infrastructure API",
    description="API consolidada para sincronización y snapshots",
    version="1.2.0"
)

# Configurar CORS
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
# ENDPOINT: ROOT
# ============================================================================

@app.get("/")
async def root():
    """Endpoint raíz - Health check y lista de endpoints"""
    return {
        "status": "ok",
        "service": "BLACK Infrastructure API",
        "version": "1.2.0",
        "endpoints": {
            "/health": "Health check",
            "/sync-pst": "Sincroniza balance de PST.NET",
            "/snapshot-mes-anterior": "Crea snapshot del mes anterior",
            "/snapshot/{periodo}": "Obtiene snapshot de un periodo (MM-YYYY)",
            "/snapshots": "Lista todos los snapshots disponibles",
        }
    }

# ============================================================================
# ENDPOINT: HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# ENDPOINT: SYNC PST
# ============================================================================

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
        
        # Importar la función de sincronización
        from pst_sync_balances import sincronizar_balance_pst
        
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
# ENDPOINT: CREAR SNAPSHOT DEL MES ANTERIOR
# ============================================================================

@app.post("/snapshot-mes-anterior")
async def crear_snapshot():
    """
    Crea un snapshot del mes anterior con los valores actuales de PST.NET.
    
    CÁLCULO CONSERVADOR:
    - balance_neto = 50% SOLO de cuentas ID 15 y 2
    - cashback_aprobado = valor completo (NO se suma al neto)
    - cashback_hold = valor completo (NO se suma al neto)
    
    Returns:
        JSONResponse: Resultado del snapshot
    """
    try:
        print("\n" + "="*60)
        print("📸 API REQUEST: /snapshot-mes-anterior")
        print("="*60)
        
        # Verificar configuración de Supabase
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            error_msg = "Supabase no está configurado correctamente"
            print(f"❌ {error_msg}")
            return JSONResponse(
                content={
                    'success': False,
                    'error': error_msg
                },
                status_code=500
            )
        
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Calcular periodo anterior (mes que acaba de cerrar)
        fecha_anterior = datetime.now() - timedelta(days=30)
        anio_anterior = fecha_anterior.year
        mes_anterior = fecha_anterior.month
        periodo_anterior = f"{str(mes_anterior).zfill(2)}-{anio_anterior}"
        
        print(f"📅 Periodo a fotografiar: {periodo_anterior}")
        
        # Verificar si ya existe snapshot para este periodo
        result_check = supabase.table('historial_saldos').select('id').eq('periodo', periodo_anterior).execute()
        
        if result_check.data and len(result_check.data) > 0:
            print(f"⚠️  Ya existe un snapshot para el periodo {periodo_anterior}")
            return JSONResponse(
                content={
                    'success': True,
                    'periodo': periodo_anterior,
                    'message': f'Snapshot ya existe para {periodo_anterior}',
                    'already_exists': True
                },
                status_code=200
            )
        
        # Obtener valores actuales de configuración
        print(f"\n💾 Obteniendo valores actuales de configuración...")
        
        # 1. Balance neto (50% de cuentas - CÁLCULO CONSERVADOR)
        result_neto = supabase.table('configuracion').select('valor_numerico').eq('clave', 'pst_balance_neto').single().execute()
        neto_reparto = float(result_neto.data['valor_numerico']) if result_neto.data else 0.0
        
        # Calcular balance total de cuentas (neto * 2, ya que neto es el 50%)
        balance_cuentas_total = neto_reparto * 2
        
        # 2. Cashback aprobado (NO se suma al neto, solo tracking)
        result_aprobado = supabase.table('configuracion').select('valor_numerico').eq('clave', 'pst_cashback_aprobado').single().execute()
        cashback_aprobado = float(result_aprobado.data['valor_numerico']) if result_aprobado.data else 0.0
        
        # 3. Cashback hold (NO se suma al neto, solo tracking)
        result_hold = supabase.table('configuracion').select('valor_numerico').eq('clave', 'pst_cashback_hold').single().execute()
        cashback_hold = float(result_hold.data['valor_numerico']) if result_hold.data else 0.0
        
        print(f"\n💰 VALORES PARA SNAPSHOT (CONSERVADOR):")
        print(f"   Balance cuentas (ID 15+2): ${balance_cuentas_total:,.2f}")
        print(f"   Neto reparto (50%): ${neto_reparto:,.2f} ← Solo cuentas")
        print(f"   Cashback aprobado: ${cashback_aprobado:,.2f} ← NO suma al neto")
        print(f"   Cashback hold: ${cashback_hold:,.2f} ← NO suma al neto")
        
        # Insertar snapshot
        print(f"\n📸 Creando snapshot en historial_saldos...")
        
        snapshot_data = {
            'periodo': periodo_anterior,
            'anio': anio_anterior,
            'mes': mes_anterior,
            'balance_cuentas_total': balance_cuentas_total,
            'neto_reparto': neto_reparto,  # ← 50% SOLO de cuentas
            'cashback_aprobado': cashback_aprobado,  # ← Tracking
            'cashback_hold': cashback_hold,  # ← Tracking
            'fecha_snapshot': datetime.now().isoformat(),
            'notas': 'Snapshot automático de cierre de mes (Cálculo conservador)'
        }
        
        result_insert = supabase.table('historial_saldos').insert(snapshot_data).execute()
        
        print(f"✅ Snapshot creado exitosamente para periodo {periodo_anterior}")
        print(f"{'='*60}\n")
        
        return JSONResponse(
            content={
                'success': True,
                'periodo': periodo_anterior,
                'snapshot': snapshot_data,
                'message': f'Snapshot creado exitosamente para {periodo_anterior}'
            },
            status_code=200
        )
        
    except Exception as e:
        error_msg = f"Error al crear snapshot: {str(e)}"
        print(f"\n❌ {error_msg}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            content={
                'success': False,
                'error': error_msg
            },
            status_code=500
        )

# ============================================================================
# ENDPOINT: OBTENER SNAPSHOT DE UN PERIODO
# ============================================================================

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
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return JSONResponse(
                content={
                    'success': False,
                    'error': 'Supabase no configurado'
                },
                status_code=500
            )
        
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        result = supabase.table('historial_saldos').select('*').eq('periodo', periodo).single().execute()
        
        if result.data:
            return JSONResponse(
                content={
                    'success': True,
                    'snapshot': result.data
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

# ============================================================================
# ENDPOINT: LISTAR TODOS LOS SNAPSHOTS
# ============================================================================

@app.get("/snapshots")
async def listar_todos_snapshots():
    """
    Lista todos los snapshots disponibles, ordenados por fecha descendente.
    
    Returns:
        JSONResponse: Lista de snapshots
    """
    try:
        print("\n📸 API REQUEST: /snapshots")
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return JSONResponse(
                content={
                    'success': False,
                    'error': 'Supabase no configurado',
                    'snapshots': []
                },
                status_code=500
            )
        
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        result = supabase.table('historial_saldos').select('*').order('anio', desc=True).order('mes', desc=True).execute()
        
        snapshots = result.data if result.data else []
        
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
    print("🚀 BLACK INFRASTRUCTURE API SERVER (CONSOLIDADO)")
    print("="*70)
    print(f"📡 Puerto: {port}")
    print(f"🌐 URL: http://0.0.0.0:{port}")
    print(f"📚 Docs: http://0.0.0.0:{port}/docs")
    print(f"📋 Endpoints:")
    print(f"   - GET  /health")
    print(f"   - POST /sync-pst")
    print(f"   - POST /snapshot-mes-anterior")
    print(f"   - GET  /snapshot/{{periodo}}")
    print(f"   - GET  /snapshots")
    print("="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
