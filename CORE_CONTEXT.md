# BLACK INFRA - CORE CONTEXT (v2.0)

## 📌 Estado del Sistema
- **Bot de Telegram (Backend):** Operativo. Gestión de clientes y reportes financieros.
- **WebApp (Frontend):** PWA en Next.js desplegada en Vercel. Dashboard y Panel CRM.
- **Base de Datos:** Supabase (PostgreSQL) con lógica de vistas para cálculos automáticos.

## 💰 Reglas de Negocio y Contabilidad
- **Dólar Base:** Tabla `configuracion` -> `dolar_conversion`.
- **Costos Fijos (ARS a USD):** Juana, Yazmin, Maxi. Cargados en ARS, convertidos dinámicamente.
- **Costo Variable (Agustín):** `COUNT(clientes WHERE estado='Activo' AND comisiona_agustin=true) * 55 USD`.
- **Ingresos Proyectados (MRR):** `SUM(fee_mensual WHERE estado='Activo')`.
- **Neto Real:** `Ingresos Percibidos - Gastos Totales`.

## 👥 Gestión de Clientes (CRM)
- **Atributos:** `estado` (Activo, Inactivo, Pausado, Prospecto), `fee_mensual` (USD), `comisiona_agustin` (Boolean).
- **Interfaces de Control:**
  - **Telegram:** Comando `/clientes` (Edición rápida de estados y fees).
  - **WebApp:** Ruta `/dashboard/clientes` (Gestión visual y masiva).

## 🛠 Stack Técnico
- **Frontend:** Next.js 14 (App Router), Tailwind CSS, Lucide React.
- **Backend:** Python 3.x, Telebot, Supabase-py.
- **Hosting:** Vercel (Web) + Local/VPS (Bot).

## 📅 Último Hito
- **27/01/2026:** Implementación de Time Machine (Selector de Periodos) y Sistema de Vencimientos + Panel de Tesorería Semanal.

## Interfaz y Experiencia (v2.4)
- **UI:** Mobile-First con sistema de Cards táctiles en `/dashboard/clientes`.
- **Componentes:** Badges de estado por color y Switches estilo iOS para comisiones.
- **Despliegue:** Siempre ejecutar `npx vercel --prod` dentro de la carpeta `/webapp`.

## Gestión de Clientes y CRM (v2.5)
- **Altas:** Botón "+ Nuevo Cliente" implementado en la Web App con formulario modal.
- **Flujo:** Las altas desde la Web impactan inmediatamente en el cálculo de costos de Agustín y el MRR proyectado.

## Automatización y APIs (v2.6)
- **Dólar Blue:** Sincronización automática desde DolarAPI.com vía API serverless.
- **Cron Job:** Actualización diaria a las 9 AM UTC (6 AM Argentina) en Vercel.
- **Manual:** Botón "🔄 Sincronizar Dólar Ahora" en página de Configuración.
- **Recálculo:** Al actualizar el dólar, todos los costos fijos en USD se recalculan automáticamente.

## Integración PST.NET (v3.1)
- **API:** Conexión a PST.NET vía `/api/sync-pst` para obtener balance USDT y cashback.
- **Regla del 50%:** (Balance + Cashback) ÷ 2 = Neto disponible para reparto.
- **Almacenamiento:** Guardado en tabla `configuracion` (clave: `pst_balance_neto`) y en `ingresos` (concepto: `PST_REPARTO`).
- **Cron Job:** Sincronización automática diaria a las 10 AM UTC (7 AM Argentina).
- **Manual:** Botón "💰 Sincronizar PST.NET" en Configuración para actualización on-demand.

## Automatización de Divisas (v3.0 - INTELLIGENT)
- **Engine:** API Route Serverless en Vercel (`/api/update-dolar`).
- **Lógica de Cascada:** La actualización del dólar dispara automáticamente el recálculo de `monto_usd` en toda la tabla de `costos`.
- **Seguridad:** Uso de `SUPABASE_SERVICE_ROLE_KEY` para operaciones de backend seguras.
- **Trigger:** Manual vía UI y Automático vía Cron Job.

# BLACK INFRA - CORE CONTEXT (v3.3)

