# 📅 Feature: Sistema de Vencimientos y Próximos Cobros

## ✅ Implementación Completada - 27/01/2026

### 🎯 Objetivo
Implementar un sistema de seguimiento de vencimientos de cobros por cliente para mejorar la gestión de flujo de caja y alertas tempranas de pagos pendientes.

---

## 📦 Archivos Creados/Modificados

### Nuevos Archivos:
1. **`migration_dia_cobro.sql`** - Migración de base de datos
   - Columna `dia_cobro` en tabla `clientes`
   - Funciones SQL para cálculo de vencimientos
   - Vista `v_clientes_vencimientos`
   - Función `obtener_cobros_semana()`

2. **`webapp/lib/vencimientos.ts`** - Helpers de frontend
   - `calcularProximoPago()`: Calcula fecha del próximo pago
   - `formatearFecha()`: Formato dd/mm/yyyy
   - `getTextoPago()`: Texto descriptivo del vencimiento
   - `getClasesUrgencia()`: Clases de Tailwind según urgencia

### Archivos Modificados:
1. **`webapp/lib/supabase.ts`**
   - Agregado campo `dia_cobro?: number` al tipo `Cliente`

2. **`webapp/app/dashboard/clientes/page.tsx`**
   - Campo editable "Día de Cobro" (1-31) en cada card
   - Visualización de "Próximo pago" con alertas de color
   - Agregado campo en modal de nuevo cliente

3. **`webapp/app/dashboard/page.tsx`**
   - Widget "Cobros pendientes esta semana"
   - Muestra cantidad de clientes con vencimiento en 7 días

---

## 🎨 Sistema de Alertas Visuales

### Colores por Urgencia:

| Estado | Condición | Color | Efecto |
|--------|-----------|-------|--------|
| **ATRASADO** | Días < 0 | 🔴 Rojo neón | Animación pulse |
| **HOY** | Días = 0 | 🔴 Rojo neón | Animación pulse |
| **URGENTE** | Días ≤ 3 | 🟡 Amarillo | Border sólido |
| **ESTA_SEMANA** | Días ≤ 7 | 🟠 Naranja | Border suave |
| **NORMAL** | Días > 7 | 🔵 Azul | Sin alerta |

---

## 🔧 Lógica de Negocio

### Cálculo del Próximo Pago:

```javascript
// Si hoy es 20 de enero y el cliente cobra el día 15:
// → Próximo pago: 15 de febrero

// Si hoy es 10 de enero y el cliente cobra el día 15:
// → Próximo pago: 15 de enero (mismo mes)

// Si el cliente cobra el día 31 en febrero:
// → Próximo pago: 28 de febrero (último día del mes)
```

### Widget del Dashboard:

- **Muestra solo si hay cobros pendientes** (>0)
- **Filtra clientes Activos** con día de cobro definido
- **Cuenta vencimientos dentro de 7 días** (incluye hoy y atrasados)

---

## 📊 Estructura de Datos

### Tabla `clientes` (Nueva columna):

```sql
dia_cobro INTEGER
  - Rango: 1 a 31
  - Nullable: TRUE (opcional)
  - Constraint: CHECK (dia_cobro >= 1 AND dia_cobro <= 31)
  - Índice: idx_clientes_dia_cobro
```

### Vista SQL `v_clientes_vencimientos`:

```sql
SELECT 
  c.id,
  c.nombre,
  c.estado,
  c.fee_mensual,
  c.dia_cobro,
  calcular_proximo_vencimiento(c.dia_cobro) AS proximo_vencimiento,
  calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE AS dias_hasta_vencimiento
FROM clientes c
WHERE c.estado = 'Activo'
ORDER BY proximo_vencimiento ASC
```

---

## 🚀 Deployment Checklist

### 1. Aplicar Migración en Supabase:
```bash
# Conectarse a Supabase SQL Editor y ejecutar:
# /BLACK_INFRA/migration_dia_cobro.sql
```

### 2. Deploy a Vercel:
```bash
cd webapp
npx vercel --prod
```

