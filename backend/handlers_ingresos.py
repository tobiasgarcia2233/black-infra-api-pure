#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - HANDLERS DE INGRESOS
============================================
Manejo de todas las operaciones relacionadas con ingresos/pagos

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 2.0.0
"""

from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from supabase import Client

from utils import limpiar_id, formato_argentino
from db_manager import get_clientes_activos, get_ultimos_ingresos, get_resumen_financiero, get_dolar_blue


# ============================================================================
# HANDLERS DE BOTONES - INGRESOS
# ============================================================================

async def handler_nuevo_pago(query, supabase: Client):
    """
    Muestra lista de clientes para registrar un nuevo pago.
    """
    await query.edit_message_text("⏳ Consultando clientes activos...")
    
    clientes = get_clientes_activos(supabase)
    
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
        return
    
    if not clientes:
        mensaje = """
📋 **NUEVO PAGO**

No hay clientes activos en el sistema.

Por favor, agrega clientes desde la interfaz web.
"""
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        return
    
    mensaje = """
📥 **NUEVO PAGO**

Selecciona el cliente que te pagó:
"""
    keyboard = []
    for cliente in clientes:
        cliente_id = cliente.get('id')
        nombre = cliente.get('nombre', 'Sin nombre')
        keyboard.append([InlineKeyboardButton(f"👤 {nombre}", callback_data=f'cliente_{cliente_id}')])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data='menu_principal')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


async def handler_cliente_seleccionado(query, context: ContextTypes.DEFAULT_TYPE, supabase: Client):
    """
    Usuario seleccionó un cliente para registrar pago.
    """
    # Extraer cliente_id del callback_data
    cliente_id = query.data.replace('cliente_', '')
    
    try:
        response = supabase.table('clientes').select('id, nombre, honorario_usd').eq('id', cliente_id).execute()
        
        if response.data and len(response.data) > 0:
            cliente = response.data[0]
            nombre_cliente = cliente.get('nombre', 'Cliente')
            honorario_sugerido = cliente.get('honorario_usd', 0)
            
            # Guardar en context para usar después
            context.user_data['cliente_pago'] = {
                'id': cliente_id,
                'nombre': nombre_cliente
            }
            context.user_data['esperando_monto'] = True
            
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


async def handler_ver_movimientos(query, supabase: Client):
    """
    Muestra los últimos movimientos/ingresos.
    """
    await query.edit_message_text("⏳ Consultando últimos movimientos...")
    
    ingresos = get_ultimos_ingresos(supabase, limite=10)
    
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
        return
    
    if not ingresos:
        mensaje = """
📜 **ÚLTIMOS MOVIMIENTOS**

No hay ingresos registrados todavía.

Usa el botón "📥 Nuevo Pago" para agregar uno.
"""
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        return
    
    # Construir lista de movimientos
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
            fecha_obj = datetime.fromisoformat(fecha_cobro.replace('Z', '+00:00'))
            fecha_fmt = fecha_obj.strftime('%d/%m/%Y')
        except:
            fecha_fmt = fecha_cobro
        
        mensaje += f"{idx}. 👤 **{cliente_nombre}**\n"
        mensaje += f"   💵 ${monto_usd:,.2f} USD | 💰 ${monto_ars:,.0f} ARS\n"
        mensaje += f"   📅 {fecha_fmt}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(f"❌ Borrar #{idx} ({cliente_nombre})", callback_data=f'borrar_ingreso_{ingreso_id}')
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


async def handler_borrar_ingreso(query, supabase: Client):
    """
    Pide confirmación para borrar un ingreso.
    """
    # Extraer ingreso_id
    ingreso_id = query.data.replace('borrar_ingreso_', '')
    
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


async def handler_confirmar_borrar_ingreso(query, supabase: Client):
    """
    Confirma y elimina un ingreso.
    """
    ingreso_id = query.data.replace('confirmar_borrar_', '')
    
    await query.edit_message_text("⏳ Eliminando registro...")
    
    try:
        supabase.table('ingresos').delete().eq('id', ingreso_id).execute()
        
        # Recalcular neto
        resumen = get_resumen_financiero(supabase)
        
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


# ============================================================================
# PROCESADORES DE TEXTO - INGRESOS
# ============================================================================

async def procesar_monto_pago(update: Update, context: ContextTypes.DEFAULT_TYPE, supabase: Client):
    """
    Procesa el monto ingresado para registrar un nuevo pago.
    """
    if not context.user_data.get('esperando_monto'):
        return
    
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
            "⚠️ *Monto inválido*\n\n"
            "Por favor, envía solo el número en USD.\n"
            "_Ejemplo: 1500_\n\n"
            "O envía /cancelar para abortar.",
            parse_mode='Markdown'
        )
        return
    
    cliente_info = context.user_data.get('cliente_pago')
    if not cliente_info:
        await update.message.reply_text(
            "❌ Error: No se encontró información del cliente.\n\n"
            "Usa /start para comenzar de nuevo."
        )
        context.user_data.clear()
        return
    
    mensaje_procesando = await update.message.reply_text(
        "⏳ Procesando pago...\n"
        "• Obteniendo cotización del dólar\n"
        "• Calculando equivalente en ARS\n"
        "• Guardando en Supabase..."
    )
    
    try:
        # Obtener cotización del dólar
        cotizacion = get_dolar_blue()
        if 'error' in cotizacion:
            print(f"⚠️ Error al obtener cotización, usando fallback")
            dolar_venta = 1500.0
        else:
            dolar_venta = cotizacion['venta']
        
        # Calcular equivalente en ARS
        monto_ars = monto_usd * dolar_venta
        
        # Guardar en la tabla ingresos
        ingreso_data = {
            'cliente_id': str(cliente_info['id']),
            'monto_usd_total': monto_usd,
            'monto_ars': monto_ars,
            'fecha_cobro': date.today().isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        supabase.table('ingresos').insert(ingreso_data).execute()
        
        # Obtener resumen actualizado
        resumen = get_resumen_financiero(supabase)
        
        if 'error' not in resumen:
            total_usd = resumen['total_usd']
            total_costos = resumen['total_costos']
            neto_usd = total_usd - total_costos
            neto_fmt = formato_argentino(neto_usd)
        else:
            neto_fmt = "N/A"
        
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
        
        context.user_data.clear()
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
