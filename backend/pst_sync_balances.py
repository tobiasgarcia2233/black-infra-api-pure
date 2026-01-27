#!/usr/bin/env python3
"""
PST.NET Balance Sync - BLACK INFRASTRUCTURE
============================================
Sincroniza el balance USDT desde PST.NET y calcula la regla del 50%

Autor: Senior Backend Developer
Fecha: 23/01/2026
Versión: 1.0.0
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PST_API_KEY = os.getenv("PST_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


# ============================================================================
# FUNCIÓN PRINCIPAL DE SINCRONIZACIÓN
# ============================================================================

def sincronizar_balance_pst() -> Dict:
    """
    Sincroniza el balance USDT desde PST.NET y aplica la regla del 50%.
    
    Returns:
        dict: Resultado de la sincronización con estructura:
            {
                'success': bool,
                'pst': {
                    'balance_usdt': float,
                    'cashback': float,
                    'total_disponible': float,
                    'neto_reparto': float
                },
                'message': str,
                'fecha': str,
                'error': str (opcional)
            }
    """
    print(f"\n{'='*60}")
    print(f"🔄 SINCRONIZACIÓN PST.NET - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # 1. Verificar API Key
        if not PST_API_KEY:
            error_msg = "PST_API_KEY no está configurada"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'No se pudo sincronizar PST.NET'
            }
        
        print(f"🔑 API Key detectada: {PST_API_KEY[:8]}...{PST_API_KEY[-4:]}")
        
        # 2. URLs a probar (fallback strategy)
        # ACTUALIZACIÓN 27/01/2026: Endpoint oficial confirmado por soporte PST.NET
        api_urls = [
            'https://api.pst.net/integration/members/accounts',  # Endpoint oficial (v2)
            'https://api.pst.net/account/get-all-accounts',       # Fallback (v1 - legacy)
        ]
        
        response = None
        success_url = None
        
        for api_url in api_urls:
            print(f"\n📍 Probando URL: {api_url}")
            
            headers = {
                'Authorization': f'Bearer {PST_API_KEY}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            try:
                test_response = requests.get(
                    api_url,
                    headers=headers,
                    timeout=15
                )
                
                print(f"📥 Status: {test_response.status_code}")
                
                # Si es 401, el endpoint es correcto pero el token es inválido
                if test_response.status_code == 401:
                    error_msg = f"Token inválido o expirado. Endpoint correcto: {api_url}"
                    print(f"🚨 {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'message': 'No se pudo sincronizar PST.NET'
                    }
                
                # Si es 404, intentar con el siguiente
                if test_response.status_code == 404:
                    print("⏭️  404 - Probando siguiente URL...")
                    continue
                
                # Si es exitoso (200-299)
                if test_response.ok:
                    print(f"✅ ENDPOINT CORRECTO: {api_url}")
                    response = test_response
                    success_url = api_url
                    break
                
                print(f"⚠️  Status {test_response.status_code} - Probando siguiente URL...")
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error en fetch: {e}")
                continue
        
        # Si ninguna URL funcionó
        if not response:
            error_msg = "No se pudo conectar con PST.NET. Todas las rutas dieron error."
            print(f"\n❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'No se pudo sincronizar PST.NET'
            }
        
        # 3. Parsear respuesta JSON
        print(f"\n📊 Parseando respuesta...")
        data = response.json()
        print(f"📄 Estructura recibida: {list(data.keys()) if isinstance(data, dict) else 'array'}")
        
        # 4. Extraer array de cuentas/balances
        accounts_array = []
        
        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
            print(f"✓ Estructura Swagger: data.data con {len(data['data'])} elementos")
            accounts_array = data['data']
        elif isinstance(data, dict) and 'accounts' in data and isinstance(data['accounts'], list):
            print(f"✓ data.accounts con {len(data['accounts'])} elementos")
            accounts_array = data['accounts']
        elif isinstance(data, list):
            print(f"✓ Array directo con {len(data)} elementos")
            accounts_array = data
        elif isinstance(data, dict) and 'balances' in data and isinstance(data['balances'], list):
            print(f"✓ data.balances con {len(data['balances'])} elementos")
            accounts_array = data['balances']
        else:
            error_msg = "Formato de respuesta inesperado: no se encontró array de cuentas"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'No se pudo sincronizar PST.NET',
                'raw_response': str(data)[:200]
            }
        
        # 5. Buscar cuenta Master con balance USDT
        print(f"\n💰 Buscando cuenta Master con balance USDT...")
        master_account = None
        
        # Primera pasada: Buscar cuenta con type='Master' o role='Master'
        for item in accounts_array:
            account_type = (item.get('type') or item.get('account_type') or item.get('role') or '').lower()
            currency = (item.get('currency') or item.get('asset') or '').upper()
            
            if 'master' in account_type and currency == 'USDT':
                master_account = item
                print(f"✅ Cuenta Master USDT encontrada (type: {account_type})")
                break
        
        # Segunda pasada: Si no hay Master explícito, buscar la cuenta principal con mayor balance USDT
        if not master_account:
            print(f"⚠️  No se encontró cuenta tipo 'Master', buscando cuenta USDT principal...")
            usdt_accounts = []
            
            for item in accounts_array:
                currency = (item.get('currency') or item.get('asset') or '').upper()
                if currency == 'USDT':
                    balance = float(item.get('balance') or item.get('available') or item.get('amount') or 0)
                    usdt_accounts.append((item, balance))
            
            if usdt_accounts:
                # Ordenar por balance descendente y tomar la primera
                usdt_accounts.sort(key=lambda x: x[1], reverse=True)
                master_account = usdt_accounts[0][0]
                print(f"✅ Cuenta USDT principal encontrada (balance: ${usdt_accounts[0][1]})")
            else:
                available_accounts = [
                    f"{item.get('type', 'N/A')}:{item.get('currency', 'N/A')}" 
                    for item in accounts_array
                ]
                error_msg = f"No se encontró cuenta Master USDT. Disponibles: {', '.join(available_accounts)}"
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'message': 'No se pudo sincronizar PST.NET'
                }
        
        # 6. Extraer valores del balance
        balance_usdt = float(master_account.get('balance') or master_account.get('available') or master_account.get('amount') or 0)
        cashback = float(master_account.get('cashback_balance') or master_account.get('cashback') or master_account.get('rewards') or 0)
        
        print(f"💰 Balance USDT: ${balance_usdt}")
        print(f"💵 Cashback: ${cashback}")
        
        # 7. Aplicar regla del 50%
        total_disponible = balance_usdt + cashback
        neto_reparto = round((total_disponible / 2) * 100) / 100
        
        print(f"\n📊 Total disponible: ${total_disponible}")
        print(f"📊 Neto 50%: ${neto_reparto}")
        
        # 8. Guardar en Supabase
        print(f"\n💾 Guardando en Supabase...")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("⚠️  Supabase no configurado, saltando guardado...")
        else:
            from supabase import create_client
            
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Guardar en tabla configuracion
            config_result = supabase.table('configuracion').upsert({
                'clave': 'pst_balance_neto',
                'valor_numerico': neto_reparto,
                'descripcion': f'Balance PST.NET (50% de {total_disponible} USDT)',
                'updated_at': datetime.now().isoformat()
            }, on_conflict='clave').execute()
            
            print(f"✅ Configuración guardada")
            
            # Guardar en tabla ingresos (un registro por mes)
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            primer_dia_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            
            # Buscar ingreso existente del mes
            ingreso_existente = supabase.table('ingresos')\
                .select('id, monto_usd_total')\
                .eq('concepto', 'PST_REPARTO')\
                .gte('fecha_cobro', primer_dia_mes)\
                .limit(1)\
                .execute()
            
            if ingreso_existente.data and len(ingreso_existente.data) > 0:
                # Actualizar existente
                ingreso_id = ingreso_existente.data[0]['id']
                supabase.table('ingresos').update({
                    'monto_usd_total': neto_reparto,
                    'monto_ars': 0,
                    'fecha_cobro': fecha_actual
                }).eq('id', ingreso_id).execute()
                print(f"✅ Ingreso PST actualizado (ID: {ingreso_id})")
            else:
                # Crear nuevo
                supabase.table('ingresos').insert({
                    'concepto': 'PST_REPARTO',
                    'monto_usd_total': neto_reparto,
                    'monto_ars': 0,
                    'fecha_cobro': fecha_actual,
                    'cliente_id': None
                }).execute()
                print(f"✅ Nuevo ingreso PST creado")
        
        # 9. Retornar resultado exitoso
        result = {
            'success': True,
            'pst': {
                'balance_usdt': balance_usdt,
                'cashback': cashback,
                'total_disponible': total_disponible,
                'neto_reparto': neto_reparto
            },
            'message': f'PST sincronizado: ${neto_reparto} USD (50% de ${total_disponible})',
            'fecha': datetime.now().isoformat(),
            'endpoint_usado': success_url
        }
        
        print(f"\n✅ Sincronización completada exitosamente")
        print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        print(f"\n❌ {error_msg}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': error_msg,
            'message': 'No se pudo sincronizar PST.NET',
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# SCRIPT DE PRUEBA
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 TEST - PST.NET Balance Sync\n")
    
    resultado = sincronizar_balance_pst()
    
    print("\n" + "="*60)
    print("📋 RESULTADO FINAL:")
    print("="*60)
    print(f"Success: {resultado.get('success')}")
    
    if resultado.get('success'):
        pst = resultado.get('pst', {})
        print(f"Balance USDT: ${pst.get('balance_usdt')}")
        print(f"Cashback: ${pst.get('cashback')}")
        print(f"Neto 50%: ${pst.get('neto_reparto')}")
    else:
        print(f"Error: {resultado.get('error')}")
    
    print("="*60 + "\n")
