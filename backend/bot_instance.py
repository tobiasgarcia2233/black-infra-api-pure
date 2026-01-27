#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - BOT INSTANCE
====================================
Configuración y arranque del bot de Telegram

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 2.0.0
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from db_manager import (
    inicializar_supabase,
    get_resumen_financiero,
    get_dolar_blue,
    get_clientes_activos,
    verificar_conexion_supabase
)
from handlers_costos import (
    handler_gestionar_costos,
    handler_editar_costo,
    handler_edit_nombre,
    handler_edit_monto,
    handler_borrar_costo,
    handler_confirmar_borrar_costo,
    handler_nuevo_costo,
    handler_nuevo_costo_tipo_seleccionado,
    procesar_nombre_costo,
    procesar_monto_costo,
    procesar_observacion_costo,
    procesar_editar_nombre_costo,
    procesar_editar_monto_costo
)
from handlers_ingresos import (
    handler_nuevo_pago,
    handler_cliente_seleccionado,
    handler_ver_movimientos,
    handler_borrar_ingreso,
    handler_confirmar_borrar_ingreso,
    procesar_monto_pago
)
from handlers_clientes import (
    handler_ver_clientes,
    handler_editar_cliente,
    handler_edit_estado,
    handler_set_estado,
    handler_edit_fee,
    handler_toggle_comision,
    procesar_nuevo_fee
)
from utils import formato_argentino


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

def obtener_token_telegram() -> str:
    """
    Obtiene el token de Telegram desde las variables de entorno.
    
    Returns:
        str: Token de Telegram
    """
    # Obtener ruta del .env
    SCRIPT_DIR = Path(__file__).resolve().parent
    ROOT_DIR = SCRIPT_DIR.parent
    ENV_PATH = ROOT_DIR / '.env'
    
    print(f"📁 Cargando .env desde: {ENV_PATH}")
    
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
        print("✅ Archivo .env encontrado")
    else:
        print(f"❌ ERROR: Archivo .env no encontrado en {ENV_PATH}")
        sys.exit(1)
    
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TELEGRAM_TOKEN:
        print("❌ ERROR: TELEGRAM_TOKEN no está definido en .env")
        sys.exit(1)
    
    TELEGRAM_TOKEN = TELEGRAM_TOKEN.strip().strip('"').strip("'")
    print(f"✅ Token de Telegram cargado: {TELEGRAM_TOKEN[:20]}...")
    
    return TELEGRAM_TOKEN


# ============================================================================
# COMANDOS
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /start - Muestra el menú principal.
    """
    user = update.effective_user
    
    supabase = inicializar_supabase()
    conexion_ok = verificar_conexion_supabase(supabase)
    
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
    Handler para el comando /resumen - Muestra resumen financiero.
    """
    mensaje_procesando = await update.message.reply_text("⏳ Consultando datos de Enero 2026...")
    
    supabase = inicializar_supabase()
    resumen = get_resumen_financiero(supabase)
    
    cotizacion_dolar = get_dolar_blue()
    if 'error' in cotizacion_dolar:
        dolar_mercado = 1500.0
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
        total_ars = resumen['total_ars']
        total_usd = resumen['total_usd']
        total_costos = resumen['total_costos']
        dolar_conversion = resumen.get('dolar_conversion_costos', 1500.0)
        
        utilidad_neta_usdt = total_usd - total_costos
        pesos_en_usdt = total_ars / dolar_mercado
        
        ars_fmt = formato_argentino(total_ars).split(',')[0]
        usd_fmt = formato_argentino(total_usd)
        costos_fmt = formato_argentino(total_costos)
        neto_fmt = formato_argentino(utilidad_neta_usdt)
        dolar_blue_fmt = formato_argentino(dolar_mercado)
        dolar_conversion_fmt = formato_argentino(dolar_conversion)
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
🏦 Dólar Blue (Ingresos): ${dolar_blue_fmt}
💱 Dólar Conversión (Costos): ${dolar_conversion_fmt}
🪙 Equivalente Pesos: ${pesos_en_usd_fmt} USDT
   _(Si los cambiaras hoy)_
