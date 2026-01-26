# Implementación de Periodos (MM-YYYY)

## 📅 Fecha: 24 de Enero 2026

## 🎯 Objetivo

Agregar soporte para filtrar ingresos y gastos por periodo mensual usando formato `MM-YYYY`, permitiendo:
- Consultar datos del mes actual automáticamente
- Filtrar datos de meses anteriores
- Mejorar performance con índices

---

## 📊 Cambios en la Base de Datos

### 1. Nueva Columna: `periodo`

**Formato:** `MM-YYYY` (ej: `01-2026`, `12-2025`)

**Tablas Afectadas:**
- `ingresos`
- `costos`

**Tipo:** `VARCHAR(7)`

### 2. Índices Creados

```sql
CREATE INDEX idx_ingresos_periodo ON ingresos(periodo);
CREATE INDEX idx_costos_periodo ON costos(periodo);
```

### 3. Vistas Creadas

**Vista: `ingresos_mes_actual`**
```sql
SELECT * FROM ingresos WHERE periodo = TO_CHAR(CURRENT_DATE, 'MM-YYYY');
```

**Vista: `costos_mes_actual`**
```sql
SELECT * FROM costos WHERE periodo = TO_CHAR(CURRENT_DATE, 'MM-YYYY');
```

---

## 🔧 Cambios en el Backend

### Archivo: `main.py`

**Antes:**
```python
# Usaba fecha_cobro >= primer_dia_mes
ingreso_existente = supabase.table("ingresos")\
    .select("id")\
    .eq("concepto", "PST_REPARTO")\
    .gte("fecha_cobro", primer_dia_mes)\
    .execute()
```

**Después:**
```python
# Usa periodo MM-YYYY
periodo_actual = datetime.now().strftime("%m-%Y")  # "01-2026"
ingreso_existente = supabase.table("ingresos")\
    .select("id")\
    .eq("concepto", "PST_REPARTO")\
    .eq("periodo", periodo_actual)\
    .execute()
```

**Campos guardados:**
```python
{
    "concepto": "PST_REPARTO",
    "monto_usd_total": 123.45,
    "monto_ars": 0,
    "fecha_cobro": "2026-01-24",
    "periodo": "01-2026",  # ✅ NUEVO
    "cliente_id": None
}
```

---

## 💻 Uso en el Frontend

### Queries Recomendadas

**1. Obtener datos del mes actual:**
```typescript
const periodoActual = new Date().toLocaleDateString('es-AR', { 
  month: '2-digit', 
  year: 'numeric' 
}).replace('/', '-')  // "01-2026"

const { data, error } = await supabase
  .from('ingresos')
  .select('*')
  .eq('periodo', periodoActual)
```

**2. Obtener lista de periodos disponibles:**
```typescript
const { data, error } = await supabase
  .rpc('get_periodos_disponibles', { limite: 12 })

// Retorna: [
//   { periodo: "01-2026", mes: 1, anio: 2026 },
//   { periodo: "12-2025", mes: 12, anio: 2025 },
//   ...
// ]
```

**3. Filtrar por periodo seleccionado:**
```typescript
const periodoSeleccionado = "12-2025"

const { data: ingresos } = await supabase
  .from('ingresos')
  .select('*')
  .eq('periodo', periodoSeleccionado)

const { data: costos } = await supabase
  .from('costos')
  .select('*')
  .eq('periodo', periodoSeleccionado)
```

---

## 🎨 Componente de Selector de Periodo (React)

```typescript
'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'

export default function PeriodoSelector() {
  const [periodos, setPeriodos] = useState([])
  const [periodoActual, setPeriodoActual] = useState('')
  
  useEffect(() => {
    cargarPeriodos()
  }, [])
  
  const cargarPeriodos = async () => {
    // Periodo actual
    const actual = new Date().toLocaleDateString('es-AR', { 
      month: '2-digit', 
      year: 'numeric' 
    }).replace('/', '-')
    setPeriodoActual(actual)
    
    // Lista de periodos disponibles
    const { data } = await supabase.rpc('get_periodos_disponibles', { limite: 12 })
    setPeriodos(data || [])
  }
  
  const handleChangePeriodo = (nuevoPeriodo) => {
    setPeriodoActual(nuevoPeriodo)
    // Aquí recargas los datos del dashboard con el nuevo periodo
  }
  
  return (
    <select 
      value={periodoActual} 
      onChange={(e) => handleChangePeriodo(e.target.value)}
      className="bg-white/5 text-white rounded-lg px-4 py-2"
    >
      {periodos.map(p => (
        <option key={p.periodo} value={p.periodo}>
          {formatPeriodo(p.periodo)} {/* "Enero 2026" */}
        </option>
      ))}
    </select>
  )
}

function formatPeriodo(periodo: string) {
  const [mes, anio] = periodo.split('-')
  const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
  return `${meses[parseInt(mes) - 1]} ${anio}`
}
```