## 📌 Estado del Sistema
- **Dashboard:** Operativo en Vercel con UI Mobile-First (Cards táctiles).
- **CRM:** Altas y bajas de clientes gestionadas desde Web y Telegram.
- **Dólar:** Actualización automática (Cascada de costos fijos) vía API Route.

## 💰 Reglas de Automatización
- **Dólar Blue:** Sincronizado diariamente a las 09:00 UTC.
- **PST.NET API:** Sincronización a las 10:00 UTC. 
- **Fórmula Societaria:** `(Saldo_USDT + Cashback) * 0.5`. 
- **Persistencia:** Un único registro `PST_REPARTO` por mes calendario para evitar duplicados.

## 👥 Gestión de Clientes (CRM)
- **Costo Agustín:** $55 USD x Cliente (Estado: Activo, Comisiona: True).
- **Ingresos Proyectados:** Fees de Clientes Activos + Balance Neto PST.NET.

## 🛠 Stack y Hosting
- **Frontend:** Next.js 14 (Vercel).
- **Backend/Bot:** Python (Render - Background Service).
- **Base de Datos:** Supabase (PostgreSQL).

## Notas Técnicas de Integración (v3.7 - Arquitectura Proxy)
- **Arquitectura PST.NET:** Vercel → Render (Proxy) → PST.NET API
- **Backend en Render:** FastAPI server (`api_server.py`) con endpoint `/sync-pst`
- **Módulo de sincronización:** `pst_sync_balances.py` con estrategia de fallback de 4 URLs
- **IP Fija:** Render proporciona IP estática para lista blanca de PST.NET
- **Proxy Vercel:** `/api/sync-pst/route.ts` redirige a `NEXT_PUBLIC_BACKEND_URL`
- **Deploy:** Backend en Render con auto-deploy, Free tier disponible
- **Variables críticas:** `PST_API_KEY`, `SUPABASE_KEY`, `NEXT_PUBLIC_BACKEND_URL`

## Actualización de Lógica Financiera (v4.8)
- **Feature:** Integración de `approved_cashback` vía `/subscriptions/info`.
- **Backend:** FastAPI v1.1.0 en Render (Pure API).
- **Cálculo:** El reparto del 50% ahora incluye el cashback recuperado.
- **Acción:** Sincronizar IP de Render en panel PST para habilitar nuevos endpoints.

## INFRAESTRUCTURA ACTIVA (v6.5)
- **Render Status:** LIVE con método de ruta absoluta de Python.
- **Error actual:** 404 en endpoints de PST.NET.
- **Acción inmediata:** Sincronizar IP de salida de Render en Whitelist de PST.NET.
- **Próximo paso:** Testear endpoints sin barra diagonal de cierre.

# BLACK INFRA - CORE CONTEXT (v15.0)

## 🏗️ Nueva Arquitectura de Integración (Direct Connect)
- **Paradigma:** Se eliminó la capa de "Proxy" de Vercel. El Frontend (PWA/iPhone) ahora realiza un `fetch()` directo al Backend de Render.
- **Hosting Backend:** Render (Web Service) operando con **FastAPI**.
- **Seguridad CORS:** El Backend en Render tiene una política estricta que solo permite peticiones desde `https://black-infra-webapp-pure.vercel.app`.
- **Despliegue Independiente:** - **Frontend:** Repositorio `black-infra-webapp-pure` (Vercel).
  - **Backend:** Repositorio `black-infra-api-pure` (Render).

## 🔗 Protocolo PST.NET (Actualizado 27/01/2026)
- **Endpoint Oficial v2:** `https://api.pst.net/integration/members/accounts` 
  - *Módulo Integration:* Mayor precisión y datos completos de cuentas.
  - *Filtrado:* Busca automáticamente la cuenta tipo 'Master' con balance USDT.
  - *Fallback:* `/account/get-all-accounts` (legacy v1) si el nuevo endpoint falla.
- **Autenticación:** Header `Authorization: Bearer [JWT]`.
- **IP de Salida Crítica:** `74.220.49.249` (Confirmada vía `/ip`). Debe estar en la Whitelist de PST.NET.
- **Lógica de Extracción:** 
  1. Busca cuenta con `type='Master'` y `currency='USDT'`
  2. Si no existe, selecciona la cuenta USDT con mayor balance
  3. Extrae `balance`, `cashback_balance` y aplica regla del 50%