"""
    
    await mensaje_procesando.edit_text(mensaje, parse_mode='Markdown')


async def clientes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para el comando /clientes - Gestión de clientes con edición.
    """
    from handlers_clientes import get_todos_clientes
    
    mensaje_procesando = await update.message.reply_text("⏳ Consultando clientes...")
    
    supabase = inicializar_supabase()
    clientes = get_todos_clientes(supabase)
    
    if isinstance(clientes, dict) and 'error' in clientes:
        mensaje = f"❌ **ERROR**\n\n`{clientes['error']}`"
        keyboard = []
    elif not clientes:
        mensaje = "📋 **GESTIÓN DE CLIENTES**\n\nNo hay clientes en el sistema."
        keyboard = []
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
        for cliente in clientes[:10]:  # Limitar a 10
            nombre = cliente.get('nombre', 'Sin nombre')
            estado = cliente.get('estado', 'Inactivo')
            emoji = "✅" if estado == 'Activo' else "⚠️"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {nombre} ({estado})", 
                    callback_data=f'editar_cliente_{cliente["id"]}'
                )
            ])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await mensaje_procesando.edit_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)


# ============================================================================
# HANDLER PRINCIPAL DE BOTONES
# ============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler central para todos los botones inline (CallbackQuery).
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    supabase = inicializar_supabase()
    
    # MENÚ PRINCIPAL
    if callback_data == 'menu_principal':
        user = update.effective_user
        conexion_ok = verificar_conexion_supabase(supabase)
        
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
        
        keyboard = [
            [InlineKeyboardButton("📊 Resumen Enero", callback_data='ver_resumen')],
            [InlineKeyboardButton("📥 Nuevo Pago", callback_data='nuevo_pago')],
            [InlineKeyboardButton("💸 Nuevo Costo", callback_data='nuevo_costo')],
            [InlineKeyboardButton("👥 Ver Clientes", callback_data='ver_clientes')],
            [InlineKeyboardButton("📜 Últimos Movimientos", callback_data='ver_movimientos')],
            [InlineKeyboardButton("⚙️ Gestionar Costos", callback_data='gestionar_costos')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    # VER RESUMEN
    elif callback_data == 'ver_resumen':
        await query.edit_message_text("⏳ Consultando datos de Enero 2026...")
        
        resumen = get_resumen_financiero(supabase)
        cotizacion_dolar = get_dolar_blue()
        
        if 'error' in cotizacion_dolar:
            dolar_mercado = 1500.0
        else:
            dolar_mercado = cotizacion_dolar['venta']
        
        if 'error' in resumen:
            mensaje = f"❌ *ERROR*\n\n`{resumen['error']}`"
        else:
            total_ars = resumen['total_ars']
            total_usd = resumen['total_usd']
            total_costos = resumen['total_costos']
            dolar_conversion = resumen.get('dolar_conversion_costos', 1500.0)
            utilidad_neta_usdt = total_usd - total_costos
            pesos_en_usdt = total_ars / dolar_mercado
            
            ars_fmt = formato_argentino(total_ars).split(',')[0]
            usd_fmt = formato_argentino(total_usd)
            costos_fmt = formato_argentino(total_costos)
            neto_fmt = formato_argentino(utilidad_neta_usdt)
            dolar_blue_fmt = formato_argentino(dolar_mercado)
            dolar_conversion_fmt = formato_argentino(dolar_conversion)
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
🏦 Dólar Blue (Ingresos): ${dolar_blue_fmt}
💱 Dólar Conversión (Costos): ${dolar_conversion_fmt}
🪙 Equivalente Pesos: ${pesos_en_usd_fmt} USDT
   _(Si los cambiaras hoy)_
"""
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    # VER CLIENTES
    elif callback_data == 'ver_clientes':
        await handler_ver_clientes(update, context)
        return
        
        keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data='menu_principal')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    # HANDLERS DE COSTOS
    elif callback_data == 'gestionar_costos':
        await handler_gestionar_costos(query, supabase)
    
    elif callback_data.startswith('editar_costo_'):
        await handler_editar_costo(query, supabase)
    
    elif callback_data.startswith('edit_nombre_'):
        await handler_edit_nombre(query, context)
    
    elif callback_data.startswith('edit_monto_'):
        await handler_edit_monto(query, context)
    
    elif callback_data.startswith('borrar_costo_'):
        await handler_borrar_costo(query, supabase)
    
    elif callback_data.startswith('confirmar_borrar_costo_'):
        await handler_confirmar_borrar_costo(query, supabase)
    
    elif callback_data == 'nuevo_costo':
        await handler_nuevo_costo(query, context)
    
    elif callback_data.startswith('nuevo_costo_tipo_'):
        await handler_nuevo_costo_tipo_seleccionado(query, context)
    
    # HANDLERS DE INGRESOS
    elif callback_data == 'nuevo_pago':
        await handler_nuevo_pago(query, supabase)
    
    elif callback_data.startswith('cliente_'):
        await handler_cliente_seleccionado(query, context, supabase)
    
    elif callback_data == 'ver_movimientos':
        await handler_ver_movimientos(query, supabase)
    
    elif callback_data.startswith('borrar_ingreso_'):
        await handler_borrar_ingreso(query, supabase)
    
    elif callback_data.startswith('confirmar_borrar_'):
        await handler_confirmar_borrar_ingreso(query, supabase)
    
    # HANDLERS DE CLIENTES
    elif callback_data.startswith('editar_cliente_'):
        await handler_editar_cliente(update, context)
    
    elif callback_data.startswith('edit_estado_'):
        await handler_edit_estado(update, context)
    
    elif callback_data.startswith('set_estado_'):
        await handler_set_estado(update, context)
    
    elif callback_data.startswith('edit_fee_'):
        await handler_edit_fee(update, context)
    
    elif callback_data.startswith('toggle_comision_'):
        await handler_toggle_comision(update, context)


# ============================================================================
# PROCESADOR DE TEXTO
# ============================================================================

async def procesar_texto_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa mensajes de texto del usuario para diferentes flujos.
    """
    supabase = inicializar_supabase()
    
    if context.user_data.get('esperando_monto'):
        await procesar_monto_pago(update, context, supabase)
    elif context.user_data.get('esperando_costo_nombre'):
        await procesar_nombre_costo(update, context)
    elif context.user_data.get('esperando_costo_monto'):
        await procesar_monto_costo(update, context, supabase)
    elif context.user_data.get('esperando_costo_observacion'):
        await procesar_observacion_costo(update, context, supabase)
    elif context.user_data.get('esperando_edit_nombre'):
        await procesar_editar_nombre_costo(update, context, supabase)
    elif context.user_data.get('esperando_edit_monto'):
        await procesar_editar_monto_costo(update, context, supabase)
    elif context.user_data.get('editando_fee_cliente'):
        await procesar_nuevo_fee(update, context)


# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler global de errores.
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
    Función principal que inicia el bot.
    """
    print("\n" + "="*70)
    print("🤖 INICIANDO BOT DE TELEGRAM - SISTEMA BLACK v2.0")
    print("="*70 + "\n")
    
    try:
        # Obtener token
        TELEGRAM_TOKEN = obtener_token_telegram()
        
        # Inicializar Supabase
        supabase = inicializar_supabase()
        
        # Crear aplicación
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Registrar handlers de comandos
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("resumen", resumen_command))
        application.add_handler(CommandHandler("clientes", clientes_command))
        
        # Registrar handler de botones
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Registrar handler de mensajes de texto
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
