# 📅 Guía de Atribución Temporal de Ingresos

## 🎯 Concepto Fundamental

**Los cobros son por adelantado**. Esto significa que cuando cobro hoy, el dinero **ya es mío** (impacta mi liquidez inmediatamente), pero ese pago corresponde al **servicio del mes siguiente**.

## 📊 Dos Tipos de Vista en el Dashboard

### 💰 Vista: Liquidez Actual (Verde Neón)
**¿Qué muestra?** Todo el dinero que ha entrado a mi cuenta en este periodo.

**¿Cómo filtra?** Por `periodo` (cuando se registró el cobro en el sistema).

**Ejemplo:**
```
Hoy es 28 de Enero 2026
- Cobro a Cashboom: $150 → Entra HOY a mi cuenta
- Cobro a Telecom: $200 → Entra HOY a mi cuenta
---
LIQUIDEZ ENERO: $350 (dinero real en mi cuenta)
```

**¿Cuándo usar esta vista?**
- Para saber cuánto dinero tengo disponible HOY
- Para calcular mi caja real
- Para decisiones de tesorería inmediatas

### 📊 Vista: Performance Mensual (Azul)
**¿Qué muestra?** Solo los ingresos que corresponden al trabajo realizado en este mes específico.

**¿Cómo filtra?** Por `mes_aplicado` (a qué mes de servicio pertenece el cobro).

**Ejemplo:**
```
Hoy es 28 de Enero 2026
- Cobro a Cashboom: $150 → Pero es por el servicio de FEBRERO
- Cobro a Telecom: $200 → Pero es por el servicio de FEBRERO
---
PERFORMANCE ENERO: $0 (no cobré nada del trabajo de enero)
PERFORMANCE FEBRERO: $350 (ya cobré esto para febrero)
```

**¿Cuándo usar esta vista?**
- Para evaluar la rentabilidad de un mes específico
- Para comparar performance entre meses
- Para reportes de objetivos mensuales

## 🗄️ Estructura de Base de Datos

### Tabla `ingresos`

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id` | UUID | Identificador único | `abc-123-def-456` |
| `cliente_id` | UUID | Cliente que pagó | `Cashboom-uuid` |
| `monto_usd_total` | NUMERIC | Monto cobrado | `150.00` |
| `fecha_cobro` | DATE | **Cuándo entró el dinero** | `2026-01-28` |
| `periodo` | VARCHAR(7) | Periodo del sistema al registrar | `01-2026` |
| `mes_aplicado` | VARCHAR(7) | **A qué mes pertenece el servicio** | `02-2026` |
| `detalle` | TEXT | Descripción | `Cobro adelantado para 02-2026` |

### 🔑 Diferencias Clave

```sql
-- LIQUIDEZ: ¿Cuánto cobré en Enero?
SELECT SUM(monto_usd_total) 
FROM ingresos 
WHERE periodo = '01-2026';  -- Todo lo registrado en enero

-- PERFORMANCE: ¿Cuánto facturé por el trabajo de Enero?
SELECT SUM(monto_usd_total) 
FROM ingresos 
WHERE mes_aplicado = '01-2026';  -- Solo lo que corresponde a enero
```

## 🎬 Flujo de Registro de Cobro

### Paso 1: Usuario hace clic en "Cobrar"
```
Cliente: Cashboom
Monto: $150
Fecha: 28 de Enero 2026
```

### Paso 2: Sistema calcula automáticamente
```javascript
const fechaCobroHoy = new Date('2026-01-28')
const mesProximo = new Date(fechaCobroHoy)
mesProximo.setMonth(mesProximo.getMonth() + 1)  // Mes siguiente

// Resultado: Febrero 2026 = '02-2026'
```

### Paso 3: Registro en Supabase
```javascript
{
  cliente_id: 'cashboom-uuid',
  monto_usd_total: 150.00,
  fecha_cobro: '2026-01-28',        // Cuándo entró el dinero
  periodo: '01-2026',                // Contexto: Enero (cuando lo registré)
  mes_aplicado: '02-2026',           // Servicio: Febrero (a qué mes pertenece)
  detalle: 'Cobro adelantado para 02-2026'
}
```

### Paso 4: Toast de confirmación
```
✅ Cashboom: $150 cobrado para Febrero
```

## 📈 Casos de Uso Reales

### Caso 1: Cobro Normal Adelantado
```
HOY: 28 Enero 2026
ACCIÓN: Cobro a Cashboom $150

RESULTADO:
✓ fecha_cobro: 2026-01-28
✓ periodo: 01-2026 (Enero)
✓ mes_aplicado: 02-2026 (Febrero)

DASHBOARD:
- Liquidez Enero: +$150 ✅
- Performance Enero: No cambia
- Performance Febrero: +$150 ✅
```

### Caso 2: Ver Performance de Enero
```
SELECTOR: Enero 2026
VISTA: Performance Mensual