## 💰 Lógica Financiera Actualizada
- **Fórmula Societaria:** `(Master_Balance_USDT + Cashback) * 0.5`.
- **Sincronización:** El botón "💰 Sincronizar PST.NET" en el Dashboard gatilla el proceso en Render, que consulta PST.NET y persiste el resultado en la tabla `configuracion` y `ingresos` de Supabase.

## 🛠️ Variables de Entorno (Environment)
- **Vercel:** `NEXT_PUBLIC_BACKEND_URL` apuntando a la URL de Render.
- **Render:** `PST_API_KEY` (JWT), `SUPABASE_URL`, `SUPABASE_KEY`.

## 📅 Log de Debugging (26/01/2026)
- Identificación de ruta correcta mediante pruebas de penetración manuales (`curl`) desde la shell de Render. 
- Transición de errores 404 (Path inexistente) a 401 (Problema de permisos), confirmando que el servidor de PST.NET ya reconoce las peticiones del backend de Black Infra.

## 🚨 Guía de Recuperación (Quick Fixes)

### 1. ¿El botón de PST.NET da error? (Check de IP)
Si el botón deja de funcionar, lo primero es verificar si Render cambió la IP de salida (pasa rara vez, pero pasa).
- **Paso A:** Entrá a `https://black-infra-api-pure.onrender.com/ip`.
- **Paso B:** Si la IP no es `74.220.49.249`, copiala.
- **Paso C:** Andá al panel de PST.NET -> API -> Whitelist y reemplazá la IP vieja por la nueva.

### 2. ¿Cómo probar si el backend está vivo?
Si tenés dudas de si el servidor de Render se "durmió":
- Entrá a `https://black-infra-api-pure.onrender.com/health`.
- Deberías ver: `{"status": "online"}`.

### 3. El comando "Bomba" (Test Manual)
Si querés saber exactamente qué error devuelve PST sin usar la WebApp, tirá esto en la **Shell de Render**:
```bash
# Endpoint nuevo (oficial v2 - Integration)
curl -v -H "Authorization: Bearer TU_TOKEN_AQUÍ" https://api.pst.net/integration/members/accounts

# Endpoint legacy (fallback v1)
curl -v -H "Authorization: Bearer TU_TOKEN_AQUÍ" https://api.pst.net/account/get-all-accounts
```

### 4. Actualizar el Token
Si renovás la API Key en PST.NET:
1. Andá al Dashboard de **Render** -> **Environment**.
2. Editá `PST_API_KEY`, pegá la nueva y dale a **Save Changes**.
3. El servidor se reiniciará solo con la llave nueva.

## 🧠 Protocolo de Interacción con IA (Prompt Maestro)
*Para mantener la consistencia técnica, copiar este prompt al iniciar un nuevo chat con Cursor o cualquier IA:*

> "Actúa como un Senior Backend Developer. Lee el archivo @CORE_CONTEXT.md. 
> Nuestra arquitectura es VERCEL (Frontend) -> RENDER (Backend) -> PST.NET (API).
> REGLA DE ORO: No uses el prefijo '/api/v1' para PST.NET; usa siempre la ruta absoluta 
> '/account/get-all-accounts', ya que las demás devuelven 404. 
> El backend corre en FastAPI (Render). No sugieras cambios de arquitectura sin consultar."

# BLACK INFRA - CORE CONTEXT (v16.0 - Time Machine + Vencimientos)

## 🆕 Nuevas Features (27/01/2026)

### 1. Time Machine (Selector de Periodos)
- **Componente:** PeriodoSelector en header del Dashboard
- **Funcionalidad:** Selector dropdown con últimos 12 meses
- **Filtrado:** Queries usan `.eq('periodo', periodoSeleccionado)` en lugar de rangos de fecha
- **Default:** Mes actual (datetime.now())
- **Context:** PeriodoContext global para sincronización
- **Performance:** Queries optimizadas con índices en columna `periodo`

### 2. Sistema de Vencimientos y Próximos Cobros
- **Columna Nueva:** `dia_cobro` (1-31) en tabla `clientes`
- **Cálculo Automático:** Función `calcularProximoPago()` determina próxima fecha
- **Alertas Visuales:**
  - 🔴 Rojo + Pulse: Atrasado o HOY
  - 🟡 Amarillo: ≤ 3 días
  - 🟠 Naranja: ≤ 7 días
  - 🔵 Azul: Normal
