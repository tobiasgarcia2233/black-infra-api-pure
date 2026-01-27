#!/bin/bash
# verify_architecture.sh
# Script de verificación de reglas arquitectónicas
# Ejecutar antes de cada commit para prevenir duplicación de código

echo "🔍 Verificando reglas de arquitectura..."
echo ""

ERRORS=0

# 1. Verificar URLs de PST.NET fuera de backend/
echo "📍 Verificando URLs de PST.NET..."
URLS=$(grep -r "api\.pst\.net" --include="*.py" --exclude-dir=backend . 2>/dev/null | grep -v "ARCHITECTURE_RULES" | grep -v "#")
if [ -n "$URLS" ]; then
    echo "❌ URLs de PST.NET encontradas fuera de backend/:"
    echo "$URLS"
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo "✅ URLs solo en backend/"
fi

# 2. Verificar lógica de cálculo en main.py
echo "🧮 Verificando lógica de cálculo en main.py..."
CALC=$(grep -E "/ 2|balance.*\+.*cashback|\* 0\.5" main.py 2>/dev/null | grep -v "JSONResponse" | grep -v "#")
if [ -n "$CALC" ]; then
    echo "❌ Lógica de cálculo encontrada en main.py:"
    echo "$CALC"
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Sin lógica de cálculo en main.py"
fi

# 3. Verificar parseo de JSON de PST en main.py (excluir endpoint /ip)
echo "📄 Verificando parseo de JSON de PST en main.py..."
JSON=$(grep -E "\.balances|\.currency|balance_usdt|cashback_balance|accounts_array" main.py 2>/dev/null | grep -v "#")
if [ -n "$JSON" ]; then
    echo "❌ Parseo de JSON de PST encontrado en main.py:"
    echo "$JSON"
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Sin parseo de JSON de PST en main.py"
fi

# 4. Verificar que main.py importe pst_sync_balances
echo "📦 Verificando import correcto..."
IMPORT=$(grep -E "from.*pst_sync_balances.*import|import.*pst_sync_balances" main.py 2>/dev/null)
if [ -z "$IMPORT" ]; then
    echo "⚠️  WARNING: main.py no importa pst_sync_balances"
    echo ""
fi

# 5. Verificar longitud de main.py (no debería tener más de 200 líneas)
echo "📏 Verificando tamaño de main.py..."
LINES=$(wc -l < main.py 2>/dev/null | tr -d ' ')
if [ "$LINES" -gt 200 ]; then
    echo "⚠️  WARNING: main.py tiene $LINES líneas (máximo recomendado: 200)"
    echo "   Considerar refactorizar a módulos específicos"
    echo ""
fi

# Resultado final
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo "✅ Verificación exitosa - Arquitectura cumple reglas"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo "❌ Verificación fallida - $ERRORS errores encontrados"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Por favor corregir antes de hacer commit."
    echo "Consultar: ARCHITECTURE_RULES.md"
    exit 1
fi
