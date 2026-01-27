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
        
        # Debug: Mostrar muestra de los datos (primeros 500 caracteres)
        import json
        data_preview = json.dumps(data, indent=2)[:500]
        print(f"🔍 Preview de respuesta:\n{data_preview}...")
        
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
        
        # 5. Buscar cuenta con USDT (flexible y robusto)
        print(f"\n💰 Buscando cuentas con balance USDT...")
        print(f"📋 Analizando {len(accounts_array)} cuentas...")
        
        def extraer_balance_usdt(cuenta_item):
            """
            Extrae balance USDT de una cuenta, manejando múltiples estructuras posibles.
            Retorna (balance_usdt, cashback, cuenta_completa) o None si no tiene USDT
            """
            try:
                # Caso 1: Balance directo en el objeto principal
                currency = (cuenta_item.get('currency') or cuenta_item.get('asset') or cuenta_item.get('symbol') or '').upper()
                if currency == 'USDT':
                    balance = float(cuenta_item.get('balance') or cuenta_item.get('available') or cuenta_item.get('amount') or 0)
                    cashback = float(cuenta_item.get('cashback_balance') or cuenta_item.get('cashback') or cuenta_item.get('rewards') or 0)
                    if balance > 0:
                        return (balance, cashback, cuenta_item)
                
                # Caso 2: Balance dentro de un array 'balances'
                if 'balances' in cuenta_item and isinstance(cuenta_item.get('balances'), list):
                    for bal in cuenta_item['balances']:
                        if not isinstance(bal, dict):
                            continue
                        bal_currency = (bal.get('currency') or bal.get('asset') or bal.get('symbol') or '').upper()
                        if bal_currency == 'USDT':
                            balance = float(bal.get('balance') or bal.get('available') or bal.get('amount') or 0)
                            cashback = float(bal.get('cashback_balance') or bal.get('cashback') or bal.get('rewards') or 0)
                            if balance > 0:
                                return (balance, cashback, cuenta_item)
                
                # Caso 3: Balance dentro de un objeto 'balance'
                if 'balance' in cuenta_item and isinstance(cuenta_item.get('balance'), dict):
                    bal = cuenta_item['balance']
                    bal_currency = (bal.get('currency') or bal.get('asset') or bal.get('symbol') or '').upper()
                    if bal_currency == 'USDT':
                        balance = float(bal.get('amount') or bal.get('value') or bal.get('balance') or 0)
                        cashback = float(bal.get('cashback_balance') or bal.get('cashback') or bal.get('rewards') or 0)
                        if balance > 0:
                            return (balance, cashback, cuenta_item)
                
                return None
                
            except Exception as e:
                print(f"⚠️  Error al procesar cuenta: {e}")
                return None
        
        # Buscar todas las cuentas con USDT
        cuentas_usdt = []
        for idx, item in enumerate(accounts_array):
            print(f"  🔍 Cuenta {idx + 1}/{len(accounts_array)}: ", end='')
            
            # Obtener información de la cuenta
            account_type = (item.get('type') or item.get('account_type') or item.get('role') or item.get('name') or 'Unknown').lower()
            print(f"Tipo: {account_type}", end='')
            
            # Intentar extraer balance USDT
            resultado = extraer_balance_usdt(item)
            if resultado:
                balance, cashback, cuenta = resultado
                es_master = 'master' in account_type
                cuentas_usdt.append({
                    'balance': balance,
                    'cashback': cashback,
                    'cuenta': cuenta,
                    'type': account_type,
                    'es_master': es_master,
                    'index': idx
                })
                print(f" ✅ USDT: ${balance} {'🏆 MASTER' if es_master else ''}")
            else:
                print(f" ⏭️  Sin USDT")
        
        # Validar que encontramos al menos una cuenta con USDT
        if not cuentas_usdt:
            error_msg = f"No se encontró ninguna cuenta con balance USDT > 0. Total cuentas analizadas: {len(accounts_array)}"
            print(f"\n❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': 'No se pudo sincronizar PST.NET'
            }
        
        # Seleccionar la mejor cuenta: Master primero, luego la de mayor balance
        print(f"\n🎯 Seleccionando cuenta óptima de {len(cuentas_usdt)} candidatas...")
        
        cuenta_seleccionada = None
        
        # Prioridad 1: Cuenta Master
        cuentas_master = [c for c in cuentas_usdt if c['es_master']]
        if cuentas_master:
            cuenta_seleccionada = max(cuentas_master, key=lambda x: x['balance'])
            print(f"✅ Usando cuenta Master (balance: ${cuenta_seleccionada['balance']})")
        else:
            # Prioridad 2: Cuenta con mayor balance
            cuenta_seleccionada = max(cuentas_usdt, key=lambda x: x['balance'])
            print(f"✅ Usando cuenta con mayor balance: {cuenta_seleccionada['type']} (${cuenta_seleccionada['balance']})")
        
        # 6. Extraer valores finales
        balance_usdt = cuenta_seleccionada['balance']
        cashback = cuenta_seleccionada['cashback']
        
        print(f"💰 Balance USDT: ${balance_usdt}")
        print(f"💵 Cashback: ${cashback}")
        
        # 7. Aplicar regla del 50%
        total_disponible = balance_usdt + cashback
        neto_reparto = round((total_disponible / 2) * 100) / 100
        
        print(f"\n📊 Total disponible: ${total_disponible}")
        print(f"📊 Neto 50%: ${neto_reparto}")
        
        # 8. Guardar en Supabase (con manejo robusto de errores)
        print(f"\n💾 Guardando en Supabase...")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("⚠️  Supabase no configurado, saltando guardado...")
        else:
            try:
                from supabase import create_client
                
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                
                # Guardar en tabla configuracion
                print("📝 Preparando datos para tabla 'configuracion'...")
                config_data = {
                    'clave': 'pst_balance_neto',
                    'valor_numerico': neto_reparto,
                    'descripcion': f'Balance PST.NET (50% de {total_disponible} USDT)',
                    'updated_at': datetime.now().isoformat()
                }
                print(f"   Datos: {config_data}")
                
                print("🔄 Ejecutando upsert en 'configuracion'...")
                config_result = supabase.table('configuracion').upsert(
                    config_data, 
                    on_conflict='clave'
                ).execute()
                
                print(f"✅ Configuración guardada exitosamente")
                
            except Exception as e:
                error_msg = f"Error al guardar en tabla 'configuracion': {str(e)}"
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()
                # Continuar con ingresos aunque falle configuracion
            
            # Guardar en tabla ingresos (un registro por mes)
            try:
                print("\n📝 Preparando ingreso PST para Supabase...")
                fecha_actual = datetime.now().strftime('%Y-%m-%d')
                primer_dia_mes = datetime.now().replace(day=1).strftime('%Y-%m-%d')
                
                print(f"   Fecha actual: {fecha_actual}")
                print(f"   Primer día del mes: {primer_dia_mes}")
                
                # Buscar ingreso existente del mes
                print("🔍 Buscando ingreso PST existente del mes...")
                ingreso_existente = supabase.table('ingresos')\
                    .select('id, monto_usd_total')\
                    .eq('concepto', 'PST_REPARTO')\
                    .gte('fecha_cobro', primer_dia_mes)\
                    .limit(1)\
                    .execute()
                
                if ingreso_existente.data and len(ingreso_existente.data) > 0:
                    # Actualizar existente
                    ingreso_id = ingreso_existente.data[0]['id']
                    print(f"📝 Actualizando ingreso existente (ID: {ingreso_id})...")
                    
                    update_data = {
                        'monto_usd_total': neto_reparto,
                        'monto_ars': 0,
                        'fecha_cobro': fecha_actual
                    }
                    print(f"   Datos: {update_data}")
                    
                    supabase.table('ingresos').update(update_data).eq('id', ingreso_id).execute()
                    print(f"✅ Ingreso PST actualizado exitosamente (ID: {ingreso_id})")
                else:
                    # Crear nuevo
                    print("📝 Creando nuevo ingreso PST...")
                    insert_data = {
                        'concepto': 'PST_REPARTO',
                        'monto_usd_total': neto_reparto,
                        'monto_ars': 0,
                        'fecha_cobro': fecha_actual,
                        'cliente_id': None
                    }
                    print(f"   Datos: {insert_data}")
                    
                    supabase.table('ingresos').insert(insert_data).execute()
                    print(f"✅ Nuevo ingreso PST creado exitosamente")
                    
            except Exception as e:
                error_msg = f"Error al guardar en tabla 'ingresos': {str(e)}"
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()
                print("⚠️  Continuando a pesar del error en ingresos...")
        
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
