# 🚀 Deploy Rápido - Panel de Tesorería Semanal

## ⚡ Quick Start (2 minutos)

### Paso 1: Verificar/Aplicar Migración (30 seg)

La función `obtener_detalle_cobros_semana()` ya está incluida en `migration_dia_cobro.sql`.

**Si ya aplicaste la migración anterior:**
- Ejecuta solo desde la línea 90 en adelante (la nueva función)

**Si es primera vez:**
- Ejecuta `migration_dia_cobro.sql` completo en Supabase SQL Editor

**Verificar que funcionó:**
```sql
-- Debería devolver filas si tienes clientes con vencimientos próximos
SELECT * FROM obtener_detalle_cobros_semana();
```

---

### Paso 2: Deploy a Vercel (1 min)

```bash
cd webapp
npx vercel --prod
```

**Output esperado:**
```
✓ Production: https://black-infra-dashboard.vercel.app [25s]
```

---

### Paso 3: Test Visual (30 seg)

1. **Abrir Dashboard:**
   ```
   https://black-infra-dashboard.vercel.app/dashboard
   ```

2. **Verificar Panel:**
   - Si hay clientes con vencimientos próximos, verás el panel amarillo
   - Debe mostrar: "Cobros pendientes esta semana"
   - Debe mostrar: "Total a cobrar: $X,XXX.XX"

3. **Click en el Panel:**
   - Debe expandirse mostrando la lista de clientes
   - Cada cliente debe tener:
     - Nombre
     - Badge de urgencia (Rojo/Amarillo/Naranja)
     - Fecha de cobro
     - Monto individual

---

## 🎨 Vista Previa Esperada

### Panel Colapsado:
```
┌─────────────────────────────────────┐
│ 📅 Cobros pendientes esta semana  ▼ │
│ 3 clientes con vencimiento próximo  │
│                                     │
│ 💵 Total a cobrar:      $1,850.00  │
└─────────────────────────────────────┘
```

### Panel Expandido:
```
┌─────────────────────────────────────┐
│ 📅 Cobros pendientes esta semana  ▲ │
│ 3 clientes con vencimiento próximo  │
│                                     │
│ 💵 Total a cobrar:      $1,850.00  │
├─────────────────────────────────────┤
│ Cliente A          [HOY] 🔴        │
│ 📅 27 de Enero     $600.00         │
│                                     │
│ Cliente B          [2 días] 🟡     │
│ 📅 29 de Enero     $750.00         │
│                                     │
│ Cliente C          [5 días] 🟠     │
│ 📅 1 de Febrero    $500.00         │
├─────────────────────────────────────┤
│ 💡 Tip: Los cobros atrasados        │
│ aparecen primero        2 urgentes  │
└─────────────────────────────────────┘
```

---

## 🧪 Checklist de Verificación

### Visual:
- [ ] Panel aparece en el Dashboard
- [ ] Muestra total en grande
- [ ] Click expande/colapsa suavemente
- [ ] Lista muestra todos los clientes
- [ ] Badges tienen colores correctos (Rojo/Amarillo/Naranja)
- [ ] Fechas en español: "28 de Enero"

### Funcional:
- [ ] Total coincide con suma manual de fees
- [ ] Lista ordenada por fecha (más próximo primero)
- [ ] Scroll funciona si hay >5 clientes
- [ ] Panel se oculta si no hay cobros

### Mobile:
- [ ] Panel se ve bien en iPhone
- [ ] Touch targets grandes y fáciles de presionar
- [ ] Texto legible sin zoom
- [ ] Scroll suave en lista

---

## 🐛 Troubleshooting Express

### Problema: "RPC function not found"
```sql
-- Verificar que la función existe:
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_name = 'obtener_detalle_cobros_semana';

-- Si no existe, ejecutar migration_dia_cobro.sql líneas 90-140
```

### Problema: Panel no aparece
**Causas:**
1. No hay clientes con `dia_cobro` definido
2. Ningún cliente vence en los próximos 7 días

**Solución de prueba:**
```sql
-- Configurar un cliente para que venza hoy:
UPDATE clientes 
SET dia_cobro = EXTRACT(DAY FROM CURRENT_DATE)
WHERE estado = 'Activo' 
LIMIT 1;
```

### Problema: Total en $0.00
**Verificar:**
```sql
-- Los clientes deben tener fee_mensual definido:
SELECT nombre, fee_mensual, dia_cobro 
FROM clientes 
WHERE estado = 'Activo' AND dia_cobro IS NOT NULL;
```

### Problema: Panel no se expande
**Revisar:**
1. Console del navegador (F12)
2. Verificar que no haya errores de JavaScript
3. Probar con click en cualquier parte del header

---

## 📊 Datos de Prueba

Para testear con clientes de ejemplo:

```sql
-- Crear clientes con vencimientos variados:
UPDATE clientes SET dia_cobro = EXTRACT(DAY FROM CURRENT_DATE) + 0 WHERE nombre ILIKE '%cliente1%';  -- HOY
UPDATE clientes SET dia_cobro = EXTRACT(DAY FROM CURRENT_DATE) + 2 WHERE nombre ILIKE '%cliente2%';  -- 2 días
UPDATE clientes SET dia_cobro = EXTRACT(DAY FROM CURRENT_DATE) + 5 WHERE nombre ILIKE '%cliente3%';  -- 5 días

-- Ver resultado:
SELECT * FROM obtener_detalle_cobros_semana();
```

---

## 🎯 Diferencias vs Widget Anterior

### Antes (Widget Simple):
```
📅 Cobros pendientes esta semana: 3
```

### Ahora (Panel Detallado):
```
📅 Cobros pendientes esta semana ▼
3 clientes con vencimiento próximo

💵 Total a cobrar: $1,850.00

[Lista detallada al expandir]
```

**Ventajas:**
- ✅ Total a cobrar visible
- ✅ Desglose por cliente
- ✅ Fechas exactas de cobro
- ✅ Badges de urgencia
- ✅ Mobile-friendly
- ✅ Expandible/colapsable

---

## ✅ Deploy Exitoso!

Si todos los checks están ✅, el panel está operativo.

**Próximos pasos recomendados:**
1. Configurar `dia_cobro` para todos los clientes activos
2. Monitorear cobros HOY y atrasados
3. Usar el panel como herramienta de cobranza diaria

---

## 📞 Soporte

Si algo no funciona:
1. F12 → Console (ver errores JavaScript)
2. Network tab (ver respuesta de RPC call)
3. Supabase Dashboard → Logs
4. Verificar que la migración se aplicó correctamente
