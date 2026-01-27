#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - HANDLERS DE CLIENTES
============================================
Handlers para gestionar clientes desde Telegram

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 1.0.0
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from supabase import Client

from db_manager import inicializar_supabase


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_todos_clientes(supabase: Client) -> list:
    """
    Obtiene TODOS los clientes (activos e inactivos).
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        list: Lista de clientes o {'error': str}
    """
    try:
        print("📋 Consultando todos los clientes...")
        response = supabase.table('clientes').select('*').order('nombre').execute()
        
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Respuesta inválida de la tabla clientes")
        
        print(f"✅ {len(response.data)} clientes encontrados")
        return response.data
        
    except Exception as e:
        print(f"❌ Error en get_todos_clientes: {e}")
        return {'error': str(e)}


def actualizar_cliente_campo(supabase: Client, cliente_id: str, campo: str, valor: any) -> bool:
    """
    Actualiza un campo específico de un cliente.
    
    Args:
        supabase: Cliente de Supabase
        cliente_id: ID del cliente
        campo: Nombre del campo a actualizar
        valor: Nuevo valor
    
    Returns:
        bool: True si se actualizó correctamente
    """
    try:
        print(f"📝 Actualizando cliente {cliente_id}: {campo} = {valor}")
        response = supabase.table('clientes').update({campo: valor}).eq('id', cliente_id).execute()
        
        if not hasattr(response, 'data') or response.data is None:
            raise Exception("Error al actualizar cliente")
        
        print(f"✅ Cliente actualizado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al actualizar cliente: {e}")
        return False


# ============================================================================
# HANDLERS
# ============================================================================

async def handler_ver_clientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra la lista de clientes con opciones de edición.
    """
    query = update.callback_query
    await query.answer()
    
    supabase = inicializar_supabase()
    clientes = get_todos_clientes(supabase)
    
    if isinstance(clientes, dict) and 'error' in clientes:
        mensaje = f"❌ **ERROR**\n\n`{clientes['error']}`"
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data='menu_principal')]]
    elif not clientes:
        mensaje = "📋 **CLIENTES**\n\nNo hay clientes en el sistema."
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data='menu_principal')]]
    else:
        # Calcular resumen
        activos = sum(1 for c in clientes if c.get('estado') == 'Activo')
        con_comision = sum(1 for c in clientes if c.get('estado') == 'Activo' and c.get('comisiona_agustin', False))
        ingresos_proy = sum(float(c.get('fee_mensual', 0) or 0) for c in clientes if c.get('estado') == 'Activo')
        costo_agustin = con_comision * 55
        
        mensaje = f"""
📋 **GESTIÓN DE CLIENTES**

**Resumen:**
👥 Total: {len(clientes)}
✅ Activos: {activos}
💰 Con comisión: {con_comision}
💵 Ingresos proyectados: ${ingresos_proy:,.2f} USD
💸 Costo Agustín: ${costo_agustin:,.2f} USD

---

