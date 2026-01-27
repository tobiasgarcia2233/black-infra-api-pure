# BLACK Infrastructure API

API simple para sincronización con PST.NET y gestión de balances USDT.

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copiar `.env.example` a `.env` y completar:

```bash
PST_API_KEY=tu_token_jwt
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_service_role_key
PORT=8000
```

### 3. Ejecutar

```bash
python main.py
```

El servidor estará en: http://localhost:8000

## 📡 Endpoints

### `GET /` - Health Check
Verifica que el servidor esté funcionando.

### `GET /ip` - Obtener IP Pública
Retorna la IP pública del servidor para configurar lista blanca de PST.NET.

**Response:**
```json
{
  "ip": "123.45.67.89",
  "whitelist_format": "123.45.67.89/32",
  "message": "Agregar esta IP a la lista blanca de PST.NET: 123.45.67.89/32"
}
```

### `GET /sync-pst` - Sincronizar PST.NET
Obtiene el balance USDT desde PST.NET, aplica regla del 50% y guarda en Supabase.

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
  "fecha": "2026-01-23T15:30:00",
  "endpoint_usado": "https://api.pst.net/api/v1/balances/"
}
```

## 📦 Deploy en Render

### 1. Crear Web Service

1. Ir a [https://render.com](https://render.com)
2. Crear nuevo **Web Service**
3. Conectar repositorio

### 2. Configuración

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python main.py
```

**Environment Variables:**
```
PST_API_KEY=<tu_token_jwt>
SUPABASE_URL=<tu_url_supabase>
SUPABASE_KEY=<tu_service_role_key>
PORT=10000
```

### 3. Obtener IP

Una vez desplegado:
```bash
curl https://tu-servicio.onrender.com/ip
```

### 4. Configurar Lista Blanca

Agregar la IP obtenida a la lista blanca de PST.NET.

## 🧪 Testing

```bash
# Test local
curl http://localhost:8000/ip
curl http://localhost:8000/sync-pst

# Test producción
curl https://tu-servicio.onrender.com/ip
curl https://tu-servicio.onrender.com/sync-pst
```

## 📊 Arquitectura

```
iPhone → Vercel (Proxy) → Render (Esta API) → PST.NET
                                  ↓
                              Supabase
```

**Ventaja**: Render tiene IP fija que PST.NET puede poner en lista blanca.

## 🔧 Estructura del Proyecto

```
.
├── main.py              # Servidor FastAPI
├── requirements.txt     # Dependencias Python
├── runtime.txt          # Versión de Python para Render
├── .env.example         # Ejemplo de variables de entorno
└── README.md           # Este archivo
```

## 📝 Notas

- Python 3.10.12 (especificado en `runtime.txt`)
- FastAPI con soporte async
- Estrategia de fallback con 4 URLs de PST.NET
- Logs detallados en consola
- CORS habilitado para Vercel

## 🐛 Troubleshooting

**Error: "PST_API_KEY no configurada"**
- Verificar variables de entorno en Render

**Error: "Token inválido"**
- Obtener nuevo token JWT desde PST.NET

**Error: "404 - Todas las rutas fallaron"**
- Verificar IP en lista blanca de PST.NET
- Ejecutar: `curl https://tu-servicio.onrender.com/ip`

## 🔗 Referencias

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Render Docs](https://render.com/docs)
- [Supabase Python](https://supabase.com/docs/reference/python)
