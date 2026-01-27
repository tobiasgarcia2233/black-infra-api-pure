# 🔌 Guía de Configuración - PST.NET Integration

**Fecha:** 21/01/2026  
**Estado:** Pendiente de credenciales

---

## 📋 Checklist de Configuración

### Paso 1: Información Básica ✅

Antes de configurar la integración, necesito que me proporciones la siguiente información sobre PST.NET:

- [ ] **Nombre completo de la plataforma**
  - ¿Es "PST.NET"? ¿O tiene otro nombre?
  - ¿Empresa argentina de procesamiento de pagos?

- [ ] **URL del sitio web**
  - Para verificar documentación oficial
  - Ejemplo: `https://pst.net` o `https://www.pst.net.ar`

- [ ] **Tipo de servicio**
  - [ ] Pasarela de pago (como MercadoPago, Stripe)
  - [ ] Sistema de facturación electrónica (como Afip, Nubefact)
  - [ ] ERP/CRM (como Odoo, Salesforce)
  - [ ] Otro: _______________

---

### Paso 2: Acceso a la API

#### Opción A: Ya tienes credenciales
Si ya tienes acceso a la API de PST.NET:

1. **Busca en tu panel de PST.NET:**
   - Configuración → API
   - Integraciones → Desarrolladores
   - Settings → API Keys
   - (O similar)

2. **Copia los siguientes datos:**
   ```
   API URL: _______________________________
   API Key: _______________________________
   Secret:  _______________________________
   ```

3. **Agrégalos a tu archivo `.env`:**
   ```env
   PST_NET_API_URL=https://api.pst.net/v1
   PST_NET_API_KEY=tu_api_key_aqui
   PST_NET_SECRET=tu_secret_aqui
   ```

#### Opción B: Necesitas crear credenciales
Si aún no tienes credenciales:

1. **Inicia sesión en PST.NET**
2. **Busca sección de API/Integraciones**
3. **Crea un nuevo API Key/Token**
4. **Guarda las credenciales de forma segura**

---

### Paso 3: Documentación de la API

#### Información Necesaria:

1. **Endpoints de Pagos/Transacciones**
   - ¿Cómo obtener lista de pagos?
   - Ejemplo común: `GET /api/v1/payments`

2. **Parámetros de Filtrado**
   - ¿Cómo filtrar por fecha?
   - ¿Cómo filtrar por estado (completado, pendiente)?
   - ¿Cómo limitar resultados?

3. **Autenticación**
   - ¿Bearer Token en header?
   - ¿API Key como parámetro?
   - ¿Basic Auth?

4. **Estructura de Respuesta**
   - Ejemplo de JSON que devuelve la API
   - Campos importantes: `id`, `monto`, `cliente`, `fecha`, etc.

#### Ejemplo de Documentación Ideal:

```markdown
# PST.NET API Documentation

## Autenticación
Bearer Token en header Authorization:
Authorization: Bearer YOUR_API_KEY

## Endpoints

### GET /api/v1/payments
Obtiene lista de pagos

Parámetros:
- status: completado|pendiente|cancelado
- from_date: YYYY-MM-DD
- to_date: YYYY-MM-DD
- limit: número (default: 50, max: 100)

Respuesta:
{
  "data": [
    {
      "id": "pay_123abc",
      "amount": 1500.00,
      "currency": "USD",
      "client_id": "cli_456def",
      "client_name": "Cliente Ejemplo",
      "status": "completado",
      "date": "2026-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1
}
```

---

### Paso 4: Testing

Una vez que tengas las credenciales configuradas:

#### Test 1: Verificar Conexión
```bash
cd backend
python pst_net_integration.py
```

**Resultado esperado:**
```
🧪 TEST - PST.NET Integration

✅ Configuración de PST.NET válida
📡 Probando conexión con PST.NET...
✅ Conexión con PST.NET exitosa
📥 Obteniendo pagos pendientes...
✅ Se encontraron X pagos
```

#### Test 2: Sincronización Manual (desde Python)
```python
from pst_net_integration import sincronizar_pagos_pst_net
from bot_main import supabase

resultados = sincronizar_pagos_pst_net(supabase)
print(f"✅ Sincronizados: {resultados['exitosos']}/{resultados['total']}")
```

#### Test 3: Sincronización desde Telegram
```
/sincronizar
```

---

## 🔧 Ajustes según la API Real

Cuando me proporciones la documentación, necesitaré ajustar el código en `pst_net_integration.py`:

### Áreas a Personalizar:

#### 1. Headers de Autenticación (línea ~50)
```python
def get_pst_net_headers() -> Dict[str, str]:
    # AJUSTAR SEGÚN TIPO DE AUTH
    return {
        'Authorization': f'Bearer {PST_NET_API_KEY}',  # ¿Bearer? ¿API-Key?
        'Content-Type': 'application/json',
    }
```

#### 2. Endpoint de Pagos (línea ~75)
```python
endpoint = f"{PST_NET_API_URL}/pagos"  # ¿/pagos? ¿/payments? ¿/transactions?
params = {
    'estado': 'completado',  # ¿status? ¿state?
    'sincronizado': 'false',  # ¿synced? ¿processed?
}
```

