# 🚀 Deploy Rápido - Sistema de Vencimientos

## ⚡ Quick Start (3 minutos)

### Paso 1: Aplicar Migración en Supabase (1 min)

1. **Abrir Supabase Dashboard**
   - URL: https://supabase.com/dashboard
   - Project: BLACK_INFRA

2. **Ir a SQL Editor**
   - Click en "SQL Editor" en el menú lateral

3. **Ejecutar Migración**
   - Copiar todo el contenido de `migration_dia_cobro.sql`
   - Pegar en el editor
   - Click en "Run" (▶️)
   - **Resultado esperado:** `Success. No rows returned`

4. **Verificar que funcionó:**
```sql
-- Ejecutar esta query de verificación:
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'clientes' AND column_name = 'dia_cobro';

-- Debe mostrar:
-- column_name | data_type
-- dia_cobro   | integer
```

---

### Paso 2: Deploy a Vercel (1 min)

```bash
cd webapp
npx vercel --prod
```

**Output esperado:**
```
✓ Production: https://black-infra-webapp-pure.vercel.app [23s]
```

---

### Paso 3: Test en Producción (1 min)

#### A. Verificar Widget del Dashboard
1. Abrir: `https://black-infra-webapp-pure.vercel.app/dashboard`
2. Si hay clientes con vencimientos próximos, debe aparecer:
   ```
   📅 Cobros pendientes esta semana: [X]
   ```

#### B. Verificar CRM
1. Ir a: `/dashboard/clientes`
2. Abrir cualquier cliente activo
3. **Debe ver nuevo campo:** "Día de Cobro" con input numérico (1-31)

#### C. Test Funcional Completo
1. En un cliente activo, ingresar `dia_cobro = 15`
2. Guardar (debería guardarse automáticamente)
3. **Resultado esperado:** Aparece badge "Próximo pago: [fecha]"
4. Si la fecha es cercana (≤3 días), el badge debe ser AMARILLO 🟡
5. Si es HOY o atrasado, debe ser ROJO 🔴 y pulsar

---

## 🎨 Ejemplos Visuales

### CRM con Vencimiento Normal:
```
┌─────────────────────────────────────┐
│ Cliente XYZ              [Activo]   │
│ Fee: $500    Día Cobro: [15]       │
│ 📅 Próximo pago: 15/02/2026 🔵     │ ← Normal (azul)
└─────────────────────────────────────┘
```

### CRM con Vencimiento Urgente:
```
┌─────────────────────────────────────┐
│ Cliente ABC              [Activo]   │
│ Fee: $800    Día Cobro: [28]       │
│ 📅 Próximo pago: En 2 días 🟡      │ ← Urgente (amarillo)
└─────────────────────────────────────┘
```

### CRM con Vencimiento Atrasado:
```
┌─────────────────────────────────────┐
│ Cliente DEF              [Activo]   │
│ Fee: $600    Día Cobro: [20]       │
│ ⚠️ Próximo pago: Atrasado 3 días 🔴│ ← Atrasado (rojo + pulse)
└─────────────────────────────────────┘
```

---

## 🧪 Test de Aceptación

### Checklist Mínimo:
- [ ] Migración ejecutada sin errores
- [ ] Deploy a Vercel exitoso
- [ ] Campo "Día de Cobro" visible en CRM
- [ ] Al ingresar día, aparece "Próximo pago"
- [ ] Colores de alerta funcionan
- [ ] Widget del dashboard aparece si hay cobros

---

## 🐛 Troubleshooting

### Problema: "Column dia_cobro does not exist"
**Solución:** La migración no se aplicó. Volver al Paso 1.

### Problema: No aparece el widget de cobros pendientes
**Causas posibles:**
1. No hay clientes activos con `dia_cobro` definido
2. Ningún cliente tiene vencimiento en los próximos 7 días

**Solución de prueba:**
```sql
-- Crear un cliente de prueba con vencimiento HOY:
UPDATE clientes 
SET dia_cobro = EXTRACT(DAY FROM CURRENT_DATE)
WHERE estado = 'Activo' 
LIMIT 1;
```

### Problema: Badge de próximo pago no aparece
**Verificar:**
1. El cliente debe tener `estado = 'Activo'`
2. El cliente debe tener `dia_cobro` definido (no NULL)
3. Refrescar la página

---

## 📊 Datos de Prueba (Opcional)

Si querés testear con datos reales, ejecutá esto en Supabase:

```sql
-- Actualizar algunos clientes con días de cobro variados
UPDATE clientes SET dia_cobro = 5 WHERE nombre ILIKE '%cliente1%';
UPDATE clientes SET dia_cobro = 15 WHERE nombre ILIKE '%cliente2%';
UPDATE clientes SET dia_cobro = 25 WHERE nombre ILIKE '%cliente3%';

-- Ver resultado:
SELECT nombre, estado, dia_cobro, 
       calcular_proximo_vencimiento(dia_cobro) AS proximo_pago
FROM clientes 
WHERE dia_cobro IS NOT NULL;
```

---

## ✅ Todo Listo!

Si todos los checks están verdes, el sistema está operativo! 🎉

**Próximo paso recomendado:** Configurar días de cobro para todos los clientes activos.

---

## 📞 Contacto

Si algo no funciona, revisar:
1. Console del navegador (F12)
2. Network tab de DevTools
3. Supabase Logs (Dashboard → Logs)