**Selecciona un cliente para editar:**
"""
        
        # Crear botones para cada cliente
        keyboard = []
        for cliente in clientes[:10]:  # Limitar a 10 para no exceder límite de botones
            nombre = cliente.get('nombre', 'Sin nombre')
            estado = cliente.get('estado', 'Inactivo')
            emoji = "✅" if estado == 'Activo' else "⚠️"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {nombre} ({estado})", 
                    callback_data=f'editar_cliente_{cliente["id"]}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data='menu_principal')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


async def handler_editar_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra las opciones de edición para un cliente específico.
    """
    query = update.callback_query
    await query.answer()
    
    cliente_id = query.data.split('_')[-1]
    
    supabase = inicializar_supabase()
    
    try:
        response = supabase.table('clientes').select('*').eq('id', cliente_id).single().execute()
        cliente = response.data
        
        nombre = cliente.get('nombre', 'Sin nombre')
        estado = cliente.get('estado', 'Inactivo')
        fee_mensual = float(cliente.get('fee_mensual', 0) or 0)
        comisiona = cliente.get('comisiona_agustin', False)
        
        mensaje = f"""
📝 **EDITAR CLIENTE**

**Cliente:** {nombre}
**Estado:** {estado}
**Fee Mensual:** ${fee_mensual:.2f} USD
**Comisiona Agustín:** {'✅ Sí' if comisiona else '❌ No'}

---

**Selecciona qué editar:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Cambiar Estado", callback_data=f'edit_estado_{cliente_id}')],
            [InlineKeyboardButton("💵 Cambiar Fee Mensual", callback_data=f'edit_fee_{cliente_id}')],
            [InlineKeyboardButton(
                f"{'✅' if not comisiona else '❌'} {'Activar' if not comisiona else 'Desactivar'} Comisión",
                callback_data=f'toggle_comision_{cliente_id}'
            )],
            [InlineKeyboardButton("🔙 Volver a Lista", callback_data='ver_clientes')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        mensaje = f"❌ **ERROR**\n\n`{str(e)}`"
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data='ver_clientes')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


async def handler_edit_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra opciones para cambiar el estado del cliente.
    """
    query = update.callback_query
    await query.answer()
    
    cliente_id = query.data.split('_')[-1]
    
    mensaje = """
🔄 **CAMBIAR ESTADO**

Selecciona el nuevo estado:
"""
    
    estados = ['Activo', 'Inactivo', 'Pausado', 'Prospecto']
    keyboard = []
    
    for estado in estados:
        keyboard.append([
            InlineKeyboardButton(estado, callback_data=f'set_estado_{cliente_id}_{estado}')
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancelar", callback_data=f'editar_cliente_{cliente_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


async def handler_set_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Actualiza el estado del cliente.
    """
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    cliente_id = parts[2]
    nuevo_estado = parts[3]
    
    supabase = inicializar_supabase()
    
    if actualizar_cliente_campo(supabase, cliente_id, 'estado', nuevo_estado):
        await query.answer(f"✅ Estado actualizado a: {nuevo_estado}", show_alert=True)
    else:
        await query.answer("❌ Error al actualizar estado", show_alert=True)
    
    # Volver a la pantalla de edición del cliente
    context.application.create_task(
        handler_editar_cliente(update, context)
    )


async def handler_edit_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Solicita el nuevo fee mensual para el cliente.
    """
    query = update.callback_query
    await query.answer()
    
    cliente_id = query.data.split('_')[-1]
    
    # Guardar el cliente_id en el contexto de usuario
    context.user_data['editando_fee_cliente'] = cliente_id
    
    mensaje = """
💵 **CAMBIAR FEE MENSUAL**

Envía el nuevo monto en USD (solo el número).

Ejemplo: `55.00`

Para cancelar, envía /cancelar
"""
    
    await query.edit_message_text(mensaje, parse_mode='Markdown')


async def procesar_nuevo_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el nuevo fee mensual ingresado por el usuario.
    """
    if 'editando_fee_cliente' not in context.user_data:
        return
    
    cliente_id = context.user_data['editando_fee_cliente']
    
    try:
        nuevo_fee = float(update.message.text.strip())
        
        if nuevo_fee < 0:
            await update.message.reply_text("❌ El monto debe ser positivo. Intenta de nuevo.")
            return
        
        supabase = inicializar_supabase()
        
        if actualizar_cliente_campo(supabase, cliente_id, 'fee_mensual', nuevo_fee):
            await update.message.reply_text(f"✅ Fee mensual actualizado a: ${nuevo_fee:.2f} USD")
            del context.user_data['editando_fee_cliente']
        else:
            await update.message.reply_text("❌ Error al actualizar el fee mensual")
    
    except ValueError:
        await update.message.reply_text("❌ Monto inválido. Debes enviar un número. Ejemplo: 55.00")


async def handler_toggle_comision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Activa/desactiva la comisión de Agustín para el cliente.
    """
    query = update.callback_query
    await query.answer()
    
    cliente_id = query.data.split('_')[-1]
    
    supabase = inicializar_supabase()
    
    try:
        # Obtener estado actual
        response = supabase.table('clientes').select('comisiona_agustin').eq('id', cliente_id).single().execute()
        comisiona_actual = response.data.get('comisiona_agustin', False)
        
        # Invertir el valor
        nuevo_valor = not comisiona_actual
        
        if actualizar_cliente_campo(supabase, cliente_id, 'comisiona_agustin', nuevo_valor):
            texto = "✅ Comisión activada" if nuevo_valor else "❌ Comisión desactivada"
            await query.answer(texto, show_alert=True)
        else:
            await query.answer("❌ Error al actualizar comisión", show_alert=True)
        
        # Volver a la pantalla de edición del cliente
        context.application.create_task(
            handler_editar_cliente(update, context)
        )
        
    except Exception as e:
        await query.answer(f"❌ Error: {str(e)}", show_alert=True)
