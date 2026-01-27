# 🔄 Migración de Estructura de Costos

## Objetivo

Sincronizar la tabla `costos` en Supabase con la estructura real de Google Sheets, agregando los campos `tipo` y `observacion`.

---

## Pasos para Ejecutar la Migración

### 1. Acceder a Supabase

1. Ve a https://supabase.com/dashboard
2. Selecciona tu proyecto BLACK Infrastructure
3. Ve a **SQL Editor** (menú lateral izquierdo)

### 2. Ejecutar el Script SQL

1. Abre el archivo: `backend/migration_costos_estructura.sql`
2. Copia todo el contenido
3. Pega en el SQL Editor de Supabase
4. Haz clic en **Run** (o presiona Ctrl/Cmd + Enter)

### 3. Verificar Resultados

La migración debe mostrar:

```
total_costos: 1258
cantidad_costos: 4
```

Y agrupado por tipo:

```
tipo      | cantidad | total_usd
----------|----------|----------
Variable  |    1     |   605
Fijo      |    3     |   653
```

---

## Datos Migrados

### Costos de Enero 2026

| Nombre   | Monto USD | Tipo     | Observación    |
|----------|-----------|----------|----------------|
| Agustin  | $605      | Variable | Operatividad   |
| Juana    | $267      | Fijo     | ARS Fijo       |
| Maxi     | $253      | Fijo     | Pago Semanal   |
| Yazmin   | $133      | Fijo     | ARS Fijo       |
| **TOTAL**| **$1,258**|          |                |

---

## Estructura Nueva de la Tabla

```sql
CREATE TABLE costos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nombre VARCHAR(255) NOT NULL,
  monto_usd DECIMAL(10, 2) NOT NULL,
  tipo VARCHAR(50),           -- ← NUEVO
  observacion TEXT,           -- ← NUEVO
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Campos Nuevos

- **`tipo`**: Puede ser "Fijo" o "Variable"
- **`observacion`**: Detalles adicionales (ej: "ARS Fijo", "Pago Semanal", "Operatividad")

---

## Actualización del Backend

### Archivos Actualizados

1. ✅ `db_manager.py` - Nueva función `get_costos_agrupados()`
2. ✅ `handlers_costos.py` - Vista agrupada por tipo
3. ✅ `lib/supabase.ts` (webapp) - Tipo actualizado

### Archivos Nuevos

1. ✅ `migration_costos_estructura.sql` - Script de migración
2. ✅ `INSTRUCCIONES_MIGRACION.md` - Este archivo

---

## Testing Post-Migración

### 1. Verificar en Supabase

```sql
-- Ver todos los costos de Enero 2026
SELECT * FROM costos 
WHERE created_at >= '2026-01-01' 
  AND created_at < '2026-02-01'
ORDER BY tipo, nombre;
```

### 2. Probar el Bot de Telegram

1. Envía `/start` al bot
2. Toca "⚙️ Gestionar Costos"
3. Deberías ver los costos agrupados:

```
📊 COSTOS FIJOS ($653)
  • Juana: $267 (ARS Fijo)
  • Maxi: $253 (Pago Semanal)
  • Yazmin: $133 (ARS Fijo)

💸 COSTOS VARIABLES ($605)
  • Agustin: $605 (Operatividad)
```

### 3. Probar el Dashboard Web

1. Abre la webapp
2. Ve al dashboard
3. Verifica que muestre:
   - Total Gastos: $1,258 USD
   - Desglose por tipo (si se implementó)

---

## Rollback (si es necesario)

Si algo sale mal, puedes revertir:

```sql
-- Eliminar columnas agregadas
ALTER TABLE costos 
DROP COLUMN IF EXISTS tipo,
DROP COLUMN IF EXISTS observacion;

-- Eliminar índice
DROP INDEX IF EXISTS idx_costos_tipo;
```

---

## Próximos Pasos

Después de la migración exitosa:

1. ✅ El bot mostrará costos agrupados por tipo
2. ✅ La webapp reflejará el total correcto ($1,258)
3. ✅ Podrás agregar nuevos costos con tipo y observación

---

**Fecha de Creación**: 21/01/2026  
**Autor**: Senior Backend Developer  
**Versión**: 1.0
