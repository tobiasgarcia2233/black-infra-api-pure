# REGLAS DE ARQUITECTURA - BLACK INFRASTRUCTURE

> **Establecidas:** 27/01/2026  
> **Razón:** Prevenir duplicación de código como ocurrió en main.py  
> **Autor:** Senior Backend Engineer

---

## 🏗️ PRINCIPIO FUNDAMENTAL: SEPARACIÓN DE RESPONSABILIDADES

Cada módulo tiene **una sola responsabilidad** y **un solo lugar de mantenimiento**.

---

## 📋 REGLAS OBLIGATORIAS

### 1️⃣ LÓGICA DE PST.NET

**✅ PERMITIDO:**
- **backend/pst_sync_balances.py** es el **ÚNICO** archivo que contiene:
  - Conexión a API de PST.NET
  - URLs y endpoints de PST.NET
  - Headers de autenticación
  - Parseo de JSON de respuestas
  - Lógica de sumatoria de balances (USD + USDT)
  - Cálculo de la regla del 50%
  - Búsqueda recursiva de datos
  - Extracción de cashback
  - Guardado en Supabase

**❌ PROHIBIDO:**
- main.py **NO puede** contener:
  - URLs hardcodeadas de PST.NET
  - Lógica de cálculo matemático (50%, sumas, etc.)
  - Parseo de JSON de PST.NET
  - Búsqueda de campos en respuestas
  - Llamadas directas a `requests.get()` o `httpx.get()` a PST.NET
  - Lógica de extracción de balances

**✅ ÚNICO CÓDIGO PERMITIDO EN main.py:**
```python
from pst_sync_balances import sincronizar_balance_pst

@app.post('/sync-pst')
async def sync_pst():
    print('🚀 Prueba de Vida [VERSION]')
    
    try:
        resultado = sincronizar_balance_pst()
        
        if not resultado.get('success'):
            raise HTTPException(status_code=500, detail=resultado.get('error'))
        
        return JSONResponse(content=resultado, status_code=200)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 2️⃣ PRINCIPIO DRY (Don't Repeat Yourself)

**ANTES DE CADA COMMIT:**
- [ ] Verificar que NO existan funciones duplicadas
- [ ] Verificar que NO exista lógica hardcoded fuera de módulos específicos
- [ ] Verificar que main.py solo sea un **orquestador** (importa y llama)
- [ ] Verificar que cada módulo tenga una sola responsabilidad

**CHECKLIST PRE-COMMIT:**
```bash
# 1. Buscar URLs duplicadas
grep -r "api.pst.net" --include="*.py" .

# 2. Buscar lógica de cálculo duplicada
grep -r "/ 2\|* 0.5" --include="*.py" .

# 3. Buscar parseo de JSON duplicado
grep -r "\.json()\|json.loads" --include="*.py" main.py
```

**Si encuentra duplicación → REFACTORIZAR antes de commit**

---

### 3️⃣ ESTRUCTURA DE MÓDULOS

```
BLACK_INFRA/
├── main.py                          # ORQUESTADOR (solo imports + llamadas)
│   ├── Define rutas FastAPI
│   ├── Maneja CORS
│   └── Llama a módulos específicos
│
├── backend/
│   ├── pst_sync_balances.py        # LÓGICA PST.NET (autoridad única)
│   │   ├── Conexión API PST.NET
│   │   ├── Autenticación multi-header
│   │   ├── Parseo de respuestas
│   │   ├── Sumatoria USD + USDT + Cashback
│   │   └── Guardado en Supabase
│   │
│   ├── db_manager.py               # LÓGICA DATABASE (si existe)
│   ├── handlers_*.py               # HANDLERS ESPECÍFICOS (si existen)
│   └── utils.py                    # UTILIDADES COMPARTIDAS
│
└── webapp/                          # FRONTEND (separado)
```

---

### 4️⃣ REGLA DE ORO: UN SOLO PUNTO DE VERDAD

**Single Source of Truth (SSOT):**

| Concepto | Ubicación Única | Prohibido En |
|----------|-----------------|--------------|
| URLs de PST.NET | `backend/pst_sync_balances.py` | main.py, otros archivos |
| Cálculo 50% | `backend/pst_sync_balances.py` | main.py, frontend |
| Parseo JSON PST | `backend/pst_sync_balances.py` | main.py |
| Sumatoria USD/USDT | `backend/pst_sync_balances.py` | main.py |
| Headers Auth | `backend/pst_sync_balances.py` | main.py |

---

### 5️⃣ ANTI-PATRONES A EVITAR

**❌ MAL - Código duplicado en main.py:**
```python
# ESTO ESTÁ PROHIBIDO
@app.post('/sync-pst')
async def sync_pst():
    # ❌ URL hardcodeada
    url = "https://api.pst.net/integration/members/accounts"
    
    # ❌ Headers duplicados
    headers = {'Authorization': f'Bearer {token}'}
    
    # ❌ Parseo de JSON
    data = response.json()
    
    # ❌ Lógica de cálculo
    neto = (balance + cashback) / 2