- **CRM:** Campo editable + Badge "Próximo pago" en cada cliente
- **Funciones SQL:** `calcular_proximo_vencimiento()`, `v_clientes_vencimientos`

### 3. Panel de Tesorería Semanal
- **Componente:** CobrosPendientesPanel (expandible/colapsable)
- **Total a Cobrar:** Suma de todos los `fee_mensual` con vencimiento en 7 días
- **Lista Detallada:** Nombre, monto, fecha exacta, badge de urgencia
- **Función SQL:** `obtener_detalle_cobros_semana()`
- **Mobile-Optimized:** Touch-friendly, scroll interno, glassmorphism
- **UX:** Click en header para expandir, max 2 taps para ver detalles

## 📊 Estructura de Datos Actualizada

### Tabla `clientes`:
```sql
- dia_cobro INTEGER (1-31, nullable)
- periodo VARCHAR(7) (formato: MM-YYYY)
```

### Tabla `ingresos`:
```sql
- periodo VARCHAR(7) (formato: MM-YYYY)
```

### Tabla `costos`:
```sql
- periodo VARCHAR(7) (formato: MM-YYYY)
```

## 🛠️ Nuevas Funciones SQL

### Vencimientos:
- `calcular_proximo_vencimiento(dia_cobro)` → DATE
- `obtener_cobros_semana()` → TABLE
- `obtener_detalle_cobros_semana()` → TABLE con total_semana
- `get_periodos_disponibles(limite)` → TABLE

### Periodos:
- `get_periodo_actual()` → VARCHAR(7)

## 🎨 Componentes Nuevos

### Frontend (Next.js):
```
/contexts
  └── PeriodoContext.tsx (Estado global)

/components
  ├── PeriodoSelector.tsx (Dropdown)
  └── CobrosPendientesPanel.tsx (Panel de tesorería)

/lib
  └── vencimientos.ts (Helpers de fechas)
```

## 📱 Dashboard Actualizado

### Header:
- Time Machine (Selector de periodo MM-YYYY)

### KPIs:
- Badge con periodo actual en "Neto USD"
- Todos los datos filtrados por periodo seleccionado

### Panel de Tesorería:
- Total a cobrar esta semana en grande
- Lista expandible de clientes con vencimientos
- Badges de urgencia por color
- Footer con tips y contador de urgentes

## 🚀 Deployment Status

### Pendiente:
1. ✅ Migración `migration_periodo.sql` - Aplicada
2. ⏳ Migración `migration_dia_cobro.sql` - Pendiente
3. ⏳ Deploy a Vercel - Pendiente

### Archivos Creados (Total: 9):
- `migration_periodo.sql`
- `migration_dia_cobro.sql`
- `webapp/contexts/PeriodoContext.tsx`
- `webapp/components/PeriodoSelector.tsx`
- `webapp/components/CobrosPendientesPanel.tsx`
- `webapp/lib/vencimientos.ts`
- `FEATURE_VENCIMIENTOS.md`
- `FEATURE_PANEL_TESORERIA.md`
- `RESUMEN_IMPLEMENTACION.md`

### Archivos Modificados (Total: 5):
- `webapp/app/layout.tsx`
- `webapp/app/dashboard/page.tsx`
- `webapp/app/dashboard/clientes/page.tsx`
- `webapp/lib/supabase.ts`
- `CORE_CONTEXT.md`

## 📞 Quick Commands

### Ver vencimientos:
```sql
SELECT * FROM obtener_detalle_cobros_semana();
```

### Ver periodos disponibles:
```sql
SELECT * FROM get_periodos_disponibles();
```

### Actualizar días de cobro masivamente:
```sql
UPDATE clientes SET dia_cobro = 15 WHERE estado = 'Activo' AND dia_cobro IS NULL;
```

## PANEL DE TESORERÍA (v22.0)
- **Feature:** Desglose detallado de cobros semanales.
- **Backend:** Nueva función SQL `obtener_detalle_cobros_semana`.
- **UI:** Lista interactiva con Nombre, Monto individual, Fecha y Total Proyectado Semanal.
- **Estado:** Implementando visualización detallada para toma de decisiones financiera.

