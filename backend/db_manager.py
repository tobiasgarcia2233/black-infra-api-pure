#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - DATABASE MANAGER
========================================
Gestión de todas las consultas a Supabase

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 2.0.0
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

from utils import formato_argentino


# ============================================================================
# CONFIGURACIÓN DE SUPABASE
# ============================================================================

def inicializar_supabase() -> Client:
    """
    Inicializa y configura el cliente de Supabase.
    
    Returns:
        Client: Cliente de Supabase configurado
    """
    # Obtener ruta absoluta del archivo .env
    SCRIPT_DIR = Path(__file__).resolve().parent
    ROOT_DIR = SCRIPT_DIR.parent
    ENV_PATH = ROOT_DIR / '.env'
    
    print(f"📁 Cargando .env desde: {ENV_PATH}")
    
    # Cargar variables de entorno
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
        print("✅ Archivo .env encontrado")
    else:
        print(f"❌ ERROR: Archivo .env no encontrado en {ENV_PATH}")
        sys.exit(1)
    
    # Obtener credenciales
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Validar credenciales
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)
    
    # Limpiar credenciales
    SUPABASE_URL = SUPABASE_URL.strip().strip('"').strip("'")
    SUPABASE_KEY = SUPABASE_KEY.strip().strip('"').strip("'")
    
    print("✅ Variables de Supabase cargadas")
    print(f"   Supabase URL: {SUPABASE_URL}")
    
    # Crear cliente
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Cliente Supabase creado exitosamente")
        return supabase
    except Exception as e:
        print(f"❌ ERROR al crear cliente Supabase: {e}")
        sys.exit(1)


# ============================================================================
# CONSULTAS DE DATOS
# ============================================================================

