#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - HANDLERS DE COSTOS
==========================================
Manejo de todas las operaciones relacionadas con costos

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 2.0.0
"""

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from supabase import Client

from utils import limpiar_id, formato_argentino
from db_manager import get_ultimos_costos, get_resumen_financiero, get_costos_agrupados


# ============================================================================
# HANDLERS DE BOTONES - COSTOS
# ============================================================================

async def handler_gestionar_costos(query, supabase: Client):
    """
    Muestra los costos agrupados por tipo (Fijo/Variable).
    """
    await query.edit_message_text("⏳ Consultando costos...")
    
    # Obtener costos agrupados de Enero 2026
    costos_agrupados = get_costos_agrupados(supabase)
    
    if isinstance(costos_agrupados, dict) and 'error' in costos_agrupados:
        mensaje = f"""
❌ **ERROR AL CONSULTAR COSTOS**

No se pudieron cargar los costos.

**Detalle del error:**
`{costos_agrupados['error']}`
"""
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        return
    
    total_fijo = costos_agrupados.get('total_fijo', 0)
    total_variable = costos_agrupados.get('total_variable', 0)
    total_general = costos_agrupados.get('total_general', 0)
    costos_fijos = costos_agrupados.get('Fijo', [])
    costos_variables = costos_agrupados.get('Variable', [])
    
    if not costos_fijos and not costos_variables:
        mensaje = """
⚙️ **GESTIONAR COSTOS**

No hay costos registrados todavía.

Usa el botón "💸 Nuevo Costo" para agregar uno.
"""
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        return
    
    # Construir mensaje con costos agrupados
    mensaje = f"⚙️ **GESTIONAR COSTOS - ENERO 2026**\n\n"
    mensaje += f"💰 **TOTAL: ${total_general:,.2f} USD**\n\n"
    
    # Costos Fijos
    if costos_fijos:
        mensaje += f"📊 **COSTOS FIJOS** (${total_fijo:,.2f})\n"
        for costo in costos_fijos:
            nombre = costo.get('nombre')
            monto = costo.get('monto_usd', 0)
            obs = costo.get('observacion', '')
            mensaje += f"  • {nombre}: ${monto:,.2f}"
            if obs:
                mensaje += f" _{obs}_"
            mensaje += "\n"
        mensaje += "\n"
    
    # Costos Variables
    if costos_variables:
        mensaje += f"💸 **COSTOS VARIABLES** (${total_variable:,.2f})\n"
        for costo in costos_variables:
            nombre = costo.get('nombre')
            monto = costo.get('monto_usd', 0)
            obs = costo.get('observacion', '')
            mensaje += f"  • {nombre}: ${monto:,.2f}"
            if obs:
                mensaje += f" _{obs}_"
            mensaje += "\n"
    
    mensaje += "\n---\n_Sistema BLACK Infrastructure_"
    
    # Botón de volver
    keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


async def handler_editar_costo(query, supabase: Client):
    """
    Muestra opciones para editar un costo (nombre o monto).
    """
    # CRÍTICO: Limpiar el ID usando la función segura
    costo_id = limpiar_id(query.data)
    print(f"🔍 [EDITAR] ID limpio: '{costo_id}' (longitud: {len(costo_id)})")
    
    try:
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


async def handler_edit_nombre(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Solicita el nuevo nombre para un costo.
    """
    # CRÍTICO: Limpiar el ID
    costo_id = limpiar_id(query.data)
    print(f"🔍 [EDIT_NOMBRE] ID limpio guardado en context: '{costo_id}'")
    
    context.user_data['costo_id_editar'] = costo_id
    context.user_data['esperando_edit_nombre'] = True
    
    mensaje = """
📝 **CAMBIAR NOMBRE DEL COSTO**

Envía el nuevo nombre para este costo.

❌ Envía /cancelar para abortar.
"""
    await query.edit_message_text(mensaje, parse_mode='Markdown')