## MÓDULO DE COBRANZA ACTIVA (v30.0)
- **Feature:** Botón "Cobro Rápido" en Panel de Tesorería.
- **Lógica:** Inserción automática en `ingresos` vinculada a `periodoSeleccionado`.
- **UX:** Implementación de `react-hot-toast` para feedback visual.
- **Validación:** Prevención de duplicados por cliente/periodo habilitada.
- **Conversión:** Cálculo automático `monto_usd` -> `monto_ars` al momento del cobro.

## PST.NET API v2 - INTEGRATION MODULE (v31.0 - 27/01/2026)
- **Cambio Crítico:** Migración de endpoint legacy a módulo Integration oficial.
- **Endpoint Nuevo:** `GET /integration/members/accounts` (recomendado por soporte PST.NET).
- **Mejora:** Filtrado inteligente de cuenta tipo 'Master' con balance USDT.
- **Lógica de Fallback:** 
  1. Intenta endpoint Integration (v2)
  2. Si falla, usa `/account/get-all-accounts` (v1 legacy)
  3. Busca cuenta Master o la de mayor balance USDT
- **Arquitectura:** Backend FastAPI en Render con IP fija `74.220.49.249`.
- **Archivo Actualizado:** `backend/pst_sync_balances.py`
- **Compatibilidad:** Mantiene soporte retrocompatible con estructura de respuesta anterior.

## REINICIO DE CONTEXTO - MÓDULO PST (v37.0)
- **Objetivo:** Resolver Error 500 en el parseo de 12 cuentas de Integración.
- **Estrategia:** Implementación de "Safe Extraction" y Logs de inspección RAW.
- **Regla:** Ningún error de parseo debe tumbar el proceso (Fail-safe).
- **Backend:** FastAPI en Render / Rama: Main.

## ARQUITECTURA ELITE DESPLEGADA (v53.0)
- **Estado:** Implementación de v3.0.0 (Sumatoria Total) + Arquitectura Limpia.
- **Blindaje:** Creado `ARCHITECTURE_RULES.md` y `verify_architecture.sh`.
- **Lógica de Negocio:** Suma acumulada de USD (id:1), USDT (id:2) y Cashback Global.
- **Resultado:** El sistema refleja el 100% del capital real del Dashboard de PST.NET.
- **Hito:** Eliminación total de deuda técnica y duplicación de código.

## DESGLOSE DE ACTIVOS (v59.0)
- **Lógica:** Separación de balances operativos vs. cashback acumulado.
- **Nuevos Endpoints:** Integración oficial de `/subscriptions/info`.
- **UI/UX:** El backend ahora entrega campos diferenciados para mejorar la visibilidad en el Dashboard.
- **Estado:** Implementando la doble llamada con manejo de errores independiente.

## ESTADO DE VISUALIZACIÓN (v63.0)
- **Cuentas:** ✅ Sincronización exitosa de CID 2 y CID 15 ($4,532.27 total).
- **Reparto:** ✅ Cálculo del 50% ($2,266.13) verificado en el cartel de éxito.
- **Frontend:** 🛠️ Pendiente integrar PST Balance en el 'Neto USD' global del Dashboard.
- **Cashback:** 🔍 En espera de respuesta de soporte por error 401 en /subscriptions/info.

## UX OPTIMIZATION: QUICK SYNC (v83.0)
- **Funcionalidad:** Botón de sincronización directa en la tarjeta de PST.NET (Hero Card).
- **Lógica:** Vinculación del trigger de UI con el script de balance de PST.
- **Feedback:** Implementación de estados de carga (loading) para mejorar la respuesta al usuario.
- **Hito:** Control total del flujo de capital desde la pantalla principal.

## FÓRMULA DE HOLD DEFINIDA (v98.0)
- **Cálculo Hold:** cashback_sum (Summary) - approved_cashback (Info).
- **Lógica de Reparto:** 50% aplicado a todos los niveles de PST.
- **UI:** Inclusión de la tarjeta Ámbar de ancho completo para 'Próximo Ingreso'.
- **Hito:** Eliminación total de discrepancias manuales en el flujo de cashback.

