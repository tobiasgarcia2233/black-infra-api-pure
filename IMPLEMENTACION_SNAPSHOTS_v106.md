# IMPLEMENTACIÓN DE SNAPSHOTS MENSUALES v106.0
**Fecha:** 28 de Enero de 2026  
**Estado:** ✅ Backend Implementado - Frontend Pendiente

---

## 📸 Concepto: Snapshots de Cierre

Los **snapshots** son "fotografías" del estado financiero de PST.NET al final de cada mes. Esto previene que los datos históricos se pierdan cuando los valores en vivo cambien.

### Problema Resuelto:
- ❌ **Antes:** Al cambiar de mes, los datos viejos se pisaban
- ✅ **Ahora:** Cada mes tiene su "foto" preservada en `historial_saldos`

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────┐
│           NAVEGACIÓN DE MESES                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  Mes Actual (Enero 2026)                       │
│  ├─ Datos EN VIVO de PST.NET                   │
│  ├─ Cashback Stacking: Valor ACTUAL            │
│  └─ Sin snapshot (datos frescos)               │
│                                                 │
│  Meses Pasados (Diciembre 2025-)               │
│  ├─ Datos del SNAPSHOT histórico               │
│  ├─ Cashback Stacking: Valor ACTUAL (persiste) │
│  └─ Badge: "📸 Snapshot"                        │
│                                                 │
│  Meses Futuros (Febrero 2026+)                 │
│  ├─ Proyecciones basadas en ingresos           │
│  ├─ Cashback Stacking: Valor ACTUAL            │
│  └─ Badge: "🔮 Proyección"                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🗄️ Base de Datos

### Tabla: `historial_saldos`

```sql
CREATE TABLE historial_saldos (
    id UUID PRIMARY KEY,
    periodo VARCHAR(7) UNIQUE,  -- "01-2026"
    anio INTEGER,
    mes INTEGER,
    balance_cuentas_total DECIMAL(12, 2),
    neto_reparto DECIMAL(12, 2),
    cashback_aprobado DECIMAL(12, 2),
    cashback_hold DECIMAL(12, 2),
    desglose_por_currency JSONB,
    fecha_snapshot TIMESTAMP,
    notas TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 🔧 Backend Implementado

### 1. Módulo `snapshot_manager.py`

**Funciones:**
- `tomar_snapshot_mes_anterior()` - Crea snapshot del mes anterior
- `obtener_snapshot(periodo)` - Obtiene snapshot de un periodo
- `listar_snapshots()` - Lista todos los snapshots
- `verificar_snapshot_existe(periodo)` - Verifica existencia

### 2. Endpoints API (`api_server.py`)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/snapshot-mes-anterior` | POST | Crea snapshot del mes anterior |
| `/snapshot/{periodo}` | GET | Obtiene snapshot específico |
| `/snapshots` | GET | Lista todos los snapshots |

---

## 🎨 Frontend: Modificaciones Necesarias

### 1. Modificar `loadDashboardData()` en `page.tsx`

