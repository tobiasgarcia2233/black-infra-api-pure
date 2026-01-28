# 🔧 Fix: Botón "Cobrar" - Error 500 o de Red

## 🚨 Problema Reportado
El botón "Cobrar" en la sección de "Cobros pendientes" está fallando con error 500 o error de red.

## 🔍 Diagnóstico

El problema ocurre porque el frontend intenta insertar un registro con la columna `mes_aplicado`, pero esa columna **todavía no existe** en la tabla `ingresos` de Supabase.

### Estado Actual del Código
✅ Frontend actualizado (con soporte para `mes_aplicado`)
❌ Base de datos NO actualizada (falta ejecutar migración)

## 🛠️ Solución Paso a Paso

### Paso 1: Verificar el Estado de la Base de Datos

1. Ve a Supabase: https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Ve a **SQL Editor** → **New Query**
4. Copia y pega el contenido de `verify_db_schema.sql`
5. Ejecuta el script

### Resultado Esperado:
```
❌ La columna mes_aplicado NO EXISTE - Ejecuta migration_atribucion_temporal.sql
```

---

### Paso 2: Ejecutar la Migración

1. En el mismo **SQL Editor** de Supabase
2. Abre una **nueva query**
3. Copia y pega el contenido completo de `migration_atribucion_temporal.sql`
4. Haz clic en **Run** (o presiona Ctrl+Enter / Cmd+Enter)

### ✅ Confirmación de Éxito:
Deberías ver mensajes como:
```
✅ ALTER TABLE
✅ CREATE FUNCTION
✅ CREATE INDEX
✅ CREATE VIEW
```

---

### Paso 3: Verificar que Funcionó

Ejecuta este query simple en Supabase:
```sql
SELECT calcular_mes_aplicado(CURRENT_DATE);
```

**Resultado esperado:**
```
'02-2026'  (Febrero, si hoy es enero)
```

---

### Paso 4: Probar el Botón "Cobrar"

1. Abre el dashboard: https://tu-app.vercel.app/dashboard
2. Abre la **consola del navegador** (F12 → Console)
3. Ve a "Cobros pendientes esta semana"
4. Haz clic en **"Cobrar"** para un cliente

### 📊 Logs que Deberías Ver:

```
🔵 INICIO DE REGISTRO DE COBRO
   Cliente: Cashboom
   Monto USD: 150
   Fecha cobro: 2026-01-28
   Periodo sistema: 01-2026
   Mes aplicado (calculado): 02-2026
🔍 Verificando cobros existentes...
💵 Obteniendo tasa de conversión...
   Dólar conversión: 1200
   Monto ARS: 180000
💾 Intentando insertar registro completo (con mes_aplicado)...
✅ Cobro registrado exitosamente con atribución temporal
✅ REGISTRO COMPLETADO
```

### 🎉 Toast de Éxito:
```
✅ Cashboom: $150 cobrado para Febrero
```

---

## 🔄 Modo Legacy (Fallback Automático)

Si **NO ejecutas la migración**, el sistema tiene un modo de compatibilidad que:

1. Intenta insertar con `mes_aplicado`
2. Si falla, inserta SIN `mes_aplicado` (modo legacy)
3. Muestra warning en consola

### Logs en Modo Legacy:
```
⚠️ La columna mes_aplicado no existe todavía
⚠️ Insertando SIN mes_aplicado (modo legacy)
⚠️ IMPORTANTE: Ejecuta migration_atribucion_temporal.sql en Supabase
✅ Cobro registrado en MODO LEGACY (sin atribución temporal)
```

**⚠️ IMPORTANTE:** El modo legacy funciona, pero **NO tendrás atribución temporal** (no podrás distinguir entre liquidez y performance).

---

## 🐛 Troubleshooting: Errores Comunes

### Error 1: "Column mes_aplicado does not exist"

**Causa:** La migración no se ejecutó.

**Solución:**
```sql
-- Ejecuta esto en Supabase SQL Editor:
ALTER TABLE ingresos
ADD COLUMN IF NOT EXISTS mes_aplicado VARCHAR(7);

CREATE INDEX IF NOT EXISTS idx_ingresos_mes_aplicado 
ON ingresos(mes_aplicado);
```

---

### Error 2: "Permission denied for table ingresos"

**Causa:** Las políticas RLS (Row Level Security) no permiten la inserción.

**Solución:**
```sql
-- Ejecuta esto en Supabase SQL Editor:

-- Habilitar RLS (si no está habilitado)
ALTER TABLE ingresos ENABLE ROW LEVEL SECURITY;

-- Política para INSERT
CREATE POLICY "Usuarios autenticados pueden insertar ingresos" 
ON ingresos FOR INSERT 
TO authenticated 
WITH CHECK (true);

-- Política para SELECT
CREATE POLICY "Usuarios autenticados pueden leer ingresos" 
ON ingresos FOR SELECT 
TO authenticated 
USING (true);

-- Política para UPDATE (opcional)
CREATE POLICY "Usuarios autenticados pueden actualizar ingresos" 
ON ingresos FOR UPDATE 
TO authenticated 
USING (true);
```

