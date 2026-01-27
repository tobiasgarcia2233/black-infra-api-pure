# Backend - BLACK INFRASTRUCTURE

Sistema backend en Python con FastAPI para integraciones externas.

## 🏗 Estructura

```
backend/
├── api_server.py              # Servidor FastAPI principal
├── pst_sync_balances.py       # Módulo de sincronización PST.NET
├── bot_instance.py            # Bot de Telegram
├── db_manager.py              # Gestión de Supabase
├── handlers_*.py              # Handlers del bot
├── get_my_ip.py               # Script auxiliar para obtener IP
├── requirements.txt           # Dependencias Python
├── DEPLOY_RENDER.md           # Guía de deploy en Render
└── README.md                  # Este archivo
```

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Crear/actualizar el archivo `.env` en la raíz del proyecto:

```bash
# PST.NET
PST_API_KEY=tu_token_jwt_aqui

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_service_role_key

# Telegram (para el bot)
TELEGRAM_TOKEN=tu_token_de_telegram

# Servidor API
PORT=8000
```

### 3. Ejecutar el Servidor API

```bash
python api_server.py
```

El servidor estará disponible en:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### 4. Ejecutar el Bot de Telegram (Opcional)

```bash
python bot_instance.py
```

## 📡 Endpoints del API

### `GET /` - Health Check
Verifica que el servidor esté funcionando.

**Response:**
```json
{
  "status": "ok",
  "service": "BLACK Infrastructure API",
  "version": "1.0.0"
}
```

### `GET /health` - Health Check Detallado
Verifica el estado del servidor con timestamp.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-23T15:30:00Z"
}
```

### `GET /sync-pst` - Sincronizar PST.NET
Obtiene el balance USDT desde PST.NET y lo guarda en Supabase.

**Response exitoso:**
```json
{
  "success": true,
  "pst": {
    "balance_usdt": 1234.56,
    "cashback": 123.45,
    "total_disponible": 1358.01,
    "neto_reparto": 679.0
  },
  "message": "PST sincronizado: $679.0 USD (50% de $1358.01)",
  "fecha": "2026-01-23T15:30:00Z"
}
```

**Response con error:**
```json
{
  "success": false,
  "error": "Token inválido o expirado",
  "message": "No se pudo sincronizar PST.NET"
}
```

## 🧪 Testing

### Test Local

```bash
# Test del servidor
curl http://localhost:8000/health

# Test de sincronización PST.NET
curl http://localhost:8000/sync-pst
```

### Test del Módulo de Sincronización

```bash
# Ejecutar directamente el módulo
python pst_sync_balances.py
```

### Obtener IP Pública (para lista blanca)

```bash
python get_my_ip.py
```

## 📦 Deploy en Render

Ver guía completa en: [`DEPLOY_RENDER.md`](./DEPLOY_RENDER.md)

**Resumen:**
1. Crear cuenta en [Render](https://render.com)
2. Crear Web Service con Python runtime
3. Configurar variables de entorno
4. Deploy automático
5. Obtener IP y agregar a lista blanca de PST.NET

## 🔧 Configuración de Producción

### Variables de Entorno en Render

```bash
PST_API_KEY=<tu_token_jwt>
SUPABASE_URL=<tu_url_supabase>
SUPABASE_KEY=<tu_service_role_key>
PORT=10000
```

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
python api_server.py
```

## 📊 Logs y Monitoreo

### Ver Logs

```bash
# En desarrollo (local)
python api_server.py

# En producción (Render)
# Dashboard → Tu servicio → Logs
```

### Formato de Logs

```
🔄 API REQUEST: /sync-pst
===================================
🔄 SINCRONIZACIÓN PST.NET - 2026-01-23 15:30:00
===================================
🔑 API Key detectada: eyJhbGci...Wshg
📍 Probando URL: https://api.pst.net/api/v1/balances/
📥 Status: 200
✅ ENDPOINT CORRECTO
💰 Balance USDT: $1234.56
💵 Cashback: $123.45
📊 Total disponible: $1358.01
📊 Neto 50%: $679.0
💾 Guardando en Supabase...
✅ Configuración guardada
✅ Ingreso PST actualizado
✅ Sincronización completada exitosamente
```

## 🐛 Troubleshooting

### Error: "PST_API_KEY no está configurada"

**Solución**: Verificar que el `.env` tenga la variable `PST_API_KEY`

### Error: "Token inválido o expirado"

**Solución**: Obtener un nuevo token JWT desde el dashboard de PST.NET

### Error: "404 - Todas las rutas dieron error"

**Solución**: Agregar la IP del servidor a la lista blanca de PST.NET

### El servidor no responde

**Solución**: 
1. Verificar que el puerto no esté ocupado
2. Verificar que las dependencias estén instaladas
3. Revisar los logs para ver el error específico

## 🔗 Referencias

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Render Docs](https://render.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python)
- Guía de Deploy: [`DEPLOY_RENDER.md`](./DEPLOY_RENDER.md)
- Implementación completa: [`../IMPLEMENTACION_PST_PROXY.md`](../IMPLEMENTACION_PST_PROXY.md)

## 📞 Soporte

Para problemas o dudas, consultar la documentación en:
- `CORE_CONTEXT.md` (raíz del proyecto)
- `IMPLEMENTACION_PST_PROXY.md` (raíz del proyecto)
- `DEPLOY_RENDER.md` (este directorio)
