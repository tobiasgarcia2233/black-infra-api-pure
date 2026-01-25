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
from datetime import datetime
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

app = FastAPI(
    title="BLACK Infrastructure API",
    description="API para sincronización con PST.NET",
    version="1.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    print(f"\n{'='*60}")
    print(f"🔄 SINCRONIZACIÓN PST.NET - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # 1. Verificar API Key
        if not PST_API_KEY:
            raise HTTPException(status_code=500, detail="PST_API_KEY no configurada")
        
        print(f"🔑 API Key (primeros 10 chars): {PST_API_KEY[:10]}")
        print(f"🔑 API Key completa (parcial): {PST_API_KEY[:8]}...{PST_API_KEY[-4:]}")
        
        # 2. URLs a probar (estrategia de fallback)
        api_urls = [
            "https://api.pst.net/api/v1/balances",
            "https://api.pst.net/api/v1/user/balances",
            "https://api.pst.net/api/v1/cards/balances",
        ]
        
        headers = {
            "Authorization": f"Bearer {PST_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        response = None
        success_url = None
        
        async with httpx.AsyncClient() as client:
            for api_url in api_urls:
                print(f"📍 Probando: {api_url}")
                
                try:
                    test_response = await client.get(api_url, headers=headers, timeout=20)
                    print(f"📥 Status: {test_response.status_code}")
                    
                    # Si es 401, endpoint correcto pero token inválido
                    if test_response.status_code == 401:
                        raise HTTPException(
                            status_code=401,
                            detail=f"Token inválido. Endpoint correcto: {api_url}"
                        )
                    
                    # Si es 404, probar siguiente
                    if test_response.status_code == 404:
                        print("⏭️  404 - Siguiente...")
                        continue
                    
                    # Si es exitoso
                    if test_response.is_success:
                        print(f"✅ ENDPOINT CORRECTO: {api_url}")
                        response = test_response
                        success_url = api_url
                        break
                    
                    print(f"⚠️  Status {test_response.status_code} - Siguiente...")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue
        
        # Si ninguna URL funcionó
        if not response:
            raise HTTPException(
                status_code=500,
                detail="No se pudo conectar con PST.NET. Todas las rutas fallaron."
            )
        
        # 3. Parsear respuesta
        print("\n📊 Parseando respuesta...")
        data = response.json()
        
        # 4. Extraer array de balances
        balances_array = []
        
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            print(f"✓ Estructura: data.data ({len(data['data'])} elementos)")
            balances_array = data["data"]
        elif isinstance(data, list):
            print(f"✓ Array directo ({len(data)} elementos)")
            balances_array = data
        elif isinstance(data, dict) and "balances" in data and isinstance(data["balances"], list):
            print(f"✓ data.balances ({len(data['balances'])} elementos)")
            balances_array = data["balances"]
        else:
            raise HTTPException(
                status_code=500,
                detail="Formato de respuesta inesperado"
            )
        
        # 5. Buscar balance USDT
        print("\n💰 Buscando USDT...")
        usdt_balance = None
        
        for item in balances_array:
            currency = item.get("currency") or item.get("asset")
            if currency == "USDT":
                usdt_balance = item
                break
        
        if not usdt_balance:
            currencies = [b.get("currency") or b.get("asset") for b in balances_array]
            raise HTTPException(
                status_code=404,
                detail=f"USDT no encontrado. Disponibles: {', '.join(currencies)}"
            )
        
        print("✅ USDT encontrado")
        
        # 6. Extraer valores
        balance_usdt = float(
            usdt_balance.get("balance") or 
            usdt_balance.get("available") or 
            usdt_balance.get("amount") or 
            0
        )
        cashback = float(
            usdt_balance.get("cashback_balance") or 
            usdt_balance.get("cashback") or 
            usdt_balance.get("rewards") or 
            0
        )
        
        print(f"💰 Balance: ${balance_usdt}")
        print(f"💵 Cashback: ${cashback}")
        
        # 6.5. Obtener cashback aprobado desde /subscriptions/info
        print("\n🎁 Consultando cashback aprobado...")
        approved_cashback = 0.0
        subscription_url = "https://api.pst.net/api/v1/subscriptions/info"
        
        try:
            async with httpx.AsyncClient() as client:
                sub_response = await client.get(subscription_url, headers=headers, timeout=20)
                print(f"📥 Status subscriptions: {sub_response.status_code}")
                
                if sub_response.is_success:
                    sub_data = sub_response.json()
                    
                    # Extraer approved_cashback (viene como string)
                    approved_cashback_str = sub_data.get("approved_cashback", "0")
                    
                    # Si la respuesta tiene estructura data
                    if isinstance(sub_data, dict) and "data" in sub_data:
                        approved_cashback_str = sub_data["data"].get("approved_cashback", "0")
                    
                    # Convertir a float
                    try:
                        approved_cashback = float(approved_cashback_str or "0")
                        print(f"✅ Cashback aprobado: ${approved_cashback}")
                    except (ValueError, TypeError):
                        print(f"⚠️  Error al parsear cashback aprobado: {approved_cashback_str}")
                        approved_cashback = 0.0
                else:
                    print(f"⚠️  No se pudo obtener cashback aprobado: {sub_response.status_code}")
        except Exception as e:
            print(f"⚠️  Error al consultar cashback aprobado: {e}")
        
        # 7. Aplicar regla del 50%
        total_disponible = balance_usdt + cashback
        neto_reparto = round((total_disponible / 2) * 100) / 100
        
        print(f"\n📊 Total: ${total_disponible}")
        print(f"📊 Neto 50%: ${neto_reparto}")
        print(f"🎁 Cashback aprobado: ${approved_cashback}")
        
        # 8. Guardar en Supabase
        if SUPABASE_URL and SUPABASE_KEY:
            print("\n💾 Guardando en Supabase...")
            
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Guardar balance neto en configuracion
            supabase.table("configuracion").upsert({
                "clave": "pst_balance_neto",
                "valor_numerico": neto_reparto,
                "descripcion": f"Balance PST.NET (50% de {total_disponible} USDT)",
                "updated_at": datetime.now().isoformat()
            }, on_conflict="clave").execute()
            
            print("✅ Balance neto guardado")
            
            # Guardar cashback aprobado en configuracion
            supabase.table("configuracion").upsert({
                "clave": "pst_cashback",
                "valor_numerico": approved_cashback,
                "descripcion": f"Cashback aprobado de PST.NET",
                "updated_at": datetime.now().isoformat()
            }, on_conflict="clave").execute()
            
            print("✅ Cashback aprobado guardado")
            
            # Guardar en ingresos (un registro por mes)
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            primer_dia_mes = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            
            ingreso_existente = supabase.table("ingresos")\
                .select("id")\
                .eq("concepto", "PST_REPARTO")\
                .gte("fecha_cobro", primer_dia_mes)\
                .limit(1)\
                .execute()
            
            if ingreso_existente.data and len(ingreso_existente.data) > 0:
                # Actualizar
                ingreso_id = ingreso_existente.data[0]["id"]
                supabase.table("ingresos").update({
                    "monto_usd_total": neto_reparto,
                    "monto_ars": 0,
                    "fecha_cobro": fecha_actual
                }).eq("id", ingreso_id).execute()
                print(f"✅ Ingreso actualizado (ID: {ingreso_id})")
            else:
                # Crear nuevo
                supabase.table("ingresos").insert({
                    "concepto": "PST_REPARTO",
                    "monto_usd_total": neto_reparto,
                    "monto_ars": 0,
                    "fecha_cobro": fecha_actual,
                    "cliente_id": None
                }).execute()
                print("✅ Nuevo ingreso creado")
        
        # 9. Retornar resultado
        result = {
            "success": True,
            "pst": {
                "balance_usdt": balance_usdt,
                "cashback": cashback,
                "approved_cashback": approved_cashback,
                "total_disponible": total_disponible,
                "neto_reparto": neto_reparto
            },
            "message": f"PST sincronizado: ${neto_reparto} USD (50% de ${total_disponible})",
            "fecha": datetime.now().isoformat(),
            "endpoint_usado": success_url
        }
        
        print(f"\n✅ Sincronización exitosa")
        print(f"{'='*60}\n")
        
        return JSONResponse(content=result, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
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