---

## 📝 Migración de Datos Existentes

### Paso 1: Aplicar Migración SQL

```bash
# En Supabase SQL Editor, ejecutar:
migration_periodo.sql
```

### Paso 2: Verificar Datos

```sql
-- Ver registros sin periodo
SELECT COUNT(*) FROM ingresos WHERE periodo IS NULL;
SELECT COUNT(*) FROM costos WHERE periodo IS NULL;

-- Ver distribución por periodo
SELECT periodo, COUNT(*) 
FROM ingresos 
GROUP BY periodo 
ORDER BY periodo DESC;
```

### Paso 3: Corregir Registros Faltantes (si hay)

```sql
-- Ingresos sin periodo
UPDATE ingresos
SET periodo = TO_CHAR(fecha_cobro::date, 'MM-YYYY')
WHERE periodo IS NULL AND fecha_cobro IS NOT NULL;

-- Costos sin periodo
UPDATE costos
SET periodo = TO_CHAR(created_at::date, 'MM-YYYY')
WHERE periodo IS NULL;
```

---

## 🧪 Testing

### Tests Backend

```python
# Test: Crear ingreso con periodo
periodo = datetime.now().strftime("%m-%Y")
assert periodo == "01-2026"  # Enero 2026

# Test: Query por periodo
ingresos = supabase.table("ingresos").eq("periodo", "01-2026").execute()
assert len(ingresos.data) > 0
```

### Tests Frontend

```typescript
// Test: Periodo actual
const periodo = new Date().toLocaleDateString('es-AR', { 
  month: '2-digit', 
  year: 'numeric' 
}).replace('/', '-')
expect(periodo).toBe('01-2026')

// Test: Obtener periodos
const { data } = await supabase.rpc('get_periodos_disponibles')
expect(data).toHaveLength(12)
expect(data[0].periodo).toBe('01-2026')
```

---

## 📊 Performance

### Antes (sin periodo)
```sql
-- Query lenta con rango de fechas
WHERE fecha_cobro >= '2026-01-01' AND fecha_cobro < '2026-02-01'
```

### Después (con periodo)
```sql
-- Query rápida con índice
WHERE periodo = '01-2026'
```

**Mejora estimada:** 70-90% más rápido en tablas con +1000 registros

---

## 🔄 Cambios Automáticos al Inicio de Mes

**Comportamiento:**
- Al cambiar de mes (ej: 31 de Enero → 1 de Febrero)
- El sistema automáticamente usa el nuevo periodo: `02-2026`
- Los queries muestran el mes actual sin cambios manuales
- Los datos históricos permanecen con sus periodos originales

---

## 🚀 Deployment

### 1. Backend (Render)

```bash
git add main.py migration_periodo.sql IMPLEMENTACION_PERIODOS.md
git commit -m "feat: Agregar soporte de periodos MM-YYYY"
git push origin main
```

### 2. Database (Supabase)

1. Ir a Supabase Dashboard → SQL Editor
2. Pegar contenido de `migration_periodo.sql`
3. Ejecutar
4. Verificar con queries de prueba

### 3. Frontend (Vercel)

- Actualizar componente Dashboard para usar periodos
- Agregar selector de periodo
- Actualizar queries para filtrar por periodo

---

## 📚 Referencias

- [PostgreSQL Date/Time Functions](https://www.postgresql.org/docs/current/functions-datetime.html)
- [Supabase RPC Functions](https://supabase.com/docs/guides/database/functions)
- [JavaScript Date Formatting](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toLocaleDateString)

---

**Autor:** Senior Backend Developer  
**Fecha:** 24 de Enero 2026  
**Versión:** 1.0
