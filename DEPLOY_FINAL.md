# 🚀 DEPLOY FINAL - BLACK INFRA v16.0

## 📋 Checklist Pre-Deploy

### ✅ Completado (Código Listo):
- [x] Time Machine (PeriodoSelector) implementado
- [x] Context Provider de Periodo
- [x] Sistema de Vencimientos en CRM
- [x] Panel de Tesorería Semanal
- [x] Funciones SQL preparadas
- [x] Helpers de frontend creados
- [x] Componentes con estilo glassmorphism
- [x] Mobile-optimized
- [x] Sin errores de linter
- [x] Documentación completa

---

## 🎯 Pasos de Deployment (5 minutos)

### Paso 1: Aplicar Migraciones en Supabase (2 min)

#### A. Migración de Periodos (Si no se aplicó antes):
1. Ir a: https://supabase.com/dashboard → SQL Editor
2. Copiar contenido de `migration_periodo.sql`
3. Ejecutar (Run ▶️)
4. Verificar:
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name IN ('ingresos', 'costos') AND column_name = 'periodo';
-- Debe mostrar: periodo | character varying
```

#### B. Migración de Día de Cobro (NUEVA):
1. En el mismo SQL Editor
2. Copiar contenido de `migration_dia_cobro.sql`
3. Ejecutar (Run ▶️)
4. Verificar:
```sql
-- Verificar columna:
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'clientes' AND column_name = 'dia_cobro';
-- Debe mostrar: dia_cobro | integer

-- Verificar funciones:
SELECT routine_name FROM information_schema.routines 
WHERE routine_name IN ('calcular_proximo_vencimiento', 'obtener_detalle_cobros_semana');
-- Debe mostrar ambas funciones
```

---

### Paso 2: Deploy a Vercel (2 min)

```bash
cd webapp
npx vercel --prod
```

**Output esperado:**
```
✓ Production: https://black-infra-dashboard.vercel.app [30s]
```

---

### Paso 3: Verificación en Producción (1 min)

#### A. Time Machine:
1. Abrir: https://black-infra-dashboard.vercel.app/dashboard
2. **Debe ver:**
   - [ ] Dropdown de periodo en header
   - [ ] Muestra "Enero 2026" (o mes actual)
   - [ ] Badge en KPI "Neto USD" con mes
3. **Test funcional:**
   - [ ] Click en dropdown → muestra últimos 12 meses
   - [ ] Seleccionar otro mes → KPIs se actualizan
   - [ ] Gráfico cambia de datos

#### B. Sistema de Vencimientos:
1. Ir a: /dashboard/clientes
2. **Debe ver:**
   - [ ] Campo "Día de Cobro" (1-31) en cada cliente
   - [ ] Input numérico editable
3. **Test funcional:**
   - [ ] Ingresar día (ej: 15) → guarda automáticamente
   - [ ] Aparece badge "Próximo pago: [fecha]"
   - [ ] Badge tiene color según urgencia

#### C. Panel de Tesorería:
1. Volver a: /dashboard
2. **Debe ver (si hay clientes con vencimientos):**
   - [ ] Panel amarillo "Cobros pendientes esta semana"
   - [ ] Total a cobrar en grande: `$X,XXX.XX`
3. **Test funcional:**
   - [ ] Click en panel → se expande
   - [ ] Muestra lista de clientes
   - [ ] Cada fila tiene: nombre, fecha, monto, badge
   - [ ] Badges rojos/amarillos/naranjas según urgencia
   - [ ] Click de nuevo → se colapsa

---

## 🧪 Testing Completo (Opcional - 5 min)

### Test 1: Time Machine
```sql
-- Agregar datos de prueba en diferentes periodos:
INSERT INTO ingresos (concepto, monto_ars, monto_usd_total, fecha_cobro, periodo)
VALUES 
  ('Test Ene', 100000, 1000, '2026-01-15', '01-2026'),
  ('Test Dic', 100000, 1000, '2025-12-15', '12-2025');

-- Verificar en UI que el selector filtra correctamente
```

### Test 2: Vencimientos
```sql
-- Configurar clientes con vencimientos variados:
UPDATE clientes 
SET dia_cobro = EXTRACT(DAY FROM CURRENT_DATE)
WHERE estado = 'Activo' AND nombre ILIKE '%cliente1%';  -- HOY

UPDATE clientes 
SET dia_cobro = EXTRACT(DAY FROM CURRENT_DATE) + 2
WHERE estado = 'Activo' AND nombre ILIKE '%cliente2%';  -- 2 días

-- Verificar en CRM:
-- - Cliente1 debe tener badge ROJO "HOY"
-- - Cliente2 debe tener badge AMARILLO "2 días"
```

### Test 3: Panel de Tesorería
```sql
-- Ver detalle de cobros:
SELECT * FROM obtener_detalle_cobros_semana();

