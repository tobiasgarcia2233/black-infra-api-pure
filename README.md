# 🚀 BLACK INFRA - Sistema de Gestión Financiera

Sistema completo de gestión financiera con Bot de Telegram, base de datos normalizada en Supabase y WebApp Dashboard.

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Integración PST.NET](#integración-pstnet)
- [WebApp Dashboard](#webapp-dashboard)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## ✨ Características

### Bot de Telegram
- ✅ Menú interactivo con botones inline
- ✅ Registro de ingresos por cliente
- ✅ Gestión de costos (crear/editar/borrar)
- ✅ Resumen financiero en tiempo real
- ✅ Integración con DolarAPI (cotización actualizada)
- ✅ Cálculo automático de utilidades netas
- ✅ Formateo argentino de números

### Base de Datos (Supabase)
- ✅ Normalizada con UUIDs
- ✅ Tablas: `clientes`, `ingresos`, `costos`, `cotizaciones`
- ✅ Relaciones FK correctas
- ✅ Timestamps automáticos

### Integraciones
- ✅ DolarAPI (cotización dólar blue)
- 🚧 PST.NET (automatización de ingresos) - En desarrollo
- 🚧 WebApp Dashboard - Planificada

---

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.10+**
- **python-telegram-bot** (20.7) - Framework del bot
- **Supabase Client** (2.3.4) - PostgreSQL
- **Requests** - HTTP client
- **python-dotenv** - Manejo de variables de entorno

### Database
- **Supabase** (PostgreSQL managed)
- **UUIDs** como primary keys

### APIs Externas
- **DolarAPI** - Cotización del dólar blue
- **PST.NET** - Procesamiento de pagos (en integración)

### WebApp (Planificada)
- **Next.js 14+** (React + TypeScript)
- **Tailwind CSS** + shadcn/ui
- **Recharts** - Gráficos interactivos
- **Supabase Auth** - Autenticación
- **Vercel** - Deployment

---

## 🏗️ Arquitectura

```
┌─────────────────┐
│  TELEGRAM BOT   │ ← Usuario interactúa
└────────┬────────┘
         │
         │ (Escribe datos)
         ▼
┌─────────────────┐
│    SUPABASE     │ ← Base de datos central
│   (PostgreSQL)  │
└────────┬────────┘
         │
         │ (Lee/Escribe)
         ▼
┌─────────────────┐
│  WEBAPP DASHBOARD│ ← Visualización web
└─────────────────┘

APIs Externas:
- DolarAPI ──→ Bot (cotización)
- PST.NET ──→ Bot (pagos)
```

---

## 📦 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd BLACK_INFRA
```

### 2. Crear entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

---

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con:

```env
# Telegram Bot
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# PST.NET (opcional)
PST_NET_API_URL=https://api.pst.net/v1
PST_NET_API_KEY=your_pst_net_api_key_here
PST_NET_SECRET=your_webhook_secret_here
```

### 2. Configurar Telegram Bot

1. Habla con [@BotFather](https://t.me/BotFather) en Telegram
2. Crea un nuevo bot: `/newbot`
3. Copia el token que te da
4. Pégalo en `TELEGRAM_TOKEN` en tu `.env`

### 3. Configurar Supabase

1. Crea un proyecto en [supabase.com](https://supabase.com)
2. Ve a Settings → API
3. Copia la URL y la `anon key`
4. Pégalas en tu `.env`

### 4. Estructura de Base de Datos

Ejecuta estas queries en el SQL Editor de Supabase:

```sql
-- Tabla de clientes
CREATE TABLE clientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,
    honorario_usd NUMERIC(10, 2),
    activo BOOLEAN DEFAULT true,
    estado TEXT DEFAULT 'activo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de ingresos
CREATE TABLE ingresos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cliente_id UUID REFERENCES clientes(id),
    monto_usd_total NUMERIC(10, 2),
    monto_ars NUMERIC(15, 2),
    fecha_cobro DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de costos
CREATE TABLE costos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,
    monto_usd NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de cotizaciones
CREATE TABLE cotizaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo TEXT DEFAULT 'dolar_blue',
    compra NUMERIC(10, 2),
    venta NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 🚀 Uso

### Iniciar el Bot

```bash
cd backend
python bot_main.py
```

Deberías ver:

```
🤖 INICIANDO BOT DE TELEGRAM - SISTEMA BLACK
✅ Variables de entorno cargadas
✅ Cliente Supabase creado exitosamente
✅ Bot configurado correctamente
📡 Esperando mensajes...
```

### Comandos del Bot

Abre Telegram y busca tu bot. Comandos disponibles:

- `/start` - Menú principal con botones interactivos
- `/resumen` - Estado de resultados de Enero 2026
- `/clientes` - Lista de clientes activos

### Flujos de Trabajo

#### 1. Registrar un Pago
1. Click en "📥 Nuevo Pago"
2. Selecciona el cliente
3. Ingresa el monto en USD
4. ✅ El bot calcula automáticamente el ARS con cotización actual

#### 2. Registrar un Costo
1. Click en "💸 Nuevo Costo"
2. Escribe el concepto (ej: "Servidor")
3. Ingresa el monto en USD
4. ✅ Guardado en Supabase

#### 3. Gestionar Costos
1. Click en "⚙️ Gestionar Costos"
2. Ver últimos 5 costos
3. Opciones: ✏️ Editar o 🗑️ Borrar

---

## 🔌 Integración PST.NET

### ¿Qué es?

PST.NET es una plataforma de procesamiento de pagos. Esta integración permite:

- ✅ Sincronizar pagos automáticamente
- ✅ Evitar registro manual
- ✅ Mapeo automático cliente → pago
- ✅ Webhooks en tiempo real (opcional)

### Configuración

**⚠️ IMPORTANTE: Necesitas proporcionarme los siguientes datos:**

1. **URL de la API de PST.NET** (ej: `https://api.pst.net/v1`)
2. **Tipo de autenticación** (API Key, OAuth, JWT, etc.)
3. **Credenciales** (API Key, Secret, etc.)
4. **Documentación** (endpoints disponibles)

### Uso Manual

```python
# En el bot o en un script separado
from pst_net_integration import sincronizar_pagos_pst_net
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
resultados = sincronizar_pagos_pst_net(supabase)

print(f"Sincronizados: {resultados['exitosos']}/{resultados['total']}")
```

### Uso Automático (Webhook)

Si PST.NET soporta webhooks:

1. Configura el webhook en PST.NET apuntando a tu servidor
2. Usa el handler `procesar_webhook_pst_net()` en tu endpoint
3. Los pagos se registrarán automáticamente al ocurrir

**Ejemplo con Flask:**

```python
from flask import Flask, request
from pst_net_integration import procesar_webhook_pst_net

app = Flask(__name__)

@app.route('/webhook/pst-net', methods=['POST'])
def webhook_pst_net():
    payload = request.json
    signature = request.headers.get('X-PST-Signature')
    
    if validar_webhook_pst_net(payload, signature):
        procesar_webhook_pst_net(payload, supabase)
        return {'status': 'ok'}, 200
    
    return {'error': 'invalid signature'}, 401
```

---

## 🌐 WebApp Dashboard

### Estado: 📋 Planificada

Ver detalles completos en: [`WEBAPP_PLAN.md`](./WEBAPP_PLAN.md)

### Stack Propuesto
- Next.js 14 (React + TypeScript)
- Tailwind CSS + shadcn/ui
- Recharts (gráficos)
- Supabase Auth

### Características
- 📊 Dashboard con KPIs en tiempo real
- 📈 Gráficos de evolución mensual
- 🥧 Distribución de ingresos por cliente
- 📜 Tablas de movimientos con filtros
- 📱 Responsive (mobile-first)
- 🔐 Autenticación segura

### Inicio Rápido (próximamente)

```bash
# Crear proyecto Next.js
npx create-next-app@latest black-webapp --typescript --tailwind --app

# Instalar dependencias
cd black-webapp
npm install @supabase/supabase-js recharts shadcn-ui

# Configurar variables de entorno
echo "NEXT_PUBLIC_SUPABASE_URL=your_url" > .env.local
echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key" >> .env.local

# Iniciar desarrollo
npm run dev
```

---

## 📁 Estructura del Proyecto

```
BLACK_INFRA/
├── backend/
│   ├── bot_main.py                 # Bot principal de Telegram
│   ├── pst_net_integration.py      # Integración con PST.NET
│   ├── requirements.txt            # Dependencias Python
│   └── [otros módulos]
├── webapp/                         # (próximamente)
│   └── [aplicación Next.js]
├── .env                           # Variables de entorno (NO subir a Git)
├── README.md                      # Este archivo
├── WEBAPP_PLAN.md                 # Plan detallado de la webapp
├── master_migration.py            # Script de migración inicial
└── *.csv                          # Backups de datos (legacy)
```

---

## 🧪 Testing

### Test de conexión Supabase

```python
from bot_main import verificar_conexion_supabase

if verificar_conexion_supabase():
    print("✅ Supabase conectado")
```

### Test de DolarAPI

```python
from bot_main import get_dolar_blue

cotizacion = get_dolar_blue()
print(f"Dólar Blue: ${cotizacion['venta']}")
```

### Test de PST.NET

```bash
cd backend
python pst_net_integration.py
```

---

## 🔐 Seguridad

### Variables Sensibles
- ✅ Nunca subas el archivo `.env` a Git
- ✅ Usa `.gitignore` para proteger credenciales
- ✅ Usa variables de entorno en producción

### Supabase
- ✅ Usa Row Level Security (RLS) en producción
- ✅ Usa `anon key` para operaciones públicas
- ✅ Usa `service_role key` solo en backend seguro

### Bot de Telegram
- ✅ Valida usuarios autorizados (próximamente)
- ✅ Implementa rate limiting
- ✅ Log de operaciones críticas

---

## 📊 Próximas Funcionalidades

### Corto Plazo
- [ ] Integración completa con PST.NET
- [ ] Comando `/sincronizar` en el bot
- [ ] WebApp MVP (Dashboard básico)

### Mediano Plazo
- [ ] Autenticación de usuarios en el bot
- [ ] Reportes en PDF
- [ ] Gráficos avanzados en webapp
- [ ] Notificaciones automáticas

### Largo Plazo
- [ ] App móvil nativa
- [ ] Predicciones con IA
- [ ] Multi-tenant (múltiples empresas)
- [ ] API REST pública

---

## 🐛 Troubleshooting

### Error: "TELEGRAM_TOKEN no está definido"
- Verifica que el archivo `.env` esté en la raíz del proyecto
- Asegúrate de que no haya espacios ni comillas extras

### Error: "Respuesta inválida de Supabase"
- Verifica que las tablas existan en Supabase
- Revisa que la `SUPABASE_KEY` sea correcta
- Verifica la estructura de datos (UUIDs, tipos)

### Error: "Timeout al consultar DolarAPI"
- Verifica tu conexión a internet
- DolarAPI podría estar caído (usa fallback de 1500)

### El bot no responde
- Verifica que el token sea correcto
- Asegúrate de que el bot esté corriendo (`python bot_main.py`)
- Revisa los logs en la consola

---

## 📞 Soporte

Para dudas o problemas:

1. Revisa este README completo
2. Consulta `WEBAPP_PLAN.md` para la webapp
3. Revisa los logs en la consola
4. Verifica las variables de entorno

---

## 📝 Changelog

### v1.0.0 (21/01/2026)
- ✅ Bot de Telegram operativo
- ✅ Integración con Supabase
- ✅ DolarAPI funcionando
- ✅ Gestión de costos (CRUD completo)
- ✅ Resumen financiero
- 🚧 PST.NET integration (en desarrollo)
- 📋 WebApp planificada

---

## 📄 Licencia

Proyecto privado - Todos los derechos reservados © 2026

---

**Desarrollado con ❤️ por el equipo BLACK**  
_Sistema de Gestión Financiera - Versión 1.0.0_
