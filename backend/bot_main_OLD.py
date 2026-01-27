#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - TELEGRAM BOT
===================================
Bot de Telegram para gestión y monitoreo del Sistema BLACK

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 1.0.0
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from supabase import create_client, Client

# ============================================================================
# ESTADOS DEL CONVERSATION HANDLER
# ============================================================================

# Estados para el flujo de "Nuevo Pago"
WAITING_AMOUNT = 1

# Estados para el flujo de "Nuevo Costo"
WAITING_COSTO_NOMBRE = 2
WAITING_COSTO_MONTO = 3

# Estados para el flujo de "Editar Costo"
WAITING_EDIT_NOMBRE = 4
WAITING_EDIT_MONTO = 5

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Obtener ruta absoluta del archivo .env (un nivel arriba de backend/)
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
ENV_PATH = ROOT_DIR / '.env'

print(f"📁 Cargando .env desde: {ENV_PATH}")

# Cargar variables de entorno con ruta absoluta
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    print("✅ Archivo .env encontrado")
else:
    print(f"❌ ERROR: Archivo .env no encontrado en {ENV_PATH}")
    sys.exit(1)

# Obtener variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validar credenciales
if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN no está definido en .env")
    sys.exit(1)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
    sys.exit(1)

# Limpiar credenciales (quitar espacios y comillas)
SUPABASE_URL = SUPABASE_URL.strip().strip('"').strip("'")
SUPABASE_KEY = SUPABASE_KEY.strip().strip('"').strip("'")
TELEGRAM_TOKEN = TELEGRAM_TOKEN.strip().strip('"').strip("'")

print("✅ Variables de entorno cargadas")
print(f"   Supabase URL: {SUPABASE_URL}")
print(f"   Bot Token: {TELEGRAM_TOKEN[:20]}...")

# Crear cliente Supabase (forma simple, sin argumentos extra)
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Cliente Supabase creado exitosamente")
except Exception as e:
    print(f"❌ ERROR al crear cliente Supabase: {e}")
    sys.exit(1)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def extraer_uuid_de_callback(callback_data: str) -> str:
    """
    Extrae el UUID de un callback_data que puede tener múltiples prefijos.
    
    Args:
        callback_data: String como 'borrar_costo_UUID' o 'confirmar_borrar_costo_UUID'
    
    Returns:
        str: Solo el UUID (formato: 8-4-4-4-12 caracteres hexadecimales)
    
    Ejemplos:
        'borrar_costo_550e8400-e29b-41d4-a716-446655440000' -> '550e8400-e29b-41d4-a716-446655440000'
        'confirmar_borrar_costo_550e8400-e29b-41d4-a716-446655440000' -> '550e8400-e29b-41d4-a716-446655440000'
    """
    print(f"🔍 DEBUG extraer_uuid: Entrada completa: '{callback_data}'")
    
    # Patrón regex para UUID: 8-4-4-4-12 caracteres hexadecimales
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    
    match = re.search(uuid_pattern, callback_data, re.IGNORECASE)
    
    if match:
        uuid_limpio = match.group(0)
        print(f"✅ DEBUG extraer_uuid: UUID extraído con regex: '{uuid_limpio}'")
        return uuid_limpio
    else:
        # Fallback: buscar el último segmento que parezca un UUID
        # Esto maneja casos donde el UUID no tiene guiones
        partes = callback_data.split('_')
        print(f"⚠️  DEBUG extraer_uuid: Regex falló, usando split. Partes: {partes}")
        
        # Buscar de atrás hacia adelante la primera parte que tenga formato UUID
        for parte in reversed(partes):
            if len(parte) >= 32:  # UUID sin guiones tiene mínimo 32 caracteres
                print(f"✅ DEBUG extraer_uuid: UUID extraído con split: '{parte}'")
                return parte
        
        # Si no se encuentra nada que parezca UUID, devolver la última parte
        uuid_limpio = partes[-1]
        print(f"⚠️  DEBUG extraer_uuid: Usando última parte como fallback: '{uuid_limpio}'")
        return uuid_limpio


# ============================================================================
# FUNCIONES DE NEGOCIO
# ============================================================================

def formato_argentino(numero):
    """
    Formatea números al estilo argentino: punto para miles, coma para decimales.
    Ejemplo: 270000 -> "270.000,00"
    """
    # Formatear con separadores
    entero = int(numero)
    decimal = numero - entero
    
    # Formatear parte entera con puntos
    entero_str = f"{entero:,}".replace(',', '.')
    
    # Formatear parte decimal con coma
    decimal_str = f"{decimal:.2f}".split('.')[1]
    
    return f"{entero_str},{decimal_str}"


def get_dolar_blue():
    """
    Obtiene la cotización del dólar blue desde la API de DolarAPI.
    Guarda los valores en la tabla 'cotizaciones' de Supabase.
    
    API: https://dolarapi.com/v1/dolares/blue
    
    Returns:
        dict: Diccionario con 'compra', 'venta' y 'fecha', o 'error' si falla
    """
    try:
        print("💱 Consultando cotización del dólar blue desde DolarAPI...")
        
        # URL de la API (mucho más confiable que scraping)
        url = 'https://dolarapi.com/v1/dolares/blue'
        
        # Headers opcionales (la API no los requiere pero es buena práctica)
        headers = {
            'User-Agent': 'BLACK-Infrastructure-Bot/1.0',
            'Accept': 'application/json',
        }
        
        # Hacer la petición HTTP a la API
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parsear el JSON
        data = response.json()
        
        # Extraer valores (la API devuelve 'compra' y 'venta' directamente)
        compra = float(data['compra'])
        venta = float(data['venta'])
        fecha_api = data.get('fechaActualizacion', datetime.now().isoformat())
        
        print(f"✅ Dólar Blue (API) - Compra: ${compra:,.2f} | Venta: ${venta:,.2f}")
        
        # Intentar guardar en Supabase (no crítico - si falla, igual devolvemos los valores)
        fecha_actual = datetime.now().isoformat()
        
        try:
            cotizacion_data = {
                'tipo': 'dolar_blue',
                'compra': compra,  # Minúsculas (coincide con columna SQL)
                'venta': venta,     # Minúsculas (coincide con columna SQL)
                'created_at': fecha_actual  # Columna de timestamp en Supabase
            }
            
            # Insertar en la tabla cotizaciones
            supabase.table('cotizaciones').insert(cotizacion_data).execute()
            print(f"💾 Cotización guardada en Supabase")
            
        except Exception as e:
            # Si falla el guardado, solo mostrar warning pero continuar
            print(f"⚠️ Warning: No se pudo guardar en Supabase (caché/esquema): {e}")
            print(f"   → Continuando con valores de la API...")
        
        # Siempre devolver los valores obtenidos de la API
        return {
            'compra': compra,
            'venta': venta,
            'fecha': fecha_actual,
            'fecha_api': fecha_api
        }
        
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout al consultar DolarAPI")
        return {'error': 'Timeout al consultar la cotización'}
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar a DolarAPI")
        return {'error': 'No se pudo conectar al servicio de cotizaciones'}
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de red: {e}")
        return {'error': f'Error de red: {str(e)}'}
    
    except (KeyError, ValueError) as e:
        print(f"❌ Error al parsear la respuesta de la API: {e}")
        return {'error': f'Error al procesar la respuesta: {str(e)}'}
    
    except Exception as e:
        print(f"❌ Error al obtener cotización del dólar blue: {e}")
        return {'error': str(e)}