---

### Error 3: "Duplicate key value violates unique constraint"

**Causa:** Ya existe un cobro para ese cliente en ese `mes_aplicado`.

**Verificación:**
```sql
SELECT 
    cliente_id,
    mes_aplicado,
    monto_usd_total,
    fecha_cobro,
    detalle
FROM ingresos
WHERE cliente_id = 'uuid-del-cliente'
AND mes_aplicado = '02-2026';
```

**Solución:** Es correcto que falle. No puedes cobrar dos veces para el mismo mes de servicio.

---

### Error 4: "Failed to fetch" o "Network error"

**Causa:** Problema de conexión con Supabase o configuración incorrecta.

**Verificaciones:**
1. Verifica que las variables de entorno estén configuradas:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

2. Verifica en Vercel:
   - Settings → Environment Variables
   - Deben estar configuradas para Production, Preview y Development

3. Verifica en local (archivo `.env.local`):
   ```bash
   NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=tu-anon-key-aqui
   ```

---

## 📋 Checklist de Verificación

Antes de reportar un problema, verifica:

- [ ] Migración `migration_atribucion_temporal.sql` ejecutada en Supabase
- [ ] Columna `mes_aplicado` existe en tabla `ingresos`
- [ ] Función `calcular_mes_aplicado()` existe y funciona
- [ ] Políticas RLS configuradas correctamente
- [ ] Variables de entorno configuradas en Vercel/local
- [ ] Usuario autenticado en el dashboard
- [ ] Consola del navegador abierta para ver logs
- [ ] No hay errores previos en la consola

---

## 🔍 Logs de Debugging Avanzado

Si el problema persiste, captura estos logs:

### En la Consola del Navegador:
```javascript
// Ejecuta esto en la consola:
console.log('Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL)
console.log('Supabase Key:', process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.substring(0, 10) + '...')
```

### En Supabase (SQL Editor):
```sql
-- Ver los últimos 5 ingresos
SELECT * FROM ingresos ORDER BY created_at DESC LIMIT 5;

-- Ver estructura de la tabla
\d ingresos
```

---

## 📊 Ejemplo de Registro Exitoso

### Antes del Cobro:
```sql
SELECT COUNT(*) FROM ingresos WHERE cliente_id = 'uuid-cliente';
-- Resultado: 0
```

### Después del Cobro:
```sql
SELECT 
    fecha_cobro,
    periodo,
    mes_aplicado,
    monto_usd_total,
    detalle
FROM ingresos 
WHERE cliente_id = 'uuid-cliente'
ORDER BY created_at DESC 
LIMIT 1;
```

### Resultado Esperado:
```
fecha_cobro  | periodo  | mes_aplicado | monto_usd_total | detalle
-------------|----------|--------------|-----------------|-------------------------
2026-01-28   | 01-2026  | 02-2026      | 150.00          | Cobro adelantado para 02-2026
```

✅ Nota: `mes_aplicado` (02-2026) es **diferente** de `periodo` (01-2026)

---

## 🚀 Próximos Pasos Después del Fix

Una vez que el botón funcione:

1. **Probar el Selector de Vista:**
   - Ve al dashboard
   - Verás botones: **💰 Liquidez Actual** | **📊 Performance Mensual**
   - Cambia entre vistas y verifica que los números cambien

2. **Verificar Atribución Temporal:**
   ```sql
   -- Liquidez de Enero (todo lo cobrado en enero)
   SELECT SUM(monto_usd_total) 
   FROM ingresos 
   WHERE periodo = '01-2026';
   
   -- Performance de Enero (solo trabajo de enero)
   SELECT SUM(monto_usd_total) 
   FROM ingresos 
   WHERE mes_aplicado = '01-2026';
   
   -- Performance de Febrero (ya cobrado para febrero)
   SELECT SUM(monto_usd_total) 
   FROM ingresos 
   WHERE mes_aplicado = '02-2026';
   ```

3. **Leer la Documentación:**
   - `GUIA_ATRIBUCION_TEMPORAL.md` - Guía completa
   - `migration_atribucion_temporal.sql` - Comentarios en código

---

## 📞 Soporte

Si después de seguir todos estos pasos el problema persiste:

1. Captura los logs completos de la consola
2. Captura el resultado de `verify_db_schema.sql`
3. Captura el error exacto de Supabase
4. Incluye:
   - ¿Se ejecutó la migración? (Sí/No)
   - ¿Qué muestra la consola?
   - ¿Qué error ve el usuario?

---

**Última actualización:** 28 de Enero 2026  
**Versión:** 1.0.0  
**Estado:** ✅ Código actualizado con fallback automático