def get_dolar_blue() -> dict:
    """
    Obtiene la cotización del dólar blue desde DolarAPI.
    Guarda los valores en la tabla 'cotizaciones' de Supabase.
    
    Returns:
        dict: {'compra': float, 'venta': float, 'fecha': str} o {'error': str}
    """
    try:
        print("💱 Consultando cotización del dólar blue...")
        
        url = 'https://dolarapi.com/v1/dolares/blue'
        headers = {
            'User-Agent': 'BLACK-Infrastructure-Bot/2.0',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        compra = float(data['compra'])
        venta = float(data['venta'])
        fecha_api = data.get('fechaActualizacion', datetime.now().isoformat())
        
        print(f"✅ Dólar Blue - Compra: ${compra:,.2f} | Venta: ${venta:,.2f}")
        
        # Guardar en Supabase (no crítico)
        try:
            supabase = inicializar_supabase()
            cotizacion_data = {
                'tipo': 'dolar_blue',
                'compra': compra,
                'venta': venta,
                'created_at': datetime.now().isoformat()
            }
            supabase.table('cotizaciones').insert(cotizacion_data).execute()
            print("💾 Cotización guardada en Supabase")
        except Exception as e:
            print(f"⚠️ Warning: No se pudo guardar cotización: {e}")
        
        return {
            'compra': compra,
            'venta': venta,
            'fecha': datetime.now().isoformat(),
            'fecha_api': fecha_api
        }
        
    except Exception as e:
        print(f"❌ Error al obtener cotización: {e}")
        return {'error': str(e)}


def get_resumen_financiero(supabase: Client) -> dict:
    """
    Calcula el resumen financiero de Enero 2026.
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        dict: Resumen con ingresos, costos y neto
    """
    try:
        start_date = '2026-01-01'
        end_date = '2026-01-31'
        
        print(f"📊 Consultando ingresos de Enero 2026...")
        
        # Consultar ingresos
        ingresos_response = supabase.table('ingresos') \
            .select('monto_ars, monto_usd_total, fecha_cobro') \
            .gte('fecha_cobro', start_date) \
            .lte('fecha_cobro', end_date) \
            .execute()
        
        if not hasattr(ingresos_response, 'data') or ingresos_response.data is None:
            raise Exception("Respuesta inválida de la tabla ingresos")
        
        # Calcular totales
        total_ars = 0.0
        total_usd = 0.0
        cotizaciones_aplicadas = []
        
        for ingreso in ingresos_response.data:
            monto_ars = ingreso.get('monto_ars', 0)
            monto_usd_total = ingreso.get('monto_usd_total', 0)
            
            ars_valor = None
            usd_valor = None
            
            if monto_ars:
                try:
                    if isinstance(monto_ars, str):
                        monto_ars = monto_ars.replace('.', '').replace(',', '.')
                    ars_valor = float(monto_ars)
                    total_ars += ars_valor
                except (ValueError, TypeError):
                    pass
            
            if monto_usd_total:
                try:
                    if isinstance(monto_usd_total, str):
                        monto_usd_total = monto_usd_total.replace('.', '').replace(',', '.')
                    usd_valor = float(monto_usd_total)
                    total_usd += usd_valor
                except (ValueError, TypeError):
                    pass
            
            if ars_valor and usd_valor and usd_valor > 0:
                cotizaciones_aplicadas.append(ars_valor / usd_valor)
        
        cotizacion_promedio = sum(cotizaciones_aplicadas) / len(cotizaciones_aplicadas) if cotizaciones_aplicadas else 0.0
        
        print(f"💰 Ingresos - ARS: ${total_ars:,.2f} | USD: ${total_usd:,.2f}")
        
        # Consultar costos con lógica dinámica
        print(f"💸 Consultando costos de Enero 2026...")
        costos_agrupados = get_costos_agrupados(supabase, start_date, end_date)
        
        if 'error' in costos_agrupados:
            total_costos = 0.0
        else:
            total_costos = costos_agrupados.get('total_general', 0.0)
        
        dolar_usado = costos_agrupados.get('dolar_actual', get_valor_dolar(supabase))
        
        print(f"📉 Costos USD: ${total_costos:,.2f}")
        
        neto_usd = total_usd - total_costos
        
        print(f"✅ Neto USD: ${neto_usd:,.2f}")
        
        return {
            'total_ars': total_ars,
            'total_usd': total_usd,
            'total_costos': total_costos,
            'neto_ars': total_ars,
            'neto_usd': neto_usd,
            'cotizacion_promedio': cotizacion_promedio,
            'dolar_conversion_costos': dolar_usado,
            'registros_ingresos': len(ingresos_response.data),
            'fecha_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"❌ Error en get_resumen_financiero: {e}")
        return {'error': str(e)}


def get_clientes_activos(supabase: Client) -> list:
    """
    Obtiene la lista de clientes activos.
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        list: Lista de clientes activos o {'error': str}
    """
    try:
        print("📋 Consultando clientes activos...")
        response = supabase.table('clientes').select('id, nombre, honorario_usd, estado').eq('activo', True).execute()
        
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Respuesta inválida de la tabla clientes")
        
        print(f"✅ {len(response.data)} clientes activos encontrados")
        return response.data
        
    except Exception as e:
        print(f"❌ Error en get_clientes_activos: {e}")
        return {'error': str(e)}


def get_ultimos_costos(supabase: Client, limite: int = 5) -> list:
    """
    Obtiene los últimos costos registrados.
    
    Args:
        supabase: Cliente de Supabase
        limite: Cantidad de costos a obtener
    
    Returns:
        list: Lista de costos o {'error': str}
    """
    try:
        print(f"📋 Consultando últimos {limite} costos...")
        
        response = supabase.table('costos') \
            .select('id, nombre, monto_usd, tipo, observacion, created_at') \
            .order('created_at', desc=True) \
            .limit(limite) \
            .execute()
        
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Respuesta inválida de la tabla costos")
        
        print(f"✅ {len(response.data)} costos encontrados")
        return response.data
        
    except Exception as e:
        print(f"❌ Error en get_ultimos_costos: {e}")
        return {'error': str(e)}


def get_valor_dolar(supabase: Client) -> float:
    """
    Obtiene el valor del dólar desde la tabla de configuración.
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        float: Valor del dólar o 1500.0 por defecto
    """
    try:
        response = supabase.table('configuracion') \
            .select('valor_numerico') \
            .eq('clave', 'dolar_conversion') \
            .single() \
            .execute()
        
        if response.data:
            return float(response.data.get('valor_numerico', 1500.0))
        
        return 1500.0
    except Exception as e:
        print(f"⚠️ Error al obtener valor del dólar, usando default: {e}")
        return 1500.0


def calcular_costo_agustin(supabase: Client) -> dict:
    """
    Calcula el costo de Agustín basado en clientes activos.
    Fórmula: cantidad_clientes_activos × $55 USD
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        dict: {cantidad_clientes, honorario_unitario, total_usd}
    """
    try:
        # Obtener cantidad de clientes activos
        response = supabase.table('clientes') \
            .select('id', count='exact') \
            .eq('activo', True) \
            .execute()
        
        cantidad_clientes = response.count if hasattr(response, 'count') else 0
        honorario_unitario = 55.0  # Fijo por ahora, podría venir de configuración
        total_usd = cantidad_clientes * honorario_unitario
        
        print(f"💰 Costo Agustín: {cantidad_clientes} clientes × ${honorario_unitario} = ${total_usd:.2f} USD")
        
        return {
            'cantidad_clientes': cantidad_clientes,
            'honorario_unitario': honorario_unitario,
            'total_usd': total_usd
        }
    except Exception as e:
        print(f"❌ Error al calcular costo de Agustín: {e}")
        return {
            'cantidad_clientes': 0,
            'honorario_unitario': 55.0,
            'total_usd': 0.0
        }


def get_costos_agrupados(supabase: Client, start_date: str = '2026-01-01', end_date: str = '2026-01-31') -> dict:
    """
    Obtiene los costos agrupados por tipo para un período específico.
    
    Args:
        supabase: Cliente de Supabase
        start_date: Fecha de inicio (YYYY-MM-DD)
        end_date: Fecha de fin (YYYY-MM-DD)
    
    Returns:
        dict: Costos agrupados por tipo con totales
    """
    try:
        dolar_actual = get_valor_dolar(supabase)
        print(f"📊 Consultando costos agrupados desde {start_date} hasta {end_date}...")
        print(f"💱 Usando dólar: ${dolar_actual:,.2f}")
        
        response = supabase.table('costos') \
            .select('nombre, monto_ars, monto_usd, tipo, observacion, es_calculo_dinamico') \
            .gte('created_at', start_date) \
            .lte('created_at', end_date) \
            .order('tipo, nombre') \
            .execute()
        
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Respuesta inválida de la tabla costos")
        
        # Agrupar por tipo con cálculos dinámicos
        agrupados = {
            'Fijo': [],
            'Variable': [],
            'total_fijo': 0.0,
            'total_variable': 0.0,
            'total_general': 0.0,
            'dolar_actual': dolar_actual
        }
        
        for costo in response.data:
            nombre = costo.get('nombre')
            tipo = costo.get('tipo', 'Variable')
            es_dinamico = costo.get('es_calculo_dinamico', False)
            
            # Calcular monto USD según el tipo de costo
            if nombre == 'Agustin' or es_dinamico:
                # Cálculo dinámico para Agustín
                calc_agustin = calcular_costo_agustin(supabase)
                monto = calc_agustin['total_usd']
                observacion = f"{calc_agustin['cantidad_clientes']} clientes × ${calc_agustin['honorario_unitario']} USD"
            elif costo.get('monto_ars'):
                # Conversión ARS → USD
                monto = round(costo['monto_ars'] / dolar_actual, 2)
                observacion = costo.get('observacion', '')
            else:
                # Monto fijo en USD
                monto = float(costo.get('monto_usd', 0))
                observacion = costo.get('observacion', '')
            
            item = {
                'nombre': nombre,
                'monto_usd': monto,
                'monto_ars': costo.get('monto_ars'),
                'observacion': observacion,
                'es_dinamico': es_dinamico
            }
            
            if tipo == 'Fijo':
                agrupados['Fijo'].append(item)
                agrupados['total_fijo'] += monto
            else:
                agrupados['Variable'].append(item)
                agrupados['total_variable'] += monto
            
            agrupados['total_general'] += monto
        
        print(f"✅ Costos calculados - Fijo: ${agrupados['total_fijo']:,.2f} | Variable: ${agrupados['total_variable']:,.2f} | Total: ${agrupados['total_general']:,.2f}")
        
        return agrupados
        
    except Exception as e:
        print(f"❌ Error en get_costos_agrupados: {e}")
        return {'error': str(e)}


def get_ultimos_ingresos(supabase: Client, limite: int = 10) -> list:
    """
    Obtiene los últimos ingresos con información del cliente.
    
    Args:
        supabase: Cliente de Supabase
        limite: Cantidad de ingresos a obtener
    
    Returns:
        list: Lista de ingresos con cliente o {'error': str}
    """
    try:
        print(f"📋 Consultando últimos {limite} ingresos...")
        
        response = supabase.table('ingresos') \
            .select('id, cliente_id, monto_usd_total, monto_ars, fecha_cobro, created_at') \
            .order('created_at', desc=True) \
            .limit(limite) \
            .execute()
        
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Respuesta inválida de la tabla ingresos")
        
        print(f"🔍 DEBUG: {len(response.data)} ingresos obtenidos")
        
        # Obtener nombres de clientes
        ingresos_con_cliente = []
        for ingreso in response.data:
            cliente_id = ingreso.get('cliente_id')
            
            if cliente_id:
                try:
                    cliente_response = supabase.table('clientes') \
                        .select('nombre') \
                        .eq('id', cliente_id) \
                        .execute()
                    
                    if cliente_response.data and len(cliente_response.data) > 0:
                        ingreso['cliente_nombre'] = cliente_response.data[0].get('nombre', 'Cliente desconocido')
                    else:
                        ingreso['cliente_nombre'] = 'Cliente desconocido'
                except:
                    ingreso['cliente_nombre'] = 'Cliente desconocido'
            else:
                ingreso['cliente_nombre'] = 'Sin cliente'
            
            ingresos_con_cliente.append(ingreso)
        
        print(f"✅ {len(ingresos_con_cliente)} ingresos encontrados")
        return ingresos_con_cliente
        
    except Exception as e:
        print(f"❌ Error en get_ultimos_ingresos: {e}")
        return {'error': str(e)}


def verificar_conexion_supabase(supabase: Client) -> bool:
    """
    Verifica que la conexión con Supabase funcione.
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        print("🔍 Verificando conexión con Supabase...")
        response = supabase.table('clientes').select('id').limit(1).execute()
        
        if not hasattr(response, 'data'):
            print("❌ Respuesta inválida de Supabase")
            return False
        
        print("✅ Conexión con Supabase verificada")
        return True
    except Exception as e:
        print(f"❌ Error de conexión con Supabase: {e}")
        return False