-- Verificar que el total en UI coincida con la suma manual
```

---

## ✅ Checklist de Aceptación

### Funcionalidad:
- [ ] Time Machine filtra correctamente por periodo
- [ ] Selector muestra últimos 12 meses
- [ ] Dashboard se actualiza al cambiar periodo
- [ ] Campo "Día de Cobro" guarda y muestra correctamente
- [ ] Badge "Próximo pago" calcula fecha correcta
- [ ] Colores de urgencia funcionan (Rojo/Amarillo/Naranja)
- [ ] Panel de tesorería muestra total correcto
- [ ] Lista de clientes se expande/colapsa
- [ ] Scroll funciona con >5 clientes

### Visual (Mobile):
- [ ] Selector legible en iPhone
- [ ] Touch targets grandes (44px+)
- [ ] Panel de tesorería se ve bien en móvil
- [ ] Lista scrollea suavemente
- [ ] Badges de urgencia visibles

### Performance:
- [ ] Cambio de periodo < 500ms
- [ ] Panel se expande en < 300ms
- [ ] Queries con índices < 100ms

---

## 🐛 Troubleshooting

### Si el selector de periodo no aparece:
```bash
# Verificar que el Provider esté en layout:
grep -n "PeriodoProvider" webapp/app/layout.tsx
# Debe aparecer en línea 4 (import) y líneas 59-61 (wrapper)
```

### Si el panel de tesorería no aparece:
```sql
-- Verificar que haya clientes con vencimientos próximos:
SELECT * FROM obtener_detalle_cobros_semana();
-- Si devuelve 0 filas, configurar algún cliente con dia_cobro
```

### Si hay error "RPC function not found":
```sql
-- La migración no se aplicó. Ejecutar migration_dia_cobro.sql completo
```

---

## 📊 Datos Iniciales Recomendados

```sql
-- 1. Actualizar periodos de registros existentes:
UPDATE ingresos 
SET periodo = TO_CHAR(fecha_cobro::date, 'MM-YYYY')
WHERE periodo IS NULL AND fecha_cobro IS NOT NULL;

UPDATE costos 
SET periodo = TO_CHAR(created_at::date, 'MM-YYYY')
WHERE periodo IS NULL;

-- 2. Configurar días de cobro para clientes activos:
UPDATE clientes 
SET dia_cobro = 15  -- O el día que corresponda
WHERE estado = 'Activo' AND dia_cobro IS NULL;

-- 3. Verificar que todo está OK:
SELECT 
  'ingresos' as tabla,
  COUNT(*) as total,
  COUNT(periodo) as con_periodo
FROM ingresos
UNION ALL
SELECT 
  'costos',
  COUNT(*),
  COUNT(periodo)
FROM costos
UNION ALL
SELECT 
  'clientes',
  COUNT(*),
  COUNT(dia_cobro)
FROM clientes WHERE estado = 'Activo';
```

---

## 🎯 Resultado Esperado

### Dashboard:
```
┌──────────────────────────────────────┐
│ Dashboard              [Salir]       │
│ ┌──────────────────────────────────┐ │
│ │ 📅 ▼ Enero 2026                  │ │ ← Time Machine
│ └──────────────────────────────────┘ │
│                                      │
│ 💵 Neto USD         [Ene 2026]      │
│ $12,345.67                           │
│                                      │
│ 📅 Cobros pendientes esta semana  ▼ │ ← Panel de Tesorería
│ 3 clientes con vencimiento próximo  │
│ 💵 Total a cobrar:      $1,850.00   │
└──────────────────────────────────────┘
```

### CRM:
```
┌──────────────────────────────────────┐
│ Cliente: Juan Pérez      [Activo]    │
│ Fee: $500    Día Cobro: [15]        │
│ 📅 Próximo pago: En 2 días 🟡       │ ← Badge de urgencia
└──────────────────────────────────────┘
```

---

## ✅ Deploy Exitoso!

Si todos los checks están ✅, BLACK INFRA v16.0 está operativo! 🎉

### 🎁 Features Nuevas Disponibles:
1. ✅ Time Machine (Viaje en el tiempo por periodos)
2. ✅ Sistema de Vencimientos (Alertas por cliente)
3. ✅ Panel de Tesorería (Total semanal + desglose)

### 📚 Documentación:
- `RESUMEN_IMPLEMENTACION.md` - Overview general
- `FEATURE_VENCIMIENTOS.md` - Sistema de vencimientos
- `FEATURE_PANEL_TESORERIA.md` - Panel de tesorería
- `DEPLOY_VENCIMIENTOS.md` - Deploy vencimientos
- `DEPLOY_PANEL_TESORERIA.md` - Deploy panel
- `CORE_CONTEXT.md` - Contexto actualizado

---

## 🚀 Próximos Pasos Recomendados:

1. **Configurar días de cobro** para todos los clientes activos
2. **Monitorear cobros** HOY y atrasados diariamente
3. **Usar Time Machine** para análisis histórico
4. **Exportar reportes** mensuales (futuro)

---

## 📞 Soporte

Si algo no funciona:
1. F12 → Console (errores JavaScript)
2. Network tab (respuestas de API)
3. Supabase → Logs
4. Verificar que ambas migraciones se aplicaron

**Email de soporte:** [Tu email aquí]
**Repo:** [Tu repo aquí]