## SISTEMA DE ATRIBUCIÓN TEMPORAL (v103.0)
- **Lógica:** Cobro Adelantado (Caja Hoy / Servicio Mañana).
- **Vistas UI:** Toggle entre Liquidez (Verde) y Performance (Azul).
- **DB:** Migración ejecutada con columna `mes_aplicado` y funciones de cálculo automático.
- **Hito:** Dashboard blindado contra confusiones de flujo de caja vs utilidad neta.

## COMPARTIMENTOS ESTANCOS (v104.0 - 28/01/2026)
- **Concepto:** Cada mes es un "compartimento" aislado e independiente.
- **Selector Único:** Eliminado el toggle Liquidez/Performance. Solo existe el selector de mes.
- **Filtrado:** SIEMPRE por `mes_aplicado` (atribución temporal de servicios).
- **Reglas de Visualización:**
  - **Mes Actual:** Neto = Honorarios del mes + Saldo PST al 50%
  - **Meses Futuros/Pasados:** Neto = SOLO ingresos - gastos del mes (sin PST)
- **PST.NET:** El saldo PST es un valor REAL del momento actual, NO una proyección. Solo suma en el mes en curso.
- **Hold (Próximo Ingreso):** Se muestra como tarjeta informativa en todos los meses, pero NO suma al neto en meses futuros.
- **Aislamiento Total:** No se arrastra saldo PST ni histórico de meses anteriores a meses futuros.

## CÁLCULO CONSERVADOR - NETO TOTAL (v105.0 - 28/01/2026)
- **Principio:** El Neto Total (Hero Card Verde) solo incluye dinero 100% líquido y disponible.
- **Fórmula del Neto:**
  - Honorarios del mes (Ingresos - Gastos) = 100%
  - Saldo PST ID 15 + ID 2 = 50% aplicado
  - **EXCLUIDO:** Cashback (Aprobado o Hold) NO suma al Neto Total
- **Cashback Stacked (Nuevo Bloque):**
  - Componente visual separado del Hero Card
  - **Cashback Aprobado:** 50% de `pst_cashback_aprobado`
  - **Cashback en Hold:** 50% de `pst_cashback_hold`
  - **Propósito:** Tracking de "dinero por caer"
  - **Comportamiento:** Cuando PST deposite en cuentas principales, el balance sube y el cashback baja automáticamente
- **Visibilidad:** El bloque "Cashback Stacked" solo se muestra en el mes actual.
- **Backend (pst_sync_balances.py v3.2.2):**
  - `pst_balance_neto` = 50% SOLO del balance de cuentas (ID 15 + ID 2)
  - `pst_cashback_aprobado` = Cashback aprobado completo (100%) para tracking
  - `pst_cashback_hold` = Cashback en hold completo (100%) para tracking
  - El frontend aplica el 50% al mostrar los valores de cashback

## SISTEMA DE SNAPSHOTS MENSUALES (v106.0 - 28/01/2026)
- **Propósito:** Preservar la historia financiera mes a mes sin que se pisen los datos viejos.
- **Tabla:** `historial_saldos` - Almacena "fotografías" del estado financiero al cierre de cada mes.
- **Snapshot de Cierre:**
  - Se ejecuta el día 1 de cada mes (automático vía Cron Job)
  - Guarda: balance de cuentas, neto reparto, cashback aprobado, cashback hold
  - Los snapshots son INMUTABLES (no se modifican una vez creados)
- **Persistencia del Cashback Stack:**
  - El bloque "Cashback Stacked" SIEMPRE muestra valor ACTUAL de la API
  - NO depende del mes seleccionado (es un valor vivo)
  - Hasta que PST deposite, el valor permanece visible
- **Navegación de Meses:**
  - **Mes Actual:** Datos EN VIVO de PST.NET
  - **Meses Pasados:** Datos del SNAPSHOT histórico (badge "📸 Snapshot")
  - **Meses Futuros:** Solo proyecciones de ingresos (badge "🔮 Proyección")
- **Endpoints API:**
  - `POST /snapshot-mes-anterior` - Crear snapshot del mes anterior
  - `GET /snapshot/{periodo}` - Obtener snapshot específico (MM-YYYY)
  - `GET /snapshots` - Listar todos los snapshots
- **Automatización:** Cron Job que ejecuta snapshot el día 1 de cada mes a las 02:00 AM
- **Fallback:** Si no existe snapshot para un mes, usa datos en vivo con advertencia