### 3. Verificar en Producción:
- [ ] Dashboard muestra widget de cobros pendientes
- [ ] CRM muestra campo "Día de Cobro" editable
- [ ] Al agregar día de cobro, aparece "Próximo pago"
- [ ] Colores de alerta funcionan correctamente
- [ ] Nuevo cliente permite definir día de cobro

---

## 🧪 Casos de Prueba

### Test 1: Agregar Día de Cobro
1. Ir a `/dashboard/clientes`
2. Editar un cliente activo
3. Ingresar día de cobro: `15`
4. Guardar
5. **Resultado esperado:** Aparece badge "Próximo pago: [fecha]"

### Test 2: Verificar Alertas de Color
1. Configurar cliente con `dia_cobro = HOY`
2. **Resultado esperado:** Badge ROJO con animación pulse
3. Configurar cliente con `dia_cobro = HOY + 2 días`
4. **Resultado esperado:** Badge AMARILLO

### Test 3: Widget de Dashboard
1. Configurar 3 clientes con vencimientos en los próximos 7 días
2. Ir a `/dashboard`
3. **Resultado esperado:** Widget muestra "Cobros pendientes esta semana: 3"

### Test 4: Cliente con Día Inválido (Ej: 31 de febrero)
1. Configurar cliente con `dia_cobro = 31` en enero
2. **Resultado esperado:** En febrero, muestra 28/29 (último día del mes)

---

## 📱 UI/UX Implementado

### CRM (`/dashboard/clientes`):

```
┌─────────────────────────────────────┐
│ Cliente: Juan Pérez        [Activo] │
├─────────────────────────────────────┤
│ Fee Mensual: $500  Día Cobro: [15]  │
│                                     │
│ 📅 Próximo pago: [En 2 días] 🟡    │ ← Alerta amarilla
└─────────────────────────────────────┘
```

### Dashboard Principal:

```
┌─────────────────────────────────────┐
│ 📅 Cobros pendientes esta semana    │
│ Clientes con vencimiento próximo    │
│                              [5] ⚠️ │
└─────────────────────────────────────┘
```

---

## 🔍 Queries Útiles de Supabase

### Ver todos los vencimientos de clientes activos:
```sql
SELECT * FROM v_clientes_vencimientos;
```

### Ver cobros de esta semana:
```sql
SELECT * FROM obtener_cobros_semana();
```

### Actualizar día de cobro masivamente:
```sql
-- Ejemplo: Todos los clientes cobran el día 15
UPDATE clientes 
SET dia_cobro = 15 
WHERE estado = 'Activo' AND dia_cobro IS NULL;
```

### Clientes atrasados:
```sql
SELECT 
  nombre, 
  dia_cobro,
  calcular_proximo_vencimiento(dia_cobro) AS vencimiento
FROM clientes
WHERE estado = 'Activo' 
  AND dia_cobro IS NOT NULL
  AND calcular_proximo_vencimiento(dia_cobro) < CURRENT_DATE
ORDER BY vencimiento;
```

---

## 🎯 Próximas Mejoras (Backlog)

- [ ] **Notificaciones automáticas** vía Telegram cuando hay cobros atrasados
- [ ] **Vista de calendario** con todos los vencimientos del mes
- [ ] **Historial de pagos** por cliente
- [ ] **Exportar reporte PDF** de cobros pendientes
- [ ] **Dashboard de cobranza** con métricas de puntualidad
- [ ] **Predicción de flujo de caja** basada en vencimientos

---

## 📞 Soporte

Si hay problemas con los vencimientos:

1. **Verificar migración aplicada:**
   ```sql
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'clientes' AND column_name = 'dia_cobro';
   ```

2. **Verificar funciones creadas:**
   ```sql
   SELECT routine_name FROM information_schema.routines 
   WHERE routine_name = 'calcular_proximo_vencimiento';
   ```

3. **Revisar errores de validación:**
   - El día debe estar entre 1 y 31
   - Solo aplica para clientes con estado "Activo"

---

## ✅ Checklist Final

- [x] Migración SQL creada
- [x] Helpers de frontend implementados
- [x] Campo editable en CRM
- [x] Alertas de color funcionando
- [x] Widget en Dashboard
- [x] Modal de nuevo cliente actualizado
- [x] Linter sin errores
- [x] Documentación completa

**Status:** ✅ **READY FOR PRODUCTION**