```

**✅ BIEN - Solo orquestación:**
```python
# ESTO ES CORRECTO
@app.post('/sync-pst')
async def sync_pst():
    print('🚀 Prueba de Vida V33')
    resultado = sincronizar_balance_pst()
    return JSONResponse(content=resultado, status_code=200)
```

---

### 6️⃣ PROCESO DE REFACTORIZACIÓN

**Si encuentras código duplicado:**

1. **Identificar:** ¿Qué está duplicado?
2. **Localizar:** ¿Dónde está el código maestro?
3. **Eliminar:** Borrar duplicados de main.py
4. **Importar:** Agregar import del módulo correcto
5. **Llamar:** Reemplazar lógica con llamada a función
6. **Verificar:** Ejecutar tests, verificar sintaxis
7. **Commit:** Con mensaje claro de refactorización

**Ejemplo de commit:**
```
refactor: eliminar lógica duplicada de PST.NET en main.py

- Eliminadas 300+ líneas de lógica duplicada
- main.py ahora solo importa sincronizar_balance_pst()
- Single Source of Truth: backend/pst_sync_balances.py
- Fixes issue de mantenimiento y bugs por inconsistencia
```

---

### 7️⃣ VERIFICACIÓN AUTOMÁTICA

**Script de verificación (ejecutar antes de commit):**
```bash
#!/bin/bash
# verify_architecture.sh

echo "🔍 Verificando reglas de arquitectura..."

# Buscar URLs de PST.NET fuera de backend/
URLS=$(grep -r "api.pst.net" --include="*.py" --exclude-dir=backend . 2>/dev/null)
if [ -n "$URLS" ]; then
    echo "❌ URLs de PST.NET encontradas fuera de backend/:"
    echo "$URLS"
    exit 1
fi

# Buscar lógica de cálculo en main.py
CALC=$(grep -E "/ 2|balance.*\+.*cashback" main.py 2>/dev/null)
if [ -n "$CALC" ]; then
    echo "❌ Lógica de cálculo encontrada en main.py"
    exit 1
fi

# Buscar parseo de JSON de PST en main.py
JSON=$(grep -E "\.json\(\)|json\.loads.*pst|response\.json\(\)" main.py 2>/dev/null | grep -v "JSONResponse")
if [ -n "$JSON" ]; then
    echo "❌ Parseo de JSON encontrado en main.py"
    exit 1
fi

echo "✅ Arquitectura verificada correctamente"
exit 0
```

---

## 🎯 BENEFICIOS DE ESTAS REGLAS

✅ **Mantenibilidad:** Un solo lugar para modificar lógica de PST.NET  
✅ **Debugging:** Bugs solo en un archivo, no dispersos  
✅ **Testing:** Fácil hacer tests unitarios de módulos aislados  
✅ **Escalabilidad:** Agregar features sin afectar main.py  
✅ **Claridad:** Separación clara de responsabilidades  
✅ **Onboarding:** Nuevos devs encuentran código rápido  

---

## 📚 REFERENCIAS

- **Clean Code** - Robert C. Martin (Uncle Bob)
- **SOLID Principles** - Single Responsibility Principle
- **DRY Principle** - Don't Repeat Yourself
- **Separation of Concerns** - Architectural Pattern

---

## 🚨 INCIDENTE QUE ORIGINÓ ESTAS REGLAS

**Fecha:** 27/01/2026  
**Problema:** main.py tenía 300+ líneas de lógica PST.NET duplicada  
**Impacto:** 
- Render ejecutaba código legacy
- Mejoras v2.1.0 no se aplicaban
- Debugging confuso (¿dónde está el bug?)
- Mantenimiento doble (actualizar en 2 lugares)

**Solución aplicada:**
- Eliminadas 301 líneas de main.py
- Agregado import de pst_sync_balances
- Establecidas estas reglas arquitectónicas

---

## ✅ CUMPLIMIENTO OBLIGATORIO

**Estas reglas son OBLIGATORIAS para:**
- Todos los commits
- Todas las features nuevas
- Todos los bugfixes
- Todas las refactorizaciones

**En caso de duda:**
1. Consultar este documento
2. Preguntarse: "¿Esto es responsabilidad de main.py?"
3. Si la respuesta es NO → mover a módulo específico

---

**Última actualización:** 27/01/2026  
**Versión del documento:** 1.0.0