def get_resumen_financiero():
    """
    Calcula el resumen financiero de Enero 2026.
    Filtra ingresos por fecha_cobro y costos por created_at.
    
    Returns:
        dict: Diccionario con ingresos (ARS/USD), costos y neto por moneda
    """
    try:
        # Fechas fijas para Enero 2026
        start_date = '2026-01-01'
        end_date = '2026-01-31'
        
        print(f"📊 Consultando ingresos de Enero 2026 (fecha_cobro: {start_date} a {end_date})...")
        
        # Consultar ingresos filtrados por fecha_cobro
        ingresos_response = supabase.table('ingresos') \
            .select('monto_ars, monto_usd_total, fecha_cobro') \
            .gte('fecha_cobro', start_date) \
            .lte('fecha_cobro', end_date) \
            .execute()
        
        # Validar respuesta
        if not hasattr(ingresos_response, 'data') or ingresos_response.data is None:
            raise Exception("Respuesta inválida de la tabla ingresos")
        
        # Sumar ingresos por moneda y calcular cotización promedio aplicada
        total_ars = 0.0  # Pesos argentinos ($2.283.750,00)
        total_usd = 0.0  # Dólares ($2.700,00)
        cotizaciones_aplicadas = []  # Para calcular el promedio
        
        for ingreso in ingresos_response.data:
            # monto_ars -> total_ars (Pesos argentinos)
            monto_ars = ingreso.get('monto_ars', 0)
            monto_usd_total = ingreso.get('monto_usd_total', 0)
            
            # Variables para el cálculo de cotización
            ars_valor = None
            usd_valor = None
            
            if monto_ars is not None and monto_ars != 0:
                try:
                    # Limpiar si viene como string
                    if isinstance(monto_ars, str):
                        monto_ars = monto_ars.replace('.', '').replace(',', '.')
                    ars_valor = float(monto_ars)
                    total_ars += ars_valor
                except (ValueError, TypeError):
                    pass
            
            # monto_usd_total -> total_usd (Dólares)
            if monto_usd_total is not None and monto_usd_total != 0:
                try:
                    # Limpiar si viene como string
                    if isinstance(monto_usd_total, str):
                        monto_usd_total = monto_usd_total.replace('.', '').replace(',', '.')
                    usd_valor = float(monto_usd_total)
                    total_usd += usd_valor
                except (ValueError, TypeError):
                    pass
            
            # Calcular cotización aplicada si hay ambos valores
            if ars_valor and usd_valor and usd_valor > 0:
                cotizacion_aplicada = ars_valor / usd_valor
                cotizaciones_aplicadas.append(cotizacion_aplicada)
        
        # Calcular cotización promedio aplicada
        cotizacion_promedio = 0.0
        if cotizaciones_aplicadas:
            cotizacion_promedio = sum(cotizaciones_aplicadas) / len(cotizaciones_aplicadas)
            print(f"💱 Cotización Promedio Aplicada: ${cotizacion_promedio:,.2f} (de {len(cotizaciones_aplicadas)} ingresos)")
        
        print(f"💰 Ingresos - ARS: ${total_ars:,.2f} | USD: ${total_usd:,.2f}")
        
        # Consultar costos filtrados por created_at (Enero 2026)
        print(f"💸 Consultando costos de Enero 2026 (created_at: {start_date} a {end_date})...")
        costos_response = supabase.table('costos') \
            .select('monto_usd') \
            .gte('created_at', start_date) \
            .lte('created_at', end_date) \
            .execute()
        
        # Validar respuesta
        if not hasattr(costos_response, 'data') or costos_response.data is None:
            raise Exception("Respuesta inválida de la tabla costos")
        
        # Sumar costos filtrados por fecha en USD
        total_costos = 0.0
        for costo in costos_response.data:
            monto_usd = costo.get('monto_usd', 0)
            if monto_usd is not None and monto_usd != 0:
                try:
                    # Limpiar si viene como string
                    if isinstance(monto_usd, str):
                        monto_usd = monto_usd.replace('.', '').replace(',', '.')
                    total_costos += float(monto_usd)
                except (ValueError, TypeError):
                    continue
        
        print(f"📉 Costos USD: ${total_costos:,.2f}")
        
        # Calcular neto USD
        neto_usd = total_usd - total_costos
        
        print(f"✅ Neto - ARS: ${total_ars:,.2f} | USD: ${neto_usd:,.2f}")
        
        return {
            'total_ars': total_ars,
            'total_usd': total_usd,
            'total_costos': total_costos,
            'neto_ars': total_ars,  # ARS solo tiene ingresos
            'neto_usd': neto_usd,
            'cotizacion_promedio': cotizacion_promedio,  # Cotización promedio aplicada
            'registros_ingresos': len(ingresos_response.data),
            'registros_costos': len(costos_response.data),
            'fecha_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"❌ Error en get_resumen_financiero: {e}")
        return {
            'error': str(e)
        }


def get_clientes_activos():
    """
    Obtiene la lista de clientes activos.
    
    Returns:
        list: Lista de clientes activos
    """
    try:
        print("📋 Consultando clientes activos...")
        response = supabase.table('clientes').select('id, nombre, honorario_usd, estado').eq('activo', True).execute()
        
        # Validar respuesta
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Respuesta inválida de la tabla clientes")
        
        print(f"✅ {len(response.data)} clientes activos encontrados")
        return response.data
        
    except Exception as e:
        print(f"❌ Error en get_clientes_activos: {e}")
        return {'error': str(e)}


def verificar_conexion_supabase():
    """
    Verifica que la conexión con Supabase funcione correctamente.
    
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        # Hacer una query simple (con .execute() al final)
        print("🔍 Verificando conexión con Supabase...")
        response = supabase.table('clientes').select('id').limit(1).execute()
        
        # Validar respuesta
        if not hasattr(response, 'data'):
            print("❌ Respuesta inválida de Supabase")
            return False
        
        print("✅ Conexión con Supabase verificada")
        return True
    except Exception as e:
        print(f"❌ Error de conexión con Supabase: {e}")
        return False


def get_ultimos_costos(limite=5):
    """
    Obtiene los últimos costos registrados.
    
    Args:
        limite (int): Cantidad de costos a obtener (default: 5)
    
    Returns:
        list: Lista de costos, o dict con error
    """
    try:
        print(f"📋 Consultando últimos {limite} costos...")
        
        # Obtener los últimos costos ordenados por created_at descendente
        response = supabase.table('costos') \
            .select('id, nombre, monto_usd, created_at') \
            .order('created_at', desc=True) \
            .limit(limite) \
            .execute()
        
        # Validar respuesta
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Respuesta inválida de la tabla costos")
        
        print(f"✅ {len(response.data)} costos encontrados")
        return response.data
        
    except Exception as e:
        print(f"❌ Error en get_ultimos_costos: {e}")
        return {'error': str(e)}


def get_ultimos_ingresos(limite=10):
    """
    Obtiene los últimos ingresos registrados con información del cliente.
    
    Args:
        limite (int): Cantidad de ingresos a obtener (default: 10)
    
    Returns:
        list: Lista de ingresos con información del cliente, o dict con error
    """
    try:
        print(f"📋 Consultando últimos {limite} ingresos...")
        
        # Obtener los últimos ingresos ordenados por created_at descendente (más nuevo primero)
        # Sin filtros de fecha para mostrar TODOS los ingresos, incluyendo los de hoy
        response = supabase.table('ingresos') \
            .select('id, cliente_id, monto_usd_total, monto_ars, fecha_cobro, created_at') \
            .order('created_at', desc=True) \
            .limit(limite) \
            .execute()
        
        # Validar respuesta
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Respuesta inválida de la tabla ingresos")
        
        # Debug: Mostrar cuántos ingresos se obtuvieron
        print(f"🔍 DEBUG: Se obtuvieron {len(response.data)} ingresos de Supabase")
        
        # Obtener información de clientes para cada ingreso
        ingresos_con_cliente = []
        for ingreso in response.data:
            cliente_id = ingreso.get('cliente_id')
            
            # Obtener nombre del cliente
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


# ============================================================================
# HANDLERS DE COMANDOS
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /start
    Muestra el menú principal con botones interactivos
    """
    user = update.effective_user
    
    # Verificar conexión con Supabase
    conexion_ok = verificar_conexion_supabase()
    
    mensaje = f"""
🚀 **BLACK INFRASTRUCTURE SYSTEM**

¡Hola {user.first_name}! 👋

Sistema operativo y conectado.

**Estado del Sistema:**
✅ Bot de Telegram: Activo
{"✅ Supabase: Conectado" if conexion_ok else "❌ Supabase: Error de conexión"}

---
Selecciona una opción del menú:
"""
    
    # Crear botones inline
    keyboard = [
        [InlineKeyboardButton("📊 Resumen Enero", callback_data='ver_resumen')],
        [InlineKeyboardButton("📥 Nuevo Pago", callback_data='nuevo_pago')],
        [InlineKeyboardButton("💸 Nuevo Costo", callback_data='nuevo_costo')],
        [InlineKeyboardButton("👥 Ver Clientes", callback_data='ver_clientes')],
        [InlineKeyboardButton("📜 Últimos Movimientos", callback_data='ver_movimientos')],
        [InlineKeyboardButton("⚙️ Gestionar Costos", callback_data='gestionar_costos')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


async def resumen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /resumen
    Muestra el resumen financiero de Enero 2026 con cotizaciones diferenciadas y patrimonio real
    """
    # Enviar mensaje de "procesando"
    mensaje_procesando = await update.message.reply_text("⏳ Consultando datos de Enero 2026 y cotización del dólar...")
    
    # Obtener resumen financiero (incluye cotización promedio aplicada)
    resumen = get_resumen_financiero()
    
    # Obtener cotización de mercado actual del dólar blue (con fallback a 1500.0)
    cotizacion_dolar = get_dolar_blue()
    if 'error' in cotizacion_dolar:
        print(f"⚠️ Error al obtener dólar blue, usando fallback: {cotizacion_dolar['error']}")
        dolar_mercado = 1500.0  # Fallback actualizado a 1500
    else:
        dolar_mercado = cotizacion_dolar['venta']
    
    if 'error' in resumen:
        mensaje = f"""
❌ *ERROR AL CONSULTAR DATOS*

No se pudo obtener el resumen financiero.

*Detalle del error:*
`{resumen['error']}`
"""
    else:
        # Extraer valores del resumen
        total_ars = resumen['total_ars']
        total_usd = resumen['total_usd']
        total_costos = resumen['total_costos']
        
        # UTILIDAD NETA: Solo la caja real de USDT (USD - Costos)
        utilidad_neta_usdt = total_usd - total_costos
        
        # EQUIVALENTE en USDT: Cuánto valdrían los pesos si los cambiaras HOY
        pesos_en_usdt = total_ars / dolar_mercado
        
        # Formatear con estilo argentino
        ars_fmt = formato_argentino(total_ars).split(',')[0]  # Sin decimales para ARS
        usd_fmt = formato_argentino(total_usd)
        costos_fmt = formato_argentino(total_costos)
        
        # RESULTADO ESTRELLA: Utilidad neta en USDT (la caja real)
        neto_fmt = formato_argentino(utilidad_neta_usdt)
        
        # Datos informativos
        dolar_blue_fmt = formato_argentino(dolar_mercado)
        pesos_en_usd_fmt = formato_argentino(pesos_en_usdt)
        
        mensaje = f"""
🚀 *ESTADO DE RESULTADOS - ENERO 2026*

📈 **INGRESOS:**
💰 Ingresos ARS: ${ars_fmt}
💵 Ingresos USD: ${usd_fmt}

📉 **EGRESOS:**
💸 Costos USD: ${costos_fmt}

---
💎 **UTILIDAD NETA (USDT):** ${neto_fmt}
---

ℹ️ *Datos adicionales:*
🏦 Dólar Blue: ${dolar_blue_fmt}
🪙 Equivalente Pesos: ${pesos_en_usd_fmt} USDT
   _(Si los cambiaras hoy)_
"""
    
    # Editar mensaje de procesando con el resultado
    await mensaje_procesando.edit_text(mensaje, parse_mode='Markdown')


async def clientes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /clientes
    Lista los clientes activos
    """
    # Enviar mensaje de "procesando"
    mensaje_procesando = await update.message.reply_text("⏳ Consultando clientes activos...")
    
    # Obtener clientes
    clientes = get_clientes_activos()
    
    if isinstance(clientes, dict) and 'error' in clientes:
        mensaje = f"""
❌ **ERROR AL CONSULTAR CLIENTES**

**Detalle del error:**
`{clientes['error']}`
"""
    else:
        if not clientes:
            mensaje = """
📋 **CLIENTES ACTIVOS**

No hay clientes activos en el sistema.
"""
        else:
            # Construir lista de clientes
            lista_clientes = []
            total_honorarios = 0
            
            for idx, cliente in enumerate(clientes, 1):
                nombre = cliente.get('nombre', 'Sin nombre')
                honorario = float(cliente.get('honorario_usd', 0) or 0)
                estado = cliente.get('estado', 'Desconocido')
                
                total_honorarios += honorario
                
                # Emoji según estado
                emoji = "✅" if estado.lower() == 'activo' else "⚠️"
                
                lista_clientes.append(
                    f"{idx}. {emoji} **{nombre}**\n"
                    f"   💵 ${honorario:,.2f} USD | {estado}"
                )
            
            clientes_texto = "\n\n".join(lista_clientes)
            
            mensaje = f"""
📋 **CLIENTES ACTIVOS**

**Total de clientes:** {len(clientes)}
**Ingresos potenciales:** ${total_honorarios:,.2f} USD

---

{clientes_texto}

---
Sistema BLACK
"""
    
    # Editar mensaje de procesando con el resultado
    await mensaje_procesando.edit_text(mensaje, parse_mode='Markdown')


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para los botones inline (CallbackQuery)
    Maneja todas las interacciones con los botones del menú
    """
    query = update.callback_query
    
    # Responder al callback para quitar el "reloj de carga"
    await query.answer()
    
    # Obtener el callback_data
    callback_data = query.data
    
    if callback_data == 'ver_resumen':
        # Ejecutar lógica de resumen financiero
        await query.edit_message_text("⏳ Consultando datos de Enero 2026 y cotización del dólar...")
        
        # Obtener resumen financiero (incluye cotización promedio aplicada)
        resumen = get_resumen_financiero()
        
        # Obtener cotización de mercado actual del dólar blue (con fallback a 1500.0)
        cotizacion_dolar = get_dolar_blue()
        if 'error' in cotizacion_dolar:
            print(f"⚠️ Error al obtener dólar blue, usando fallback: {cotizacion_dolar['error']}")
            dolar_mercado = 1500.0  # Fallback actualizado a 1500
        else:
            dolar_mercado = cotizacion_dolar['venta']
        
        if 'error' in resumen:
            mensaje = f"""
❌ *ERROR AL CONSULTAR DATOS*

No se pudo obtener el resumen financiero.

*Detalle del error:*
`{resumen['error']}`
"""
        else:
            # Extraer valores del resumen
            total_ars = resumen['total_ars']
            total_usd = resumen['total_usd']
            total_costos = resumen['total_costos']
            
            # UTILIDAD NETA: Solo la caja real de USDT (USD - Costos)
            utilidad_neta_usdt = total_usd - total_costos
            
            # EQUIVALENTE en USDT: Cuánto valdrían los pesos si los cambiaras HOY
            pesos_en_usdt = total_ars / dolar_mercado
            
            # Formatear con estilo argentino
            ars_fmt = formato_argentino(total_ars).split(',')[0]  # Sin decimales para ARS
            usd_fmt = formato_argentino(total_usd)
            costos_fmt = formato_argentino(total_costos)
            
            # RESULTADO ESTRELLA: Utilidad neta en USDT (la caja real)
            neto_fmt = formato_argentino(utilidad_neta_usdt)
            
            # Datos informativos
            dolar_blue_fmt = formato_argentino(dolar_mercado)
            pesos_en_usd_fmt = formato_argentino(pesos_en_usdt)
            
            mensaje = f"""
🚀 *ESTADO DE RESULTADOS - ENERO 2026*

📈 **INGRESOS:**
💰 Ingresos ARS: ${ars_fmt}
💵 Ingresos USD: ${usd_fmt}

📉 **EGRESOS:**
💸 Costos USD: ${costos_fmt}

---
💎 **UTILIDAD NETA (USDT):** ${neto_fmt}
---

ℹ️ *Datos adicionales:*
🏦 Dólar Blue: ${dolar_blue_fmt}
🪙 Equivalente Pesos: ${pesos_en_usd_fmt} USDT
   _(Si los cambiaras hoy)_
"""
        
        # Agregar botón de volver al menú
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data == 'ver_clientes':
        # Ejecutar lógica de clientes
        await query.edit_message_text("⏳ Consultando clientes activos...")
        
        # Obtener clientes
        clientes = get_clientes_activos()
        
        if isinstance(clientes, dict) and 'error' in clientes:
            mensaje = f"""
❌ **ERROR AL CONSULTAR CLIENTES**

**Detalle del error:**
`{clientes['error']}`
"""
        else:
            if not clientes:
                mensaje = """
📋 **CLIENTES ACTIVOS**

No hay clientes activos en el sistema.
"""
            else:
                # Construir lista de clientes
                lista_clientes = []
                total_honorarios = 0
                
                for idx, cliente in enumerate(clientes, 1):
                    nombre = cliente.get('nombre', 'Sin nombre')
                    honorario = float(cliente.get('honorario_usd', 0) or 0)
                    estado = cliente.get('estado', 'Desconocido')
                    
                    total_honorarios += honorario
                    
                    # Emoji según estado
                    emoji = "✅" if estado.lower() == 'activo' else "⚠️"
                    
                    lista_clientes.append(
                        f"{idx}. {emoji} **{nombre}**\n"
                        f"   💵 ${honorario:,.2f} USD | {estado}"
                    )
                
                clientes_texto = "\n\n".join(lista_clientes)
                
                mensaje = f"""
📋 **CLIENTES ACTIVOS**

**Total de clientes:** {len(clientes)}
**Ingresos potenciales:** ${total_honorarios:,.2f} USD

---

{clientes_texto}

---
Sistema BLACK
"""
        
        # Agregar botón de volver al menú
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data == 'nuevo_pago':
        # Mostrar lista de clientes activos
        await query.edit_message_text("⏳ Consultando clientes activos...")
        
        # Obtener clientes activos
        clientes = get_clientes_activos()
        
        if isinstance(clientes, dict) and 'error' in clientes:
            mensaje = f"""
❌ **ERROR AL CONSULTAR CLIENTES**

No se pudo cargar la lista de clientes.

**Detalle del error:**
`{clientes['error']}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
        elif not clientes:
            mensaje = """
📋 **NUEVO PAGO**

No hay clientes activos en el sistema.

Por favor, agrega clientes desde la interfaz web.
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
        else:
            # Crear botones con los nombres de los clientes
            mensaje = """
📥 **NUEVO PAGO**

Selecciona el cliente que te pagó:
"""
            keyboard = []
            for cliente in clientes:
                cliente_id = cliente.get('id')
                nombre = cliente.get('nombre', 'Sin nombre')
                # Callback format: cliente_{id}
                keyboard.append([InlineKeyboardButton(f"👤 {nombre}", callback_data=f'cliente_{cliente_id}')])
            
            # Agregar botón de cancelar
            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data='menu_principal')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data.startswith('cliente_'):
        # Usuario seleccionó un cliente para registrar pago
        cliente_id = callback_data.replace('cliente_', '')
        
        # Obtener información del cliente
        try:
            response = supabase.table('clientes').select('id, nombre, honorario_usd').eq('id', cliente_id).execute()
            
            if response.data and len(response.data) > 0:
                cliente = response.data[0]
                nombre_cliente = cliente.get('nombre', 'Cliente')
                honorario_sugerido = cliente.get('honorario_usd', 0)
                
                # Guardar en context.user_data para usarlo después
                context.user_data['cliente_pago'] = {
                    'id': cliente_id,
                    'nombre': nombre_cliente
                }
                context.user_data['esperando_monto'] = True
                
                # Pedir el monto
                mensaje = f"""
💵 **REGISTRAR PAGO DE: {nombre_cliente}**

¿Cuánto cobraste de {nombre_cliente}?

💡 *Honorario habitual:* ${honorario_sugerido:,.2f} USD

📝 Responde solo el número en USD.
_Ejemplo: 1500_

❌ Envía /cancelar para abortar.
"""
                await query.edit_message_text(mensaje, parse_mode='Markdown')
            
            else:
                raise Exception(f"Cliente con ID {cliente_id} no encontrado")
        
        except Exception as e:
            mensaje = f"""
❌ **ERROR AL CARGAR CLIENTE**

No se pudo obtener la información del cliente.

**Error:** `{str(e)}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data == 'nuevo_costo':
        # Iniciar flujo de nuevo costo
        context.user_data['esperando_costo_nombre'] = True
        
        mensaje = """
💸 **NUEVO COSTO**

¿En qué se gastó?

💡 *Ejemplos:*
• Sueldo
• Servidor
• Publicidad
• Hosting
• Software

📝 Responde con el nombre del gasto.

❌ Envía /cancelar para abortar.
"""
        await query.edit_message_text(mensaje, parse_mode='Markdown')
    
    elif callback_data == 'ver_movimientos':
        # Mostrar últimos movimientos
        await query.edit_message_text("⏳ Consultando últimos movimientos...")
        
        # Obtener últimos 10 ingresos (sin filtros de fecha)
        ingresos = get_ultimos_ingresos(limite=10)
        
        if isinstance(ingresos, dict) and 'error' in ingresos:
            mensaje = f"""
❌ **ERROR AL CONSULTAR MOVIMIENTOS**

No se pudieron cargar los movimientos.

**Detalle del error:**
`{ingresos['error']}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
        elif not ingresos:
            mensaje = """
📜 **ÚLTIMOS MOVIMIENTOS**

No hay ingresos registrados todavía.

Usa el botón "📥 Nuevo Pago" para agregar uno.
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
        else:
            # Construir lista de movimientos con botones de borrar
            mensaje = "📜 **ÚLTIMOS MOVIMIENTOS**\n\n"
            mensaje += f"_Mostrando los {len(ingresos)} ingresos más recientes:_\n\n"
            
            keyboard = []
            for idx, ingreso in enumerate(ingresos, 1):
                ingreso_id = ingreso.get('id')
                cliente_nombre = ingreso.get('cliente_nombre', 'Sin cliente')
                monto_usd = ingreso.get('monto_usd_total', 0)
                monto_ars = ingreso.get('monto_ars', 0)
                fecha_cobro = ingreso.get('fecha_cobro', 'N/A')
                
                # Formatear fecha
                try:
                    from datetime import datetime
                    fecha_obj = datetime.fromisoformat(fecha_cobro.replace('Z', '+00:00'))
                    fecha_fmt = fecha_obj.strftime('%d/%m/%Y')
                except:
                    fecha_fmt = fecha_cobro
                
                # Agregar al mensaje
                mensaje += f"{idx}. 👤 **{cliente_nombre}**\n"
                mensaje += f"   💵 ${monto_usd:,.2f} USD | 💰 ${monto_ars:,.0f} ARS\n"
                mensaje += f"   📅 {fecha_fmt}\n\n"
                
                # Botón de borrar para este ingreso
                keyboard.append([
                    InlineKeyboardButton(f"❌ Borrar #{idx} ({cliente_nombre})", callback_data=f'borrar_ingreso_{ingreso_id}')
                ])
            
            # Botón de volver
            keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data.startswith('borrar_ingreso_'):
        # Usuario quiere borrar un ingreso - pedir confirmación
        ingreso_id = callback_data.replace('borrar_ingreso_', '')
        
        # Obtener información del ingreso
        try:
            response = supabase.table('ingresos') \
                .select('id, cliente_id, monto_usd_total, monto_ars, fecha_cobro') \
                .eq('id', ingreso_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                ingreso = response.data[0]
                monto_usd = ingreso.get('monto_usd_total', 0)
                cliente_id = ingreso.get('cliente_id')
                
                # Obtener nombre del cliente
                cliente_nombre = 'Cliente desconocido'
                if cliente_id:
                    try:
                        cliente_response = supabase.table('clientes') \
                            .select('nombre') \
                            .eq('id', cliente_id) \
                            .execute()
                        if cliente_response.data and len(cliente_response.data) > 0:
                            cliente_nombre = cliente_response.data[0].get('nombre', 'Cliente desconocido')
                    except:
                        pass
                
                # Pedir confirmación
                mensaje = f"""
⚠️ **CONFIRMAR ELIMINACIÓN**

¿Estás seguro de que quieres eliminar este ingreso?

👤 **Cliente:** {cliente_nombre}
💵 **Monto:** ${monto_usd:,.2f} USD

Esta acción NO se puede deshacer.
"""
                keyboard = [
                    [InlineKeyboardButton("✅ Sí, eliminar", callback_data=f'confirmar_borrar_{ingreso_id}')],
                    [InlineKeyboardButton("❌ No, cancelar", callback_data='ver_movimientos')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
            
            else:
                raise Exception(f"Ingreso con ID {ingreso_id} no encontrado")
        
        except Exception as e:
            mensaje = f"""
❌ **ERROR AL CARGAR INGRESO**

No se pudo obtener la información del ingreso.

**Error:** `{str(e)}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data='ver_movimientos')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data.startswith('confirmar_borrar_'):
        # Usuario confirmó la eliminación
        ingreso_id = callback_data.replace('confirmar_borrar_', '')
        
        await query.edit_message_text("⏳ Eliminando registro...")
        
        try:
            # Eliminar el ingreso
            supabase.table('ingresos').delete().eq('id', ingreso_id).execute()
            
            # Recalcular el neto
            resumen = get_resumen_financiero()
            
            if 'error' not in resumen:
                total_usd = resumen['total_usd']
                total_costos = resumen['total_costos']
                neto_usd = total_usd - total_costos
                neto_fmt = formato_argentino(neto_usd)
            else:
                neto_fmt = "N/A"
            
            mensaje = f"""
✅ **REGISTRO ELIMINADO**

El ingreso ha sido eliminado exitosamente.

El neto ha sido recalculado:

💎 **NETO USDT ACTUALIZADO:** ${neto_fmt}
"""
            keyboard = [
                [InlineKeyboardButton("📜 Ver Movimientos", callback_data='ver_movimientos')],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data='menu_principal')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
        except Exception as e:
            mensaje = f"""
❌ **ERROR AL ELIMINAR**

No se pudo eliminar el registro.

**Error:** `{str(e)}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data='ver_movimientos')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data == 'gestionar_costos':
        # Mostrar últimos costos con opciones de editar/borrar
        await query.edit_message_text("⏳ Consultando costos...")
        
        costos = get_ultimos_costos(limite=5)
        
        if isinstance(costos, dict) and 'error' in costos:
            mensaje = f"""
❌ **ERROR AL CONSULTAR COSTOS**

No se pudieron cargar los costos.

**Detalle del error:**
`{costos['error']}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
        elif not costos:
            mensaje = """
⚙️ **GESTIONAR COSTOS**

No hay costos registrados todavía.

Usa el botón "💸 Nuevo Costo" para agregar uno.
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
        else:
            mensaje = "⚙️ **GESTIONAR COSTOS**\n\n"
            mensaje += f"_Mostrando los {len(costos)} costos más recientes:_\n\n"
            
            keyboard = []
            for idx, costo in enumerate(costos, 1):
                costo_id = costo.get('id')
                print(f"🔍 DEBUG LISTADO: Costo #{idx} - ID original de Supabase: '{costo_id}' (tipo: {type(costo_id).__name__}, longitud: {len(str(costo_id)) if costo_id else 'N/A'})")
                
                nombre = costo.get('nombre', 'Sin nombre')
                monto_usd = costo.get('monto_usd', 0)
                created_at = costo.get('created_at', 'N/A')
                
                # Formatear fecha
                try:
                    fecha_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    fecha_fmt = fecha_obj.strftime('%d/%m/%Y')
                except:
                    fecha_fmt = created_at
                
                mensaje += f"{idx}. 💸 **{nombre}**\n"
                mensaje += f"   💵 ${monto_usd:,.2f} USD\n"
                mensaje += f"   📅 {fecha_fmt}\n\n"
                
                # Botones de editar y borrar para cada costo
                callback_editar = f'editar_costo_{costo_id}'
                callback_borrar = f'borrar_costo_{costo_id}'
                print(f"🔍 DEBUG LISTADO: Creando botones - editar: '{callback_editar}', borrar: '{callback_borrar}'")
                
                keyboard.append([
                    InlineKeyboardButton(f"✏️ Editar #{idx}", callback_data=callback_editar),
                    InlineKeyboardButton(f"🗑️ Borrar #{idx}", callback_data=callback_borrar)
                ])
            
            # Botón de volver
            keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data.startswith('editar_costo_'):
        # Usuario quiere editar un costo
        print(f"🔍 DEBUG EDITAR: callback_data original: '{callback_data}'")
        
        # Limpiar el ID: extraer solo el UUID del callback_data
        costo_id = query.data.split('_')[-1]
        
        print(f"🔍 DEBUG EDITAR: ID limpio para Supabase: '{costo_id}'")
        print(f"🔍 DEBUG EDITAR: Longitud del ID: {len(costo_id)}")
        
        try:
            print(f"🔍 DEBUG EDITAR: Ejecutando query .eq('id', '{costo_id}')")
            response = supabase.table('costos').select('id, nombre, monto_usd').eq('id', costo_id).execute()
            
            if response.data and len(response.data) > 0:
                costo = response.data[0]
                nombre = costo.get('nombre', 'Sin nombre')
                monto_usd = costo.get('monto_usd', 0)
                
                mensaje = f"""
✏️ **EDITAR COSTO**

💸 *Nombre actual:* {nombre}
💵 *Monto actual:* ${monto_usd:,.2f} USD

¿Qué deseas cambiar?
"""
                keyboard = [
                    [InlineKeyboardButton("📝 Cambiar Nombre", callback_data=f'edit_nombre_{costo_id}')],
                    [InlineKeyboardButton("💰 Cambiar Monto", callback_data=f'edit_monto_{costo_id}')],
                    [InlineKeyboardButton("❌ Cancelar", callback_data='gestionar_costos')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                raise Exception(f"Costo con ID {costo_id} no encontrado")
        
        except Exception as e:
            mensaje = f"""
❌ **ERROR AL CARGAR COSTO**

No se pudo obtener la información del costo.

**Error:** `{str(e)}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data='gestionar_costos')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data.startswith('edit_nombre_'):
        # Pedir nuevo nombre
        print(f"🔍 DEBUG EDIT_NOMBRE: callback_data original: '{callback_data}'")
        
        # Limpiar el ID: extraer solo el UUID del callback_data
        costo_id = query.data.split('_')[-1]
        
        print(f"🔍 DEBUG EDIT_NOMBRE: ID limpio: '{costo_id}'")
        print(f"🔍 DEBUG EDIT_NOMBRE: Guardando en context.user_data")
        context.user_data['costo_id_editar'] = costo_id
        context.user_data['esperando_edit_nombre'] = True
        
        mensaje = """
📝 **CAMBIAR NOMBRE DEL COSTO**

Envía el nuevo nombre para este costo.

❌ Envía /cancelar para abortar.
"""
        await query.edit_message_text(mensaje, parse_mode='Markdown')
    
    elif callback_data.startswith('edit_monto_'):
        # Pedir nuevo monto
        print(f"🔍 DEBUG EDIT_MONTO: callback_data original: '{callback_data}'")
        
        # Limpiar el ID: extraer solo el UUID del callback_data
        costo_id = query.data.split('_')[-1]
        
        print(f"🔍 DEBUG EDIT_MONTO: ID limpio: '{costo_id}'")
        print(f"🔍 DEBUG EDIT_MONTO: Guardando en context.user_data")
        context.user_data['costo_id_editar'] = costo_id
        context.user_data['esperando_edit_monto'] = True
        
        mensaje = """
💰 **CAMBIAR MONTO DEL COSTO**

Envía el nuevo monto en USD.

_Ejemplo: 500_

❌ Envía /cancelar para abortar.
"""
        await query.edit_message_text(mensaje, parse_mode='Markdown')
    
    elif callback_data.startswith('borrar_costo_'):
        # Pedir confirmación para borrar
        print(f"🔍 DEBUG BORRAR: callback_data original: '{callback_data}'")
        
        # Limpiar el ID: extraer solo el UUID del callback_data
        costo_id = query.data.split('_')[-1]
        
        print(f"🔍 DEBUG BORRAR: ID limpio para Supabase: '{costo_id}'")
        print(f"🔍 DEBUG BORRAR: Longitud del ID: {len(costo_id)}")
        
        try:
            print(f"🔍 DEBUG BORRAR: Ejecutando query .eq('id', '{costo_id}')")
            response = supabase.table('costos').select('id, nombre, monto_usd').eq('id', costo_id).execute()
            
            if response.data and len(response.data) > 0:
                costo = response.data[0]
                nombre = costo.get('nombre', 'Sin nombre')
                monto_usd = costo.get('monto_usd', 0)
                
                mensaje = f"""
⚠️ **CONFIRMAR ELIMINACIÓN**

¿Estás seguro de que quieres eliminar este costo?

💸 **Nombre:** {nombre}
💵 **Monto:** ${monto_usd:,.2f} USD

Esta acción NO se puede deshacer.
"""
                # Crear callback_data para botón de confirmación
                callback_confirmar = f'confirmar_borrar_costo_{costo_id}'
                print(f"🔍 DEBUG: callback_data para botón de confirmación: '{callback_confirmar}'")
                
                keyboard = [
                    [InlineKeyboardButton("✅ Sí, eliminar", callback_data=callback_confirmar)],
                    [InlineKeyboardButton("❌ No, cancelar", callback_data='gestionar_costos')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                raise Exception(f"Costo con ID {costo_id} no encontrado")
        
        except Exception as e:
            mensaje = f"""
❌ **ERROR AL CARGAR COSTO**

No se pudo obtener la información del costo.

**Error:** `{str(e)}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data='gestionar_costos')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data.startswith('confirmar_borrar_costo_'):
        # Eliminar el costo
        print(f"🔍 DEBUG CONFIRMAR: callback_data original: '{callback_data}'")
        
        # Limpiar el ID: extraer solo el UUID del callback_data
        # Ejemplo: 'confirmar_borrar_costo_UUID' -> 'UUID'
        costo_id = query.data.split('_')[-1]
        
        print(f"🔍 DEBUG CONFIRMAR: ID limpio para Supabase: '{costo_id}'")
        print(f"🔍 DEBUG CONFIRMAR: Longitud del ID: {len(costo_id)}")
        
        await query.edit_message_text("⏳ Eliminando costo...")
        
        try:
            print(f"🔍 DEBUG CONFIRMAR: Ejecutando DELETE .eq('id', '{costo_id}')")
            supabase.table('costos').delete().eq('id', costo_id).execute()
            
            # Recalcular neto
            resumen = get_resumen_financiero()
            
            if 'error' not in resumen:
                total_usd = resumen['total_usd']
                total_costos = resumen['total_costos']
                neto_usd = total_usd - total_costos
                neto_fmt = formato_argentino(neto_usd)
            else:
                neto_fmt = "N/A"
            
            mensaje = f"""
✅ **COSTO ELIMINADO**

El costo ha sido eliminado exitosamente.

El neto ha sido recalculado:

💎 **NETO USDT ACTUALIZADO:** ${neto_fmt}
"""
            keyboard = [
                [InlineKeyboardButton("⚙️ Gestionar Costos", callback_data='gestionar_costos')],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data='menu_principal')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
        except Exception as e:
            mensaje = f"""
❌ **ERROR AL ELIMINAR**

No se pudo eliminar el costo.

**Error:** `{str(e)}`
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data='gestionar_costos')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data == 'sincronizar_pst':
        # Sincronizar pagos de PST.NET
        await query.edit_message_text("🔄 Consultando pagos pendientes en PST.NET...")
        
        try:
            from pst_net_integration import (
                verificar_configuracion_pst_net,
                sincronizar_pagos_pst_net
            )
            
            # Verificar configuración
            if not verificar_configuracion_pst_net():
                mensaje = """
⚠️ **CONFIGURACIÓN INCOMPLETA**

Las credenciales de PST.NET no están configuradas.

Por favor, configura las siguientes variables en `.env`:
• PST_NET_API_URL
• PST_NET_API_KEY
• PST_NET_SECRET (opcional)

Consulta el README.md para más información.
"""
                keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
                return
            
            # Ejecutar sincronización
            resultados = sincronizar_pagos_pst_net(supabase)
            
            total = resultados['total']
            exitosos = resultados['exitosos']
            fallidos = resultados['fallidos']
            
            if total == 0:
                mensaje = """
ℹ️ **SINCRONIZACIÓN COMPLETADA**

No hay pagos pendientes de sincronizar.

Todos los pagos de PST.NET ya están registrados en Supabase.
"""
            else:
                emoji = "✅" if fallidos == 0 else "⚠️"
                mensaje = f"""
{emoji} **SINCRONIZACIÓN COMPLETADA**

📊 **Resultados:**
• Total de pagos: {total}
• Sincronizados: {exitosos} ✅
• Fallidos: {fallidos} ❌

Los ingresos han sido registrados en Supabase.
"""
            
            keyboard = [
                [InlineKeyboardButton("📊 Ver Resumen", callback_data='ver_resumen')],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data='menu_principal')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            print(f"❌ Error en sincronizar_pst: {e}")
            mensaje = f"""
❌ **ERROR AL SINCRONIZAR**

Ocurrió un error durante la sincronización:

`{str(e)}`

Revisa los logs del bot para más detalles.
"""
            keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif callback_data == 'menu_principal':
        # Volver al menú principal
        user = update.effective_user
        conexion_ok = verificar_conexion_supabase()
        
        mensaje = f"""
🚀 **BLACK INFRASTRUCTURE SYSTEM**

¡Hola {user.first_name}! 👋

Sistema operativo y conectado.

**Estado del Sistema:**
✅ Bot de Telegram: Activo
{"✅ Supabase: Conectado" if conexion_ok else "❌ Supabase: Error de conexión"}

---
Selecciona una opción del menú:
"""
        
        # Crear botones inline
        keyboard = [
            [InlineKeyboardButton("📊 Resumen Enero", callback_data='ver_resumen')],
            [InlineKeyboardButton("📥 Nuevo Pago", callback_data='nuevo_pago')],
            [InlineKeyboardButton("💸 Nuevo Costo", callback_data='nuevo_costo')],
            [InlineKeyboardButton("👥 Ver Clientes", callback_data='ver_clientes')],
            [InlineKeyboardButton("📜 Últimos Movimientos", callback_data='ver_movimientos')],
            [InlineKeyboardButton("⚙️ Gestionar Costos", callback_data='gestionar_costos')],
            [InlineKeyboardButton("🔄 Sincronizar PST.NET", callback_data='sincronizar_pst')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


async def procesar_texto_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa mensajes de texto del usuario para diferentes flujos:
    - Monto de pago
    - Nombre de costo
    - Monto de costo
    - Edición de costo
    """
    # Verificar si estamos en algún flujo
    if context.user_data.get('esperando_monto'):
        await procesar_monto_pago(update, context)
    elif context.user_data.get('esperando_costo_nombre'):
        await procesar_nombre_costo(update, context)
    elif context.user_data.get('esperando_costo_monto'):
        await procesar_monto_costo(update, context)
    elif context.user_data.get('esperando_edit_nombre'):
        await procesar_editar_nombre_costo(update, context)
    elif context.user_data.get('esperando_edit_monto'):
        await procesar_editar_monto_costo(update, context)
    # Si no está en ningún flujo, ignorar


async def procesar_monto_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el monto ingresado por el usuario para registrar un nuevo pago
    """
    # Verificar si estamos esperando un monto
    if not context.user_data.get('esperando_monto'):
        return  # Ignorar si no estamos en flujo de pago
    
    # Obtener el texto del mensaje
    texto = update.message.text.strip()
    
    # Verificar si el usuario canceló
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Operación cancelada.\n\nUsa /start para volver al menú principal.",
            parse_mode='Markdown'
        )
        return
    
    # Validar que sea un número
    try:
        monto_usd = float(texto.replace(',', '.'))
        if monto_usd <= 0:
            raise ValueError("El monto debe ser mayor a 0")
    except ValueError:
        await update.message.reply_text(
            "⚠️ *Monto inválido*\n\n"
            "Por favor, envía solo el número en USD.\n"
            "_Ejemplo: 1500_\n\n"
            "O envía /cancelar para abortar.",
            parse_mode='Markdown'
        )
        return
    
    # Obtener información del cliente guardada
    cliente_info = context.user_data.get('cliente_pago')
    if not cliente_info:
        await update.message.reply_text(
            "❌ Error: No se encontró información del cliente.\n\n"
            "Usa /start para comenzar de nuevo.",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return
    
    # Enviar mensaje de procesamiento
    mensaje_procesando = await update.message.reply_text(
        "⏳ Procesando pago...\n"
        "• Obteniendo cotización del dólar\n"
        "• Calculando equivalente en ARS\n"
        "• Guardando en Supabase..."
    )
    
    try:
        # 1. Obtener cotización actual del dólar blue
        cotizacion = get_dolar_blue()
        if 'error' in cotizacion:
            print(f"⚠️ Error al obtener cotización, usando fallback")
            dolar_venta = 1500.0
        else:
            dolar_venta = cotizacion['venta']
        
        # 2. Calcular equivalente en ARS
        monto_ars = monto_usd * dolar_venta
        
        # 3. Guardar en la tabla ingresos
        from datetime import date
        
        ingreso_data = {
            'cliente_id': str(cliente_info['id']),  # UUID como string, no como int
            'monto_usd_total': monto_usd,
            'monto_ars': monto_ars,
            'fecha_cobro': date.today().isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        # Insertar en Supabase
        supabase.table('ingresos').insert(ingreso_data).execute()
        
        # 4. Obtener nuevo resumen financiero actualizado
        resumen = get_resumen_financiero()
        
        if 'error' not in resumen:
            total_usd = resumen['total_usd']
            total_costos = resumen['total_costos']
            neto_usd = total_usd - total_costos
            neto_fmt = formato_argentino(neto_usd)
        else:
            neto_fmt = "N/A"
        
        # 5. Mensaje de confirmación
        mensaje_exito = f"""
✅ **PAGO REGISTRADO EXITOSAMENTE**

👤 *Cliente:* {cliente_info['nombre']}
💵 *Monto USD:* ${monto_usd:,.2f}
💱 *Cotización:* ${dolar_venta:,.2f}
💰 *Equivalente ARS:* ${monto_ars:,.0f}
📅 *Fecha:* {date.today().strftime('%d/%m/%Y')}

---
💎 **NETO USDT ACTUALIZADO:** ${neto_fmt}
---

Usa /start para volver al menú principal.
"""
        
        # Limpiar el contexto
        context.user_data.clear()
        
        # Editar mensaje de procesamiento con el resultado
        await mensaje_procesando.edit_text(mensaje_exito, parse_mode='Markdown')
        
    except Exception as e:
        print(f"❌ Error al procesar pago: {e}")
        context.user_data.clear()
        
        await mensaje_procesando.edit_text(
            f"❌ **ERROR AL PROCESAR PAGO**\n\n"
            f"No se pudo guardar el pago.\n\n"
            f"**Error:** `{str(e)}`\n\n"
            f"Usa /start para volver al menú principal.",
            parse_mode='Markdown'
        )


async def procesar_nombre_costo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el nombre ingresado para un nuevo costo
    """
    texto = update.message.text.strip()
    
    # Verificar si el usuario canceló
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Operación cancelada.\n\nUsa /start para volver al menú principal.",
            parse_mode='Markdown'
        )
        return
    
    # Guardar el nombre del costo
    context.user_data['costo_nombre'] = texto
    context.user_data['esperando_costo_nombre'] = False
    context.user_data['esperando_costo_monto'] = True
    
    # Pedir el monto
    mensaje = f"""
💸 **NUEVO COSTO: {texto}**

¿Cuánto se pagó en USD?

📝 Responde solo el número en USD.
_Ejemplo: 500_

❌ Envía /cancelar para abortar.
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')


async def procesar_monto_costo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el monto ingresado para un nuevo costo
    """
    texto = update.message.text.strip()
    
    # Verificar si el usuario canceló
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Operación cancelada.\n\nUsa /start para volver al menú principal.",
            parse_mode='Markdown'
        )
        return
    
    # Validar que sea un número
    try:
        monto_usd = float(texto.replace(',', '.'))
        if monto_usd <= 0:
            raise ValueError("El monto debe ser mayor a 0")
    except ValueError:
        await update.message.reply_text(
            "⚠️ *Monto inválido*\n\n"
            "Por favor, envía solo el número en USD.\n"
            "_Ejemplo: 500_\n\n"
            "O envía /cancelar para abortar.",
            parse_mode='Markdown'
        )
        return
    
    # Obtener nombre del costo
    costo_nombre = context.user_data.get('costo_nombre', 'Sin nombre')
    
    # Enviar mensaje de procesamiento
    mensaje_procesando = await update.message.reply_text(
        "⏳ Guardando costo en Supabase..."
    )
    
    try:
        # Guardar en la tabla costos
        costo_data = {
            'nombre': costo_nombre,
            'monto_usd': monto_usd,
            'created_at': datetime.now().isoformat()
        }
        
        supabase.table('costos').insert(costo_data).execute()
        
        # Obtener resumen actualizado
        resumen = get_resumen_financiero()
        
        if 'error' not in resumen:
            total_usd = resumen['total_usd']
            total_costos = resumen['total_costos']
            neto_usd = total_usd - total_costos
            neto_fmt = formato_argentino(neto_usd)
        else:
            neto_fmt = "N/A"
        
        # Mensaje de éxito
        mensaje_exito = f"""
✅ **COSTO REGISTRADO EXITOSAMENTE**

💸 *Concepto:* {costo_nombre}
💵 *Monto:* ${monto_usd:,.2f} USD
📅 *Fecha:* {datetime.now().strftime('%d/%m/%Y')}

---
💎 **NETO USDT ACTUALIZADO:** ${neto_fmt}
---

Usa /start para volver al menú principal.
"""
        
        # Limpiar contexto
        context.user_data.clear()
        
        await mensaje_procesando.edit_text(mensaje_exito, parse_mode='Markdown')
        
    except Exception as e:
        print(f"❌ Error al guardar costo: {e}")
        context.user_data.clear()
        
        await mensaje_procesando.edit_text(
            f"❌ **ERROR AL GUARDAR COSTO**\n\n"
            f"No se pudo guardar el costo.\n\n"
            f"**Error:** `{str(e)}`\n\n"
            f"Usa /start para volver al menú principal.",
            parse_mode='Markdown'
        )


async def procesar_editar_nombre_costo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el nuevo nombre para editar un costo
    """
    texto = update.message.text.strip()
    
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Operación cancelada.\n\nUsa /start para volver al menú principal."
        )
        return
    
    costo_id = context.user_data.get('costo_id_editar')
    print(f"🔍 DEBUG PROCESAR_NOMBRE: ID recuperado de context: '{costo_id}'")
    
    if not costo_id:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Error: No se encontró el ID del costo.\n\n"
            "Usa /start para comenzar de nuevo."
        )
        return
    
    # El ID ya debería estar limpio, pero lo convertimos a string por si acaso
    costo_id = str(costo_id)
    print(f"🔍 DEBUG PROCESAR_NOMBRE: ID para UPDATE: '{costo_id}'")
    print(f"🔍 DEBUG PROCESAR_NOMBRE: Nuevo nombre: '{texto}'")
    
    try:
        # Actualizar en Supabase
        print(f"🔍 DEBUG PROCESAR_NOMBRE: Ejecutando UPDATE .eq('id', '{costo_id}')")
        supabase.table('costos').update({'nombre': texto}).eq('id', costo_id).execute()
        
        context.user_data.clear()
        
        await update.message.reply_text(
            f"✅ **COSTO ACTUALIZADO**\n\n"
            f"El nombre del costo ha sido cambiado a:\n"
            f"💸 *{texto}*\n\n"
            f"Usa /start para volver al menú principal.",
            parse_mode='Markdown'
        )
    except Exception as e:
        context.user_data.clear()
        await update.message.reply_text(
            f"❌ **ERROR**\n\nNo se pudo actualizar: {str(e)}\n\n"
            f"Usa /start para volver al menú principal."
        )


async def procesar_editar_monto_costo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el nuevo monto para editar un costo
    """
    texto = update.message.text.strip()
    
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Operación cancelada.\n\nUsa /start para volver al menú principal."
        )
        return
    
    try:
        monto_usd = float(texto.replace(',', '.'))
        if monto_usd <= 0:
            raise ValueError("El monto debe ser mayor a 0")
    except ValueError:
        await update.message.reply_text(
            "⚠️ Monto inválido. Envía un número mayor a 0 o /cancelar."
        )
        return
    
    costo_id = context.user_data.get('costo_id_editar')
    print(f"🔍 DEBUG PROCESAR_MONTO: ID recuperado de context: '{costo_id}'")
    
    if not costo_id:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Error: No se encontró el ID del costo.\n\n"
            "Usa /start para comenzar de nuevo."
        )
        return
    
    # El ID ya debería estar limpio, pero lo convertimos a string por si acaso
    costo_id = str(costo_id)
    print(f"🔍 DEBUG PROCESAR_MONTO: ID para UPDATE: '{costo_id}'")
    print(f"🔍 DEBUG PROCESAR_MONTO: Nuevo monto: {monto_usd}")
    
    try:
        # Actualizar en Supabase
        print(f"🔍 DEBUG PROCESAR_MONTO: Ejecutando UPDATE .eq('id', '{costo_id}')")
        supabase.table('costos').update({'monto_usd': monto_usd}).eq('id', costo_id).execute()
        
        context.user_data.clear()
        
        await update.message.reply_text(
            f"✅ **COSTO ACTUALIZADO**\n\n"
            f"El monto del costo ha sido cambiado a:\n"
            f"💵 ${monto_usd:,.2f} USD\n\n"
            f"Usa /start para volver al menú principal.",
            parse_mode='Markdown'
        )
    except Exception as e:
        context.user_data.clear()
        await update.message.reply_text(
            f"❌ **ERROR**\n\nNo se pudo actualizar: {str(e)}\n\n"
            f"Usa /start para volver al menú principal."
        )


async def sincronizar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /sincronizar
    Sincroniza pagos pendientes desde PST.NET
    """
    # Enviar mensaje de inicio
    mensaje_procesando = await update.message.reply_text(
        "🔄 **SINCRONIZACIÓN PST.NET**\n\n"
        "Consultando pagos pendientes...",
        parse_mode='Markdown'
    )
    
    try:
        # Importar módulo de integración PST.NET
        from pst_net_integration import (
            verificar_configuracion_pst_net,
            sincronizar_pagos_pst_net
        )
        
        # Verificar configuración
        if not verificar_configuracion_pst_net():
            await mensaje_procesando.edit_text(
                "⚠️ **CONFIGURACIÓN INCOMPLETA**\n\n"
                "Las credenciales de PST.NET no están configuradas.\n\n"
                "Por favor, configura las siguientes variables en `.env`:\n"
                "• PST_NET_API_URL\n"
                "• PST_NET_API_KEY\n"
                "• PST_NET_SECRET (opcional)\n\n"
                "Consulta el README.md para más información.",
                parse_mode='Markdown'
            )
            return
        
        # Ejecutar sincronización
        resultados = sincronizar_pagos_pst_net(supabase)
        
        # Mensaje de resultado
        total = resultados['total']
        exitosos = resultados['exitosos']
        fallidos = resultados['fallidos']
        
        if total == 0:
            mensaje = """
ℹ️ **SINCRONIZACIÓN COMPLETADA**

No hay pagos pendientes de sincronizar.

Todos los pagos de PST.NET ya están registrados en Supabase.
"""
        else:
            # Emoji según resultado
            emoji = "✅" if fallidos == 0 else "⚠️"
            
            mensaje = f"""
{emoji} **SINCRONIZACIÓN COMPLETADA**

📊 **Resultados:**
• Total de pagos: {total}
• Sincronizados: {exitosos} ✅
• Fallidos: {fallidos} ❌

Los ingresos han sido registrados en Supabase.

Usa /resumen para ver el estado actualizado.
"""
        
        await mensaje_procesando.edit_text(mensaje, parse_mode='Markdown')
        
    except ImportError as e:
        await mensaje_procesando.edit_text(
            "❌ **ERROR**\n\n"
            "No se pudo cargar el módulo de PST.NET.\n\n"
            "Verifica que el archivo `pst_net_integration.py` esté en la carpeta backend.",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"❌ Error en sincronizar_command: {e}")
        await mensaje_procesando.edit_text(
            f"❌ **ERROR AL SINCRONIZAR**\n\n"
            f"Ocurrió un error durante la sincronización:\n\n"
            f"`{str(e)}`\n\n"
            f"Revisa los logs del bot para más detalles.",
            parse_mode='Markdown'
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler global de errores
    """
    print(f"❌ Error en el bot: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Ocurrió un error al procesar tu solicitud. "
            "Por favor, intenta de nuevo más tarde."
        )


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """
    Función principal que inicia el bot
    """
    print("\n" + "="*70)
    print("🤖 INICIANDO BOT DE TELEGRAM - SISTEMA BLACK")
    print("="*70 + "\n")
    
    try:
        # Crear aplicación (compatible con python-telegram-bot 20.8)
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Registrar handlers de comandos
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("resumen", resumen_command))
        application.add_handler(CommandHandler("clientes", clientes_command))
        application.add_handler(CommandHandler("sincronizar", sincronizar_command))
        
        # Registrar handler de botones (CallbackQuery)
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Registrar handler de mensajes de texto (para todos los flujos: pagos, costos, edición)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_texto_usuario))
        
        # Registrar handler de errores
        application.add_error_handler(error_handler)
        
        print("✅ Bot configurado correctamente")
        print("📡 Esperando mensajes...\n")
        print("💡 Presiona Ctrl+C para detener el bot\n")
        
        # Iniciar bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Bot detenido por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