```typescript
const loadDashboardData = async (forceRefresh = false) => {
  try {
    setLoading(true)

    // Detectar mes actual
    const ahora = new Date()
    const mesActual = String(ahora.getMonth() + 1).padStart(2, '0')
    const anioActual = ahora.getFullYear()
    const periodoActual = `${mesActual}-${anioActual}`
    
    const esPeriodoActual = periodoSeleccionado === periodoActual
    const esPeriodoPasado = periodoSeleccionado < periodoActual
    
    let pst_balance_neto = 0
    let pst_incluido = false
    let es_snapshot = false
    
    // ============================================================
    // LÓGICA DE SNAPSHOTS
    // ============================================================
    
    if (esPeriodoPasado) {
      // MESES PASADOS: Intentar cargar snapshot histórico
      console.log(`📸 Cargando snapshot para periodo ${periodoSeleccionado}...`)
      
      try {
        const snapshotResponse = await fetch(
          `https://black-infra-api-pure.onrender.com/snapshot/${periodoSeleccionado}`
        )
        
        if (snapshotResponse.ok) {
          const snapshotData = await snapshotResponse.json()
          
          if (snapshotData.success && snapshotData.snapshot) {
            // Usar datos del snapshot
            pst_balance_neto = parseFloat(snapshotData.snapshot.neto_reparto || 0)
            pst_incluido = true
            es_snapshot = true
            
            console.log('✅ Snapshot cargado exitosamente')
            console.log(`   Neto reparto: $${pst_balance_neto}`)
          }
        } else {
          console.log('⚠️ No existe snapshot para este periodo, usando datos en vivo')
          // Fallback: Usar datos en vivo de configuración
          const { data: configPstBalance } = await supabase
            .from('configuracion')
            .select('valor_numerico')
            .eq('clave', 'pst_balance_neto')
            .single()
          
          pst_balance_neto = parseFloat(String(configPstBalance?.valor_numerico || 0))
          pst_incluido = false
        }
      } catch (error) {
        console.error('Error cargando snapshot:', error)
        // Fallback a datos en vivo
        pst_incluido = false
      }
      
    } else if (esPeriodoActual) {
      // MES ACTUAL: Usar datos EN VIVO
      console.log('💰 Mes actual: Usando datos EN VIVO')
      
      const { data: configPstBalance } = await supabase
        .from('configuracion')
        .select('valor_numerico')
        .eq('clave', 'pst_balance_neto')
        .single()
      
      pst_balance_neto = parseFloat(String(configPstBalance?.valor_numerico || 0))
      pst_incluido = true
      es_snapshot = false
      
    } else {
      // MESES FUTUROS: No incluir PST
      console.log('🔮 Mes futuro: PST NO incluido')
      pst_balance_neto = 0
      pst_incluido = false
      es_snapshot = false
    }
    
    // ... resto del código de cálculo ...
    
    setResumen({
      total_ars,
      total_usd,
      total_costos,
      neto_usd,
      ingresos_proyectados,
      pst_balance_neto,
      pst_incluido,
      es_snapshot,  // ← NUEVO: Indica si se está mostrando un snapshot
    })
    
  } catch (error) {
    console.error('Error al cargar datos:', error)
  } finally {
    setLoading(false)
  }
}
```

### 2. Agregar Badge de Snapshot en Hero Card

```typescript
{/* Badge de snapshot/proyección */}
{resumen?.es_snapshot && (
  <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
    📸 Snapshot Histórico
  </span>
)}

{!resumen?.pst_incluido && periodoSeleccionado > periodoActual && (
  <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20">
    🔮 Proyección
  </span>
)}
```

### 3. Cashback Stacking SIEMPRE Actual

```typescript
// Cashback Stacking SIEMPRE muestra valores actuales
// NO depende del periodo seleccionado

{/* Bloque Cashback Stacked - SIEMPRE ACTUAL */}
{cashbackAprobado > 0 || cashbackHold > 0) && (
  <div className="glass-card rounded-2xl p-4 border border-amber-500/20">
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <div className="p-2 bg-amber-500/10 rounded-lg">
          <Clock className="h-5 w-5 text-amber-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">Cashback Acumulado</h3>
          <p className="text-[10px] text-gray-400">
            Valor ACTUAL • No depende del mes seleccionado
          </p>
        </div>
      </div>
    </div>
    
    {/* Grid de Aprobado/Hold */}
    {/* ... código existente ... */}
  </div>
)}
```

---

## ⏰ Automatización: Cron Job

### Opción 1: Cron Nativo de Render

En el dashboard de Render, crear un **Cron Job** que ejecute:

```bash
# Ejecutar el día 1 de cada mes a las 02:00 AM
curl -X POST https://black-infra-api-pure.onrender.com/snapshot-mes-anterior
```

**Configuración:**
- Nombre: `snapshot-mensual`
- Comando: `curl -X POST https://black-infra-api-pure.onrender.com/snapshot-mes-anterior`
- Schedule: `0 2 1 * *` (Minuto 0, Hora 2, Día 1, Cualquier mes, Cualquier día semana)

### Opción 2: Vercel Cron Job

Crear archivo `webapp/app/api/cron-snapshot/route.ts`:

```typescript
export async function GET() {
  try {
    const response = await fetch(
      'https://black-infra-api-pure.onrender.com/snapshot-mes-anterior',
      { method: 'POST' }
    )
    
    const data = await response.json()
    
    return Response.json(data)
  } catch (error) {
    return Response.json(
      { success: false, error: String(error) },
      { status: 500 }
    )
  }
}
```

Configurar en `vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/cron-snapshot",
      "schedule": "0 2 1 * *"
    }
  ]
}
```

---

## 🧪 Testing

### 1. Crear Snapshot Manual

```bash
# Desde terminal
cd backend
python snapshot_manager.py

# O vía API
curl -X POST https://black-infra-api-pure.onrender.com/snapshot-mes-anterior
```

### 2. Verificar Snapshot en Supabase

```sql
-- Ver todos los snapshots
SELECT 
    periodo,
    balance_cuentas_total,
    neto_reparto,
    cashback_aprobado,
    cashback_hold,
    fecha_snapshot
FROM historial_saldos
ORDER BY anio DESC, mes DESC;
```

### 3. Probar Frontend

1. Navegar al mes actual → Debe mostrar datos EN VIVO
2. Crear snapshot del mes anterior
3. Navegar al mes anterior → Debe mostrar badge "📸 Snapshot"
4. Verificar que Cashback Stacking siempre muestre valores actuales