#### 3. Mapeo de Campos (línea ~185)
```python
pago_id = pago.get('id')              # ¿payment_id? ¿transaction_id?
cliente_id = pago.get('cliente_id')   # ¿client_id? ¿customer_id?
monto_usd = pago.get('monto')         # ¿amount? ¿total?
fecha_pago = pago.get('fecha')        # ¿date? ¿created_at?
```

---

## 📞 Información de Contacto con PST.NET

Si no encuentras la documentación:

1. **Soporte de PST.NET**
   - ¿Email de soporte técnico?
   - ¿Chat en vivo?
   - ¿WhatsApp/Telegram de atención?

2. **Preguntas para hacerles:**
   - "¿Tienen documentación de API para desarrolladores?"
   - "¿Cómo puedo obtener un API Key?"
   - "¿Tienen webhooks para notificaciones en tiempo real?"
   - "¿Cuál es el formato de autenticación?"

---

## 🎯 Casos de Uso

### Caso 1: Sincronización Manual Diaria
```bash
# Ejecutar cada mañana desde el bot
/sincronizar
```

### Caso 2: Sincronización Automática con Cron
```bash
# Agregar a crontab (Linux/Mac)
# Ejecuta sincronización cada día a las 9 AM
0 9 * * * cd /path/to/BLACK_INFRA/backend && python3 -c "from pst_net_integration import sincronizar_pagos_pst_net; from bot_main import supabase; sincronizar_pagos_pst_net(supabase)"
```

### Caso 3: Webhook Automático (Recomendado)
Si PST.NET soporta webhooks:

1. **Configurar endpoint en tu servidor**
   ```python
   # webhook_server.py
   from flask import Flask, request
   from pst_net_integration import procesar_webhook_pst_net
   from bot_main import supabase
   
   app = Flask(__name__)
   
   @app.route('/webhook/pst-net', methods=['POST'])
   def webhook():
       payload = request.json
       procesar_webhook_pst_net(payload, supabase)
       return {'status': 'ok'}, 200
   ```

2. **Configurar webhook en PST.NET**
   - URL: `https://tu-servidor.com/webhook/pst-net`
   - Eventos: `payment.completed`

3. **Los pagos se sincronizarán automáticamente**
   - Sin intervención manual
   - En tiempo real

---

## 🚨 Errores Comunes

### Error: "PST_NET_API_KEY no está configurada"
**Solución:**
1. Verifica que el archivo `.env` exista en la raíz del proyecto
2. Verifica que la variable esté correctamente escrita
3. Reinicia el bot después de modificar `.env`

### Error: "401 Unauthorized" o "403 Forbidden"
**Solución:**
1. Verifica que el API Key sea correcto
2. Verifica que el formato de autenticación sea el correcto
3. Verifica que el API Key no haya expirado

### Error: "404 Not Found"
**Solución:**
1. Verifica que la URL del endpoint sea correcta
2. Verifica que el API_URL base sea correcto

### Error: "KeyError: 'monto'" o similar
**Solución:**
1. El mapeo de campos es incorrecto
2. Necesito ver un ejemplo de respuesta de la API
3. Ajustaré el código para mapear correctamente

---

## 📊 Formato de Respuesta Esperado

Para que la integración funcione, necesito que la API devuelva (al menos):

```json
{
  "id": "pago_123",           // ID único del pago
  "cliente_id": "uuid_456",   // ID del cliente (debe coincidir con Supabase)
  "monto": 1500.00,           // Monto en USD
  "moneda": "USD",            // Moneda (USD, ARS, etc.)
  "fecha": "2026-01-15",      // Fecha del pago
  "estado": "completado"      // Estado (completado, pendiente, etc.)
}
```

Si la estructura es diferente, solo dime cuál es y ajustaré el código.

---

## 🎉 Beneficios Post-Configuración

Una vez configurado PST.NET, tendrás:

- ✅ **Sincronización automática de pagos**
  - Sin registro manual
  - Ahorro de tiempo

- ✅ **Datos siempre actualizados**
  - Resumen financiero correcto
  - Neto calculado en tiempo real

- ✅ **Trazabilidad completa**
  - Cada pago con metadata de origen
  - Auditoría facilitada

- ✅ **Menos errores**
  - Sin duplicación manual
  - Sin olvidos de registro

---

## ✉️ Información a Proporcionar

Para finalizar la integración, envíame:

1. **Screenshot del panel de PST.NET** (donde se ven los pagos)
2. **Documentación de API** (link o PDF)
3. **Credenciales de prueba** (si es posible)
4. **Ejemplo de respuesta JSON** (de un pago real)

Con esto podré:
- ✅ Ajustar el código exacto
- ✅ Hacer testing real
- ✅ Garantizar funcionamiento al 100%

---

**📞 Estoy listo para configurar PST.NET cuando tengas la información.**

---

_Guía creada por el equipo BLACK - 21/01/2026_