MUESTRA:
- Solo cobros donde mes_aplicado = '01-2026'
- Estos cobros probablemente se registraron en Diciembre 2025
- Representa el trabajo realizado EN enero
```

### Caso 3: Ver Liquidez de Enero
```
SELECTOR: Enero 2026
VISTA: Liquidez Actual

MUESTRA:
- Todo lo cobrado donde periodo = '01-2026'
- Sin importar a qué mes de servicio pertenece
- Representa el dinero que entró EN enero
```

## 🚨 Validaciones Implementadas

### 1. No Duplicar Cobros
```
El sistema verifica que no exista otro cobro para:
- Mismo cliente
- Mismo mes_aplicado

Ejemplo:
❌ No puedo cobrar dos veces a Cashboom para Febrero
```

### 2. Mensaje Claro de Error
```
Si intento duplicar:
"Ya existe un cobro para Febrero 2026"
```

### 3. Confirmación Clara
```
Al registrar exitosamente:
"✅ Cashboom: $150 cobrado para Febrero"
(No dice "cobrado en enero" para evitar confusión)
```

## 🎨 UI/UX del Dashboard

### Selector de Vista (Botones)
```
┌─────────────────┬─────────────────┐
│ 💰 Liquidez     │ 📊 Performance  │
│ Actual          │ Mensual         │
│ [ACTIVO]        │                 │
└─────────────────┴─────────────────┘
```

### Tarjeta Principal (cambia según vista)
```
LIQUIDEZ:
┌────────────────────────────────┐
│ 💰 Liquidez Total              │
│ [Todo cobrado]                 │
│                                │
│ $2,500.00                      │
│ $3,000,000 ARS                 │
│                                │
│ 💡 Todo el dinero que entró    │
│    en este periodo             │
└────────────────────────────────┘

PERFORMANCE:
┌────────────────────────────────┐
│ 📊 Neto del Mes                │
│ [Solo este mes]                │
│                                │
│ $1,800.00                      │
│ $2,160,000 ARS                 │
│                                │
│ 💡 Solo los ingresos que       │
│    corresponden al trabajo     │
│    de este mes                 │
└────────────────────────────────┘
```

## 🔧 Funciones SQL Disponibles

### Calcular Mes Aplicado
```sql
SELECT calcular_mes_aplicado(CURRENT_DATE);
-- Retorna: '02-2026' si hoy es enero
```

### Obtener Ingresos (Liquidez)
```sql
SELECT * FROM obtener_ingresos_dashboard('01-2026', 'liquidez');
-- Retorna: Todo lo cobrado en enero
```

### Obtener Ingresos (Performance)
```sql
SELECT * FROM obtener_ingresos_dashboard('01-2026', 'performance');
-- Retorna: Solo lo que corresponde al trabajo de enero
```

## 📋 Checklist de Migración

Para aplicar esta funcionalidad en Supabase:

- [ ] 1. Ejecutar `migration_atribucion_temporal.sql` en Supabase SQL Editor
- [ ] 2. Verificar que la columna `mes_aplicado` existe en tabla `ingresos`
- [ ] 3. Verificar que los índices se crearon correctamente
- [ ] 4. Verificar que las funciones SQL están disponibles
- [ ] 5. Migrar datos existentes (si los hay) ejecutando el UPDATE
- [ ] 6. Deploy del frontend actualizado
- [ ] 7. Probar registro de un cobro nuevo
- [ ] 8. Verificar que el mes_aplicado se calcula correctamente
- [ ] 9. Verificar selector de vista en dashboard
- [ ] 10. Confirmar que las dos vistas muestran datos diferentes

## ❓ FAQ

**P: ¿Por qué necesito dos columnas (`periodo` y `mes_aplicado`)?**
R: Porque son conceptos diferentes. `periodo` es CUÁNDO cobré (para liquidez), `mes_aplicado` es A QUÉ MES PERTENECE (para performance).

**P: ¿Qué pasa si cobro el 1 de Febrero?**
R: El sistema calculará que `mes_aplicado = '03-2026'` (Marzo), porque sigue siendo cobro adelantado.

**P: ¿Puedo cambiar el mes_aplicado manualmente?**
R: Sí, puedes editarlo directamente en Supabase si necesitas corregir algo. Pero el sistema lo calcula automáticamente.

**P: ¿Qué vista debo usar por defecto?**
R: **Liquidez**, porque es lo que más interesa día a día (cuánto dinero tengo disponible).

**P: ¿Cómo sé si estoy cumpliendo objetivos mensuales?**
R: Usa la vista **Performance Mensual** y mira el mes específico que quieres evaluar.

## 🎯 Objetivos Cumplidos

✅ Separación clara entre liquidez y performance
✅ Cobros adelantados correctamente atribuidos
✅ Dashboard con selector de vista
✅ Validación de duplicados por mes aplicado
✅ Mensajes claros al usuario
✅ Base de datos correctamente estructurada
✅ Funciones SQL helpers disponibles
✅ Documentación completa

---

**Última actualización:** 28 de Enero 2026
**Versión:** 1.0.0
**Autor:** Black Infrastructure Dashboard Team