---

## 📊 Casos de Uso

### Caso 1: Navegación Normal

```
Usuario en Dashboard:
├─ Selector: Enero 2026 (mes actual)
│  ├─ Neto Total: $7,500 (honorarios + PST en vivo)
│  ├─ Cashback Stacking: $400 (valor actual)
│  └─ Sin badge
│
├─ Cambiar a: Diciembre 2025
│  ├─ Neto Total: $6,200 (snapshot histórico)
│  ├─ Cashback Stacking: $400 (valor actual, no snapshot)
│  ├─ Badge: "📸 Snapshot Histórico"
│  └─ Nota: "Datos preservados del cierre de mes"
│
└─ Cambiar a: Febrero 2026
   ├─ Neto Total: $0 (solo proyecciones)
   ├─ Cashback Stacking: $400 (valor actual)
   ├─ Badge: "🔮 Proyección"
   └─ Nota: "Estimación basada en ingresos proyectados"
```

### Caso 2: Cierre de Mes Automático

```
Día 1 de Febrero 2026, 02:00 AM:
├─ Cron Job ejecuta: POST /snapshot-mes-anterior
├─ Backend toma "foto" de Enero 2026:
│  ├─ Balance cuentas: $4,933.63
│  ├─ Neto reparto: $2,466.82
│  ├─ Cashback aprobado: $176.20
│  └─ Cashback hold: $0.00
├─ Se inserta en `historial_saldos`
└─ ✅ Enero 2026 queda preservado para siempre
```

### Caso 3: Sin Snapshot (Fallback)

```
Usuario navega a Noviembre 2025 (no hay snapshot):
├─ Backend busca: GET /snapshot/11-2025
├─ Respuesta: 404 Not Found
├─ Frontend hace fallback a datos en vivo
├─ Muestra advertencia: "⚠️ No hay snapshot histórico"
└─ Usa valores actuales de configuración
```

---

## 🚨 Consideraciones Importantes

### 1. **Cashback Stacking es Persistente**
- El bloque de Cashback SIEMPRE muestra el valor ACTUAL de la API
- NO se guarda en snapshots (es dinámico)
- Solo cuando PST deposite, el cashback baja y el neto sube

### 2. **Snapshots son Inmutables**
- Una vez creado, un snapshot NO se modifica
- Si necesitas corregir, crea uno nuevo manualmente

### 3. **Primer Mes**
- El primer mes no tendrá snapshot previo (es normal)
- A partir del segundo mes, todo funcionará

### 4. **Sincronización PST vs Snapshots**
- Sincronizar PST: Actualiza valores EN VIVO
- Crear Snapshot: "Congela" el mes anterior
- Son independientes

---

## 📝 Archivos Creados/Modificados

| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `migration_historial_saldos.sql` | ✅ Creado | Migración de BD |
| `backend/snapshot_manager.py` | ✅ Creado | Módulo de snapshots |
| `backend/api_server.py` | ✅ Modificado | Nuevos endpoints |
| `webapp/app/dashboard/page.tsx` | ⏳ Pendiente | Lógica de carga |
| `IMPLEMENTACION_SNAPSHOTS_v106.md` | ✅ Creado | Este documento |

---

## 🚀 Deploy

### 1. Aplicar Migración SQL

```sql
-- Ejecutar en Supabase SQL Editor
-- Copiar todo el contenido de migration_historial_saldos.sql
```

### 2. Deployar Backend

```bash
cd /Users/tobiasgarcia/Desktop/BLACK_INFRA
git add backend/
git commit -m "feat: Sistema de snapshots mensuales v106.0"
git push origin main
```

### 3. Configurar Cron Job

Opción A (Render): Crear Cron Job manual en dashboard  
Opción B (Vercel): Agregar cron en `vercel.json`

### 4. Modificar Frontend

```bash
cd webapp
# Modificar page.tsx según especificaciones
npm run dev  # Probar localmente
npx vercel --prod  # Deploy a producción
```

---

## ✅ Checklist de Implementación

- [x] Crear tabla `historial_saldos`
- [x] Implementar `snapshot_manager.py`
- [x] Agregar endpoints a API
- [ ] Aplicar migración en Supabase
- [ ] Modificar frontend para cargar snapshots
- [ ] Agregar badges de snapshot/proyección
- [ ] Configurar Cron Job automático
- [ ] Testing completo
- [ ] Deploy a producción

---

**Estado Final:** Backend 100% - Frontend Pendiente  
**Versión:** v106.0 (Snapshots Mensuales)  
**Próximo Paso:** Aplicar migración SQL y modificar frontend
