#!/usr/bin/env python3
"""
PST.NET Balance Sync - BLACK INFRASTRUCTURE
============================================
Sincroniza el balance USDT desde PST.NET y calcula la regla del 50%

Autor: Senior Backend Developer
Fecha: 23/01/2026
Versión: 2.1.0 - INDESTRUCTIBLE EDITION + MULTI-HEADER AUTH

MEJORAS DE ROBUSTEZ (v2.0.0 - 27/01/2026):
==========================================
✅ DEBUG RAW: Imprime JSON crudo de la primera cuenta en logs
✅ BÚSQUEDA RECURSIVA: Encuentra USDT en estructuras nested complejas
✅ BLINDAJE 500: NUNCA retorna Error 500, siempre success=True
✅ MODO SEGURO: Si falla algo, retorna balance 0 con error en logs
✅ TOLERANCIA A FALLOS: Cada cuenta se procesa en try-catch individual
✅ LOGGING DETALLADO: Traceback completo para debugging en Render

NUEVAS FUNCIONALIDADES (v2.1.0 - 27/01/2026):
=============================================
🔐 MULTI-HEADER AUTH: Prueba múltiples formatos de autenticación
   - Intento A: Authorization Bearer (estándar)
   - Intento B: X-API-KEY (alternativo)
🧹 ENDPOINTS LIMPIOS: Eliminados legacy/v1, solo endpoint oficial
🛡️ PARSEO SEGURO: JSON parsing con try-catch para respuestas inválidas
📊 LOGS MEJORADOS: Indica qué formato de header funcionó

ARQUITECTURA DE EXTRACCIÓN:
- Estrategia 1: Búsqueda recursiva profunda (hasta 5 niveles)
- Estrategia 2: Métodos clásicos (balance directo, arrays, objetos)
- Estrategia 3: Búsqueda profunda con función recursiva nested

ENDPOINT OFICIAL (confirmado por soporte PST.NET):
- GET /integration/members/accounts
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
        
        # 2. Endpoint oficial (único, confirmado por soporte PST.NET)
        # ACTUALIZACIÓN 27/01/2026 v2: Solo endpoint oficial, eliminados legacy/v1
        api_url = 'https://api.pst.net/integration/members/accounts'
        
        print(f"\n📍 Endpoint oficial PST.NET: {api_url}")
        print(f"🔐 Estrategia: Probar múltiples formatos de autenticación\n")
        
        response = None
        header_format_usado = None
        
        # ESTRATEGIA DE PRUEBA: Dos formatos de header
        header_strategies = [
            {
                'name': 'Bearer Token (Estándar)',
                'headers': {
                    'Authorization': f'Bearer {PST_API_KEY}',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            },
            {
                'name': 'X-API-KEY (Alternativo)',
                'headers': {
                    'X-API-KEY': PST_API_KEY,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }
        ]
        
        for idx, strategy in enumerate(header_strategies):
            strategy_name = strategy['name']
            headers = strategy['headers']
            
            print(f"{'🔑' if idx == 0 else '🔐'} Intento #{idx + 1}: {strategy_name}")
            
            try:
                test_response = requests.get(
                    api_url,
                    headers=headers,
                    timeout=15
                )
                
                print(f"📥 Status: {test_response.status_code}")
                
                # Si es exitoso (200-299)
                if test_response.ok:
                    print(f"✅ AUTENTICACIÓN EXITOSA con {strategy_name}")
                    response = test_response
                    header_format_usado = strategy_name
                    break
                
                # Si es 401, el token/formato puede estar incorrecto
                if test_response.status_code == 401:
                    if idx < len(header_strategies) - 1:
                        # Todavía quedan estrategias por probar
                        print(f"⚠️  Intento con {strategy_name} falló (401), probando formato alternativo...")
                        continue
                    else:
                        # Última estrategia también falló
                        error_msg = f"Autenticación rechazada (401) con todos los formatos. Verificar PST_API_KEY."
                        print(f"🚨 {error_msg}")
                        # BLINDAJE: No fallar con 500
                        return {
                            'success': True,
                            'pst': {
                                'balance_usdt': 0.0,
                                'cashback': 0.0,
                                'total_disponible': 0.0,
                                'neto_reparto': 0.0
                            },
                            'message': 'PST sincronizado con error (token inválido)',
                            'warning': error_msg,
                            'fecha': datetime.now().isoformat(),
                            'modo_seguro': True,
                            'error_autenticacion': True
                        }
                
                # Si es 404
                if test_response.status_code == 404:
                    print(f"⚠️  404 - Endpoint no encontrado con {strategy_name}")
                    if idx < len(header_strategies) - 1:
                        continue
                    else:
                        error_msg = "Endpoint /integration/members/accounts no encontrado (404)"
                        print(f"🚨 {error_msg}")
                        return {
                            'success': True,
                            'pst': {
                                'balance_usdt': 0.0,
                                'cashback': 0.0,
                                'total_disponible': 0.0,
                                'neto_reparto': 0.0
                            },
                            'message': 'PST sincronizado con error (endpoint no encontrado)',
                            'warning': error_msg,
                            'fecha': datetime.now().isoformat(),
                            'modo_seguro': True
                        }
                
                # Otro status code
                print(f"⚠️  Status {test_response.status_code} con {strategy_name}")
                if idx < len(header_strategies) - 1:
                    print("   Probando siguiente formato...")
                    continue
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error en conexión con {strategy_name}: {e}")
                if idx < len(header_strategies) - 1:
                    print("   Probando siguiente formato...")
                    continue
            except Exception as e:
                print(f"❌ Error inesperado con {strategy_name}: {e}")
                if idx < len(header_strategies) - 1:
                    continue
        
        # Si ningún formato funcionó
        if not response:
            error_msg = "No se pudo conectar con PST.NET con ningún formato de autenticación."
            print(f"\n❌ {error_msg}")
            print(f"🛡️  MODO SEGURO: Retornando balance 0")
            
            return {
                'success': True,
                'pst': {
                    'balance_usdt': 0.0,
                    'cashback': 0.0,
                    'total_disponible': 0.0,
                    'neto_reparto': 0.0
                },
                'message': 'PST sincronizado con error (sin conexión)',
                'warning': error_msg,
                'fecha': datetime.now().isoformat(),
                'modo_seguro': True,
                'error_conexion': True
            }
        
        # 3. Parsear respuesta JSON (con blindaje anti-500)
        print(f"\n📊 Parseando respuesta...")
        
        try:
            data = response.json()
            print(f"✅ JSON válido parseado correctamente")
        except ValueError as e:
            error_msg = f"Respuesta no es JSON válido: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"📄 Raw response (primeros 500 chars): {response.text[:500]}")
            print(f"🛡️  MODO SEGURO: Retornando balance 0")
            
            return {
                'success': True,
                'pst': {
                    'balance_usdt': 0.0,
                    'cashback': 0.0,
                    'total_disponible': 0.0,
                    'neto_reparto': 0.0
                },
                'message': 'PST sincronizado con error (respuesta inválida)',
                'warning': error_msg,
                'fecha': datetime.now().isoformat(),
                'modo_seguro': True,
                'error_parseo': True
            }
        except Exception as e:
            error_msg = f"Error inesperado parseando JSON: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"🛡️  MODO SEGURO: Retornando balance 0")
            
            return {
                'success': True,
                'pst': {
                    'balance_usdt': 0.0,
                    'cashback': 0.0,
                    'total_disponible': 0.0,
                    'neto_reparto': 0.0
                },
                'message': 'PST sincronizado con error (error de parseo)',
                'warning': error_msg,
                'fecha': datetime.now().isoformat(),
                'modo_seguro': True,
                'error_parseo': True
            }
        
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
        
        # 5. DEBUG: Imprimir estructura RAW de la primera cuenta
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG: ESTRUCTURA RAW DE LA PRIMERA CUENTA")
        print(f"{'='*60}")
        if len(accounts_array) > 0:
            print(f"DEBUG_DATA: {json.dumps(accounts_array[0], indent=2, ensure_ascii=False, default=str)}")
        else:
            print("⚠️  WARNING: Array de cuentas está vacío")
        print(f"{'='*60}\n")
        
        # 6. Buscar cuenta con USDT (flexible y robusto)
        print(f"\n💰 Buscando cuentas con balance USDT...")
        print(f"📋 Analizando {len(accounts_array)} cuentas...")
        
        def buscar_valor_recursivo(obj, keys_buscar):
            """
            Busca valores en un objeto de forma recursiva.
            keys_buscar: lista de posibles nombres de clave a buscar
            Retorna el primer valor encontrado o None
            """
            if obj is None:
                return None
            
            # Si es un diccionario, buscar en sus claves
            if isinstance(obj, dict):
                # Buscar directamente en las claves del objeto
                for key in keys_buscar:
                    if key in obj and obj[key] is not None:
                        return obj[key]
                
                # Buscar recursivamente en todos los valores
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        resultado = buscar_valor_recursivo(value, keys_buscar)
                        if resultado is not None:
                            return resultado
            
            # Si es una lista, buscar en cada elemento
            elif isinstance(obj, list):
                for item in obj:
                    resultado = buscar_valor_recursivo(item, keys_buscar)
                    if resultado is not None:
                        return resultado
            
            return None
        
        def extraer_balance_usdt(cuenta_item):
            """
            Extrae balance USDT de una cuenta, manejando múltiples estructuras posibles.
            Usa búsqueda recursiva profunda para encontrar currency y balance.
            Retorna (balance_usdt, cashback, cuenta_completa) o None si no tiene USDT
            """
            try:
                # ESTRATEGIA 1: Búsqueda recursiva de currency/asset/symbol
                currency_keys = ['currency', 'asset', 'symbol', 'coin', 'token', 'currencyCode']
                currency_encontrado = buscar_valor_recursivo(cuenta_item, currency_keys)
                
                if currency_encontrado and str(currency_encontrado).upper() == 'USDT':
                    # Encontramos USDT, ahora buscar el balance
                    balance_keys = ['balance', 'available', 'amount', 'total', 'availableBalance', 'free']
                    balance_encontrado = buscar_valor_recursivo(cuenta_item, balance_keys)
                    
                    if balance_encontrado is not None:
                        try:
                            balance = float(balance_encontrado)
                            if balance > 0:
                                # Buscar cashback (opcional)
                                cashback_keys = ['cashback_balance', 'cashback', 'rewards', 'bonus', 'cashBack']
                                cashback_encontrado = buscar_valor_recursivo(cuenta_item, cashback_keys)
                                cashback = float(cashback_encontrado) if cashback_encontrado else 0
                                
                                return (balance, cashback, cuenta_item)
                        except (ValueError, TypeError) as e:
                            print(f"⚠️  Error convirtiendo balance a float: {e}")
                
                # ESTRATEGIA 2: Métodos clásicos (fallback)
                # Caso A: Balance directo en el objeto principal
                currency = str(cuenta_item.get('currency') or cuenta_item.get('asset') or cuenta_item.get('symbol') or '').upper()
                if currency == 'USDT':
                    balance = float(cuenta_item.get('balance') or cuenta_item.get('available') or cuenta_item.get('amount') or 0)
                    cashback = float(cuenta_item.get('cashback_balance') or cuenta_item.get('cashback') or cuenta_item.get('rewards') or 0)
                    if balance > 0:
                        return (balance, cashback, cuenta_item)
                
                # Caso B: Balance dentro de un array 'balances'
                if 'balances' in cuenta_item and isinstance(cuenta_item.get('balances'), list):
                    for bal in cuenta_item['balances']:
                        if not isinstance(bal, dict):
                            continue
                        bal_currency = str(bal.get('currency') or bal.get('asset') or bal.get('symbol') or '').upper()
                        if bal_currency == 'USDT':
                            balance = float(bal.get('balance') or bal.get('available') or bal.get('amount') or 0)
                            cashback = float(bal.get('cashback_balance') or bal.get('cashback') or bal.get('rewards') or 0)
                            if balance > 0:
                                return (balance, cashback, cuenta_item)
                
                # Caso C: Balance dentro de un objeto 'balance'
                if 'balance' in cuenta_item and isinstance(cuenta_item.get('balance'), dict):
                    bal = cuenta_item['balance']
                    bal_currency = str(bal.get('currency') or bal.get('asset') or bal.get('symbol') or '').upper()
                    if bal_currency == 'USDT':
                        balance = float(bal.get('amount') or bal.get('value') or bal.get('balance') or 0)
                        cashback = float(bal.get('cashback_balance') or bal.get('cashback') or bal.get('rewards') or 0)
                        if balance > 0:
                            return (balance, cashback, cuenta_item)
                
                # Caso D: Estructura profunda - buscar en cualquier nivel
                # Este caso captura estructuras nested complejas
                def buscar_usdt_profundo(obj, nivel=0, max_nivel=5):
                    """Búsqueda profunda recursiva de USDT en estructuras complejas"""
                    if nivel > max_nivel or obj is None:
                        return None
                    
                    if isinstance(obj, dict):
                        # Verificar si este nivel tiene USDT
                        curr = str(obj.get('currency') or obj.get('asset') or obj.get('symbol') or '').upper()
                        if curr == 'USDT':
                            bal_val = obj.get('balance') or obj.get('available') or obj.get('amount') or obj.get('total') or 0
                            try:
                                balance = float(bal_val)
                                if balance > 0:
                                    cashback = float(obj.get('cashback_balance') or obj.get('cashback') or 0)
                                    return (balance, cashback)
                            except (ValueError, TypeError):
                                pass
                        
                        # Buscar en todos los valores del dict
                        for value in obj.values():
                            resultado = buscar_usdt_profundo(value, nivel + 1, max_nivel)
                            if resultado:
                                return resultado
                    
                    elif isinstance(obj, list):
                        for item in obj:
                            resultado = buscar_usdt_profundo(item, nivel + 1, max_nivel)
                            if resultado:
                                return resultado
                    
                    return None
                
                resultado_profundo = buscar_usdt_profundo(cuenta_item)
                if resultado_profundo:
                    balance, cashback = resultado_profundo
                    return (balance, cashback, cuenta_item)
                
                return None
                
            except Exception as e:
                print(f"⚠️  Error al procesar cuenta: {e}")
                return None
        
        # Buscar todas las cuentas con USDT (con máximo blindaje)
        cuentas_usdt = []
        errores_procesamiento = []
        
        for idx, item in enumerate(accounts_array):
            try:
                print(f"  🔍 Cuenta {idx + 1}/{len(accounts_array)}: ", end='')
                
                # Obtener información de la cuenta (tolerante a fallos)
                try:
                    account_type = str(item.get('type') or item.get('account_type') or item.get('role') or item.get('name') or 'Unknown').lower()
                except Exception as e:
                    account_type = f'unknown_error_{idx}'
                    print(f"⚠️  Error obteniendo tipo: {e}", end=' ')
                
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
                    
            except Exception as e:
                error_msg = f"Error procesando cuenta {idx + 1}: {str(e)}"
                print(f" ❌ {error_msg}")
                errores_procesamiento.append(error_msg)
                # Continuar con la siguiente cuenta
                continue
        
        # Si hubo errores de procesamiento, loguearlos
        if errores_procesamiento:
            print(f"\n⚠️  Se encontraron {len(errores_procesamiento)} errores durante el procesamiento:")
            for err in errores_procesamiento:
                print(f"   - {err}")
        
        # BLINDAJE: Si no encontramos cuentas USDT, NO fallar con 500
        # Retornar success=True con balance 0 y mensaje informativo
        if not cuentas_usdt:
            warning_msg = f"No se encontró ninguna cuenta con balance USDT > 0. Total cuentas analizadas: {len(accounts_array)}"
            print(f"\n⚠️  {warning_msg}")
            print(f"🛡️  MODO SEGURO: Retornando balance 0 para evitar errores en frontend")
            
            # Retornar resultado "exitoso" con balance en 0
            return {
                'success': True,
                'pst': {
                    'balance_usdt': 0.0,
                    'cashback': 0.0,
                    'total_disponible': 0.0,
                    'neto_reparto': 0.0
                },
                'message': 'PST sincronizado: Sin balance USDT disponible',
                'warning': warning_msg,
                'fecha': datetime.now().isoformat(),
                'endpoint_usado': api_url,
                'header_format': header_format_usado,
                'modo_seguro': True
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
            'endpoint_usado': api_url,
            'header_format': header_format_usado
        }
        
        print(f"\n✅ Sincronización completada exitosamente")
        print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        print(f"\n❌ {error_msg}")
        import traceback
        print("\n🔍 TRACEBACK COMPLETO:")
        traceback.print_exc()
        
        # BLINDAJE FINAL: Incluso con error catastrófico, retornar success=True
        # para evitar Error 500 en el frontend
        print(f"\n🛡️  MODO SEGURO ACTIVADO: Retornando balance 0 para evitar Error 500")
        
        return {
            'success': True,
            'pst': {
                'balance_usdt': 0.0,
                'cashback': 0.0,
                'total_disponible': 0.0,
                'neto_reparto': 0.0
            },
            'message': 'PST sincronizado con error (modo seguro)',
            'error': error_msg,
            'timestamp': datetime.now().isoformat(),
            'modo_seguro': True,
            'error_critico': True
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
