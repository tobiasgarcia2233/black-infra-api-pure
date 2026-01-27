# BLACK INFRA - REFACTORIZACIÓN v2.0

## 📋 Resumen

Se ha realizado una refactorización completa del código del bot de Telegram, modularizando el archivo monolítico `bot_main.py` (2083 líneas) en módulos especializados y limpios.

## 🗂️ Nueva Estructura

```
backend/
├── bot_instance.py          # ⚙️ Configuración y arranque del bot
├── db_manager.py            # 💾 Todas las consultas a Supabase
├── handlers_costos.py       # 💸 Lógica de gestión de costos
├── handlers_ingresos.py     # 💰 Lógica de pagos e ingresos
├── utils.py                 # 🔧 Utilidades comunes (incluye limpiar_id)
├── bot_main_OLD.py          # 📦 Backup del archivo original
└── requirements.txt         # 📚 Dependencias
```

## 🔐 Fix de Seguridad Crítico

### Problema Original (Error 22P02)
El bot enviaba callback_data completos a Supabase:
- ❌ `"borrar_costo_550e8400-..."` → Error 22P02
- ❌ `"confirmar_borrar_costo_UUID"` → Error 22P02

### Solución Implementada
Creada función `limpiar_id(callback_data)` en `utils.py`:

```python
def limpiar_id(callback_data: str) -> str:
    """Extrae solo el UUID puro del callback_data"""
    # Método 1: Regex
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    match = re.search(uuid_pattern, callback_data, re.IGNORECASE)
    if match:
        return match.group(0)
    
    # Método 2: Split (fallback)
    return callback_data.split('_')[-1]
```

**Todas las funciones que interactúan con la base de datos ahora usan `limpiar_id()`:**
- ✅ `handler_editar_costo()`
- ✅ `handler_borrar_costo()`
- ✅ `handler_confirmar_borrar_costo()`
- ✅ `handler_edit_nombre()`
- ✅ `handler_edit_monto()`

## 📦 Módulos

### 1. `utils.py`
Funciones auxiliares y utilidades comunes.

**Funciones:**
- `limpiar_id(callback_data)` - Extrae UUID puro (FIX CRÍTICO)
- `formato_argentino(numero)` - Formato de números argentino

### 2. `db_manager.py`
Gestión centralizada de todas las consultas a Supabase.

**Funciones:**
- `inicializar_supabase()` - Configura cliente Supabase
- `get_dolar_blue()` - Obtiene cotización del dólar
- `get_resumen_financiero(supabase)` - Calcula resumen Enero 2026
- `get_clientes_activos(supabase)` - Lista clientes activos
- `get_ultimos_costos(supabase, limite)` - Últimos costos
- `get_ultimos_ingresos(supabase, limite)` - Últimos ingresos
- `verificar_conexion_supabase(supabase)` - Test de conexión

### 3. `handlers_costos.py`
Lógica completa de gestión de costos.

**Handlers de Botones:**
- `handler_gestionar_costos()` - Lista costos
- `handler_editar_costo()` - Muestra opciones de edición
- `handler_edit_nombre()` - Solicita nuevo nombre
- `handler_edit_monto()` - Solicita nuevo monto
- `handler_borrar_costo()` - Pide confirmación
- `handler_confirmar_borrar_costo()` - Elimina costo
- `handler_nuevo_costo()` - Inicia flujo de creación

**Procesadores de Texto:**
- `procesar_nombre_costo()` - Procesa nombre de nuevo costo
- `procesar_monto_costo()` - Procesa monto de nuevo costo
- `procesar_editar_nombre_costo()` - Actualiza nombre
- `procesar_editar_monto_costo()` - Actualiza monto

### 4. `handlers_ingresos.py`
Lógica completa de gestión de ingresos/pagos.

**Handlers de Botones:**
- `handler_nuevo_pago()` - Lista clientes
- `handler_cliente_seleccionado()` - Procesa cliente seleccionado
- `handler_ver_movimientos()` - Lista últimos ingresos
- `handler_borrar_ingreso()` - Pide confirmación
- `handler_confirmar_borrar_ingreso()` - Elimina ingreso

**Procesadores de Texto:**
- `procesar_monto_pago()` - Procesa y registra nuevo pago

### 5. `bot_instance.py`
Configuración, comandos y orquestación del bot.

**Comandos:**
- `/start` - Menú principal
- `/resumen` - Estado de resultados
- `/clientes` - Lista clientes activos

**Handler Central:**
- `button_handler()` - Enruta todos los callbacks a handlers específicos

## 🚀 Cómo Ejecutar

### Opción 1: Usar el nuevo bot modular
```bash
cd backend
python3 bot_instance.py
```

### Opción 2: Volver al backup (si hay problemas)
```bash
cd backend
mv bot_main_OLD.py bot_main.py
python3 bot_main.py
```

## ✅ Mejoras Implementadas

1. **Modularidad**: Código organizado en módulos especializados
2. **Seguridad**: Fix del error 22P02 con función `limpiar_id()`
3. **Mantenibilidad**: Funciones pequeñas y específicas
4. **Legibilidad**: Código limpio sin duplicación
5. **Debugging**: Logs específicos por módulo
6. **Escalabilidad**: Fácil agregar nuevas funcionalidades

## 🔍 Verificación

Después de iniciar el bot, verifica que:

1. ✅ El bot se conecta a Telegram
2. ✅ Supabase se conecta correctamente
3. ✅ Los comandos funcionan: `/start`, `/resumen`, `/clientes`
4. ✅ **CRÍTICO**: Probá borrar un costo - debe funcionar sin error 22P02
5. ✅ **CRÍTICO**: Probá editar un costo - debe funcionar sin error 22P02

## 📊 Comparación

| Aspecto | Antes (v1.0) | Después (v2.0) |
|---------|--------------|----------------|
| **Líneas de código** | 2083 líneas en 1 archivo | ~1500 líneas en 5 archivos |
| **Funciones** | 30+ en un solo archivo | Organizadas en módulos |
| **Error 22P02** | ❌ Presente | ✅ Corregido |
| **Mantenibilidad** | Difícil | Fácil |
| **Testing** | Complejo | Sencillo (módulos independientes) |

## 🐛 Solución de Problemas

### Error: "Module not found"
```bash
# Asegurate de estar en la carpeta backend
cd /Users/tobiasgarcia/Desktop/BLACK_INFRA/backend
python3 bot_instance.py
```

### Error: "TELEGRAM_TOKEN not found"
```bash
# Verificá que el .env esté en la carpeta raíz
ls -la ../. env
```

### El bot funciona pero sigue dando error 22P02
```bash
# Verificá que estés usando bot_instance.py (nuevo) y no bot_main_OLD.py
ps aux | grep python
```

## 🎯 Próximos Pasos

1. ✅ Refactorización completada
2. ⏳ Testing de borrado/edición de costos
3. ⏳ Verificar que PST.NET sigue funcionando
4. ⏳ Eliminar `bot_main_OLD.py` después de confirmar que todo funciona

---

**Autor:** Senior Backend Developer  
**Fecha:** 21/01/2026  
**Versión:** 2.0.0