async def handler_edit_monto(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Solicita el nuevo monto para un costo.
    """
    # CRÍTICO: Limpiar el ID
    costo_id = limpiar_id(query.data)
    print(f"🔍 [EDIT_MONTO] ID limpio guardado en context: '{costo_id}'")
    
    context.user_data['costo_id_editar'] = costo_id
    context.user_data['esperando_edit_monto'] = True
    
    mensaje = """
💰 **CAMBIAR MONTO DEL COSTO**

Envía el nuevo monto en USD.

_Ejemplo: 500_

❌ Envía /cancelar para abortar.
"""
    await query.edit_message_text(mensaje, parse_mode='Markdown')


async def handler_borrar_costo(query, supabase: Client):
    """
    Solicita confirmación para borrar un costo.
    """
    # CRÍTICO: Limpiar el ID
    costo_id = limpiar_id(query.data)
    print(f"🔍 [BORRAR] ID limpio: '{costo_id}' (longitud: {len(costo_id)})")
    
    try:
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
            keyboard = [
                [InlineKeyboardButton("✅ Sí, eliminar", callback_data=f'confirmar_borrar_costo_{costo_id}')],
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


async def handler_confirmar_borrar_costo(query, supabase: Client):
    """
    Elimina el costo confirmado por el usuario.
    """
    # CRÍTICO: Limpiar el ID
    costo_id = limpiar_id(query.data)
    print(f"🔍 [CONFIRMAR_BORRAR] ID limpio: '{costo_id}' (longitud: {len(costo_id)})")
    
    await query.edit_message_text("⏳ Eliminando costo...")
    
    try:
        supabase.table('costos').delete().eq('id', costo_id).execute()
        
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


async def handler_nuevo_costo(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Inicia el flujo para crear un nuevo costo (ahora con tipo).
    """
    mensaje = """
💸 **NUEVO COSTO - SELECCIONAR TIPO**

¿Qué tipo de costo es?

📊 **Fijo**: Monto que se paga cada mes (ej: sueldos, alquileres)
💸 **Variable**: Monto que cambia mes a mes (ej: publicidad, servicios)

Selecciona el tipo:
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Fijo", callback_data='nuevo_costo_tipo_Fijo')],
        [InlineKeyboardButton("💸 Variable", callback_data='nuevo_costo_tipo_Variable')],
        [InlineKeyboardButton("❌ Cancelar", callback_data='menu_principal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


# ============================================================================
# PROCESADORES DE TEXTO - COSTOS
# ============================================================================

async def procesar_nombre_costo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el nombre ingresado para un nuevo costo.
    """
    texto = update.message.text.strip()
    
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Operación cancelada.\n\nUsa /start para volver al menú principal."
        )
        return
    
    context.user_data['costo_nombre'] = texto
    context.user_data['esperando_costo_nombre'] = False
    context.user_data['esperando_costo_monto'] = True
    
    mensaje = f"""
💸 **NUEVO COSTO: {texto}**

¿Cuánto se pagó en USD?

📝 Responde solo el número en USD.
_Ejemplo: 500_

❌ Envía /cancelar para abortar.
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')


async def handler_nuevo_costo_tipo_seleccionado(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Usuario seleccionó el tipo de costo (Fijo/Variable).
    """
    # Extraer tipo del callback_data
    tipo = query.data.replace('nuevo_costo_tipo_', '')
    context.user_data['costo_tipo'] = tipo
    context.user_data['esperando_costo_nombre'] = True
    
    mensaje = f"""
💸 **NUEVO COSTO - {tipo.upper()}**

¿En qué se gastó?

💡 *Ejemplos:*
• Sueldo Agustin
• Juana Administrativo
• Hosting Servidor
• Publicidad Facebook

📝 Responde con el nombre del gasto.

❌ Envía /cancelar para abortar.
"""
    await query.edit_message_text(mensaje, parse_mode='Markdown')


async def procesar_monto_costo(update: Update, context: ContextTypes.DEFAULT_TYPE, supabase: Client):
    """
    Procesa el monto ingresado para un nuevo costo.
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
            "⚠️ *Monto inválido*\n\n"
            "Por favor, envía solo el número en USD.\n"
            "_Ejemplo: 500_\n\n"
            "O envía /cancelar para abortar.",
            parse_mode='Markdown'
        )
        return
    
    # Ahora pedir observación
    context.user_data['costo_monto'] = monto_usd
    context.user_data['esperando_costo_monto'] = False
    context.user_data['esperando_costo_observacion'] = True
    
    mensaje = f"""
💸 **NUEVO COSTO - OBSERVACIÓN**

💡 *Observación opcional* (detalles adicionales):
• ARS Fijo
• Pago Semanal
• Operatividad
• Servicio mensual

📝 Responde con la observación o escribe "Sin observación".

❌ Envía /cancelar para abortar.
"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')


async def procesar_observacion_costo(update: Update, context: ContextTypes.DEFAULT_TYPE, supabase: Client):
    """
    Procesa la observación ingresada y guarda el costo completo.
    """
    texto = update.message.text.strip()
    
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Operación cancelada.\n\nUsa /start para volver al menú principal."
        )
        return
    
    observacion = texto if texto.lower() != 'sin observacion' else ''
    costo_nombre = context.user_data.get('costo_nombre', 'Sin nombre')
    costo_monto = context.user_data.get('costo_monto', 0)
    costo_tipo = context.user_data.get('costo_tipo', 'Variable')
    
    mensaje_procesando = await update.message.reply_text("⏳ Guardando costo en Supabase...")
    
    try:
        costo_data = {
            'nombre': costo_nombre,
            'monto_usd': costo_monto,
            'tipo': costo_tipo,
            'observacion': observacion,
            'created_at': datetime.now().isoformat()
        }
        
        supabase.table('costos').insert(costo_data).execute()
        
        resumen = get_resumen_financiero(supabase)
        
        if 'error' not in resumen:
            total_usd = resumen['total_usd']
            total_costos = resumen['total_costos']
            neto_usd = total_usd - total_costos
            neto_fmt = formato_argentino(neto_usd)
        else:
            neto_fmt = "N/A"
        
        mensaje_exito = f"""
✅ **COSTO REGISTRADO EXITOSAMENTE**

💸 *Concepto:* {costo_nombre}
📊 *Tipo:* {costo_tipo}
💵 *Monto:* ${costo_monto:,.2f} USD
📝 *Observación:* {observacion if observacion else 'Sin observación'}
📅 *Fecha:* {datetime.now().strftime('%d/%m/%Y')}

---
💎 **NETO USDT ACTUALIZADO:** ${neto_fmt}
---

Usa /start para volver al menú principal.
"""
        
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


async def procesar_editar_nombre_costo(update: Update, context: ContextTypes.DEFAULT_TYPE, supabase: Client):
    """
    Procesa el nuevo nombre para editar un costo.
    """
    texto = update.message.text.strip()
    
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text("❌ Operación cancelada.\n\nUsa /start para volver al menú principal.")
        return
    
    costo_id = context.user_data.get('costo_id_editar')
    
    if not costo_id:
        context.user_data.clear()
        await update.message.reply_text("❌ Error: No se encontró el ID del costo.\n\nUsa /start para comenzar de nuevo.")
        return
    
    # El ID ya debería estar limpio
    costo_id = str(costo_id)
    print(f"🔍 [PROCESAR_NOMBRE] ID para UPDATE: '{costo_id}'")
    
    try:
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


async def procesar_editar_monto_costo(update: Update, context: ContextTypes.DEFAULT_TYPE, supabase: Client):
    """
    Procesa el nuevo monto para editar un costo.
    """
    texto = update.message.text.strip()
    
    if texto.lower() in ['/cancelar', 'cancelar']:
        context.user_data.clear()
        await update.message.reply_text("❌ Operación cancelada.\n\nUsa /start para volver al menú principal.")
        return
    
    try:
        monto_usd = float(texto.replace(',', '.'))
        if monto_usd <= 0:
            raise ValueError("El monto debe ser mayor a 0")
    except ValueError:
        await update.message.reply_text("⚠️ Monto inválido. Envía un número mayor a 0 o /cancelar.")
        return
    
    costo_id = context.user_data.get('costo_id_editar')
    
    if not costo_id:
        context.user_data.clear()
        await update.message.reply_text("❌ Error: No se encontró el ID del costo.\n\nUsa /start para comenzar de nuevo.")
        return
    
    # El ID ya debería estar limpio
    costo_id = str(costo_id)
    print(f"🔍 [PROCESAR_MONTO] ID para UPDATE: '{costo_id}'")
    
    try:
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
