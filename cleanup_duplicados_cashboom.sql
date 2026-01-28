-- ============================================================================
-- SCRIPT DE LIMPIEZA: Cobros Duplicados de Cashboom
-- ============================================================================
-- Fecha: 28/01/2026
-- Propósito: Eliminar cobros duplicados de Cashboom generados durante pruebas
-- 
-- IMPORTANTE: Este script es para limpiar datos de PRUEBA
-- Si tienes cobros REALES, adapta el WHERE según sea necesario
-- ============================================================================

-- PASO 1: Verificar cobros duplicados de Cashboom
-- ============================================================================
-- Esto te mostrará todos los cobros de Cashboom y sus detalles
SELECT 
    i.id,
    c.nombre as cliente_nombre,
    i.fecha_cobro,
    i.periodo,
    i.mes_aplicado,
    i.monto_usd_total,
    i.detalle,
    i.created_at
FROM ingresos i
JOIN clientes c ON i.cliente_id = c.id
WHERE c.nombre ILIKE '%cashboom%'  -- Busca cualquier variación de "Cashboom"
ORDER BY i.created_at DESC;

-- RESULTADO ESPERADO:
-- Verás múltiples registros de Cashboom con el mismo mes_aplicado
-- Ejemplo:
-- id | cliente_nombre | fecha_cobro | periodo  | mes_aplicado | monto_usd_total | created_at
-- ---|----------------|-------------|----------|--------------|-----------------|-------------
-- 1  | Cashboom       | 2026-01-28  | 01-2026  | 02-2026      | 150.00          | 2026-01-28 10:00:00
-- 2  | Cashboom       | 2026-01-28  | 01-2026  | 02-2026      | 150.00          | 2026-01-28 10:05:00
-- 3  | Cashboom       | 2026-01-28  | 01-2026  | 02-2026      | 150.00          | 2026-01-28 10:10:00


-- ============================================================================
-- PASO 2A: OPCIÓN SEGURA - Mantener el primer cobro, eliminar duplicados
-- ============================================================================
-- Esta query ELIMINA todos los cobros duplicados EXCEPTO el más antiguo (primero)

-- ANTES DE EJECUTAR: Verifica cuántos registros se van a eliminar
SELECT 
    COUNT(*) as registros_a_eliminar,
    SUM(i.monto_usd_total) as total_usd_a_eliminar
FROM ingresos i
JOIN clientes c ON i.cliente_id = c.id
WHERE c.nombre ILIKE '%cashboom%'
AND mes_aplicado = '02-2026'  -- Ajusta según el mes que quieras limpiar
AND i.id NOT IN (
    -- Mantener solo el primer cobro (más antiguo)
    SELECT MIN(i2.id)
    FROM ingresos i2
    JOIN clientes c2 ON i2.cliente_id = c2.id
    WHERE c2.nombre ILIKE '%cashboom%'
    AND i2.mes_aplicado = '02-2026'
);

-- Si el resultado te parece correcto, ejecuta el DELETE:
DELETE FROM ingresos
WHERE id IN (
    SELECT i.id
    FROM ingresos i
    JOIN clientes c ON i.cliente_id = c.id
    WHERE c.nombre ILIKE '%cashboom%'
    AND mes_aplicado = '02-2026'
    AND i.id NOT IN (
        -- Mantener solo el primer cobro (más antiguo)
        SELECT MIN(i2.id)
        FROM ingresos i2
        JOIN clientes c2 ON i2.cliente_id = c2.id
        WHERE c2.nombre ILIKE '%cashboom%'
        AND i2.mes_aplicado = '02-2026'
    )
);

-- ============================================================================
-- PASO 2B: OPCIÓN NUCLEAR - Eliminar TODOS los cobros de Cashboom
-- ============================================================================
-- CUIDADO: Esta opción elimina TODOS los cobros de Cashboom, no solo duplicados

-- Verificar primero:
SELECT 
    COUNT(*) as total_registros,
    SUM(monto_usd_total) as total_usd
FROM ingresos i
JOIN clientes c ON i.cliente_id = c.id
WHERE c.nombre ILIKE '%cashboom%';

-- Si estás seguro, ejecuta:
-- DELETE FROM ingresos
-- WHERE cliente_id IN (
--     SELECT id FROM clientes WHERE nombre ILIKE '%cashboom%'
-- );

-- ============================================================================
-- PASO 3: Verificar que se limpiaron correctamente
-- ============================================================================
-- Debería mostrar solo 1 registro (o 0 si usaste la opción nuclear)
SELECT 
    COUNT(*) as registros_restantes,
    SUM(i.monto_usd_total) as total_usd_restante
FROM ingresos i
JOIN clientes c ON i.cliente_id = c.id
WHERE c.nombre ILIKE '%cashboom%'
AND mes_aplicado = '02-2026';

-- ============================================================================
-- PASO 4: Ver todos los cobros por cliente y mes para auditoría
-- ============================================================================
-- Esta query te muestra un resumen por cliente y mes_aplicado
SELECT 
    c.nombre as cliente,
    i.mes_aplicado,
    COUNT(*) as cantidad_cobros,
    SUM(i.monto_usd_total) as total_usd,
    STRING_AGG(i.fecha_cobro::TEXT, ', ' ORDER BY i.created_at) as fechas_cobro
FROM ingresos i
JOIN clientes c ON i.cliente_id = c.id
WHERE i.mes_aplicado IS NOT NULL
GROUP BY c.nombre, i.mes_aplicado
HAVING COUNT(*) > 1  -- Solo mostrar los que tienen duplicados
ORDER BY c.nombre, i.mes_aplicado;

-- RESULTADO ESPERADO (antes de limpiar):
-- cliente  | mes_aplicado | cantidad_cobros | total_usd | fechas_cobro
-- ---------|--------------|-----------------|-----------|---------------
-- Cashboom | 02-2026      | 3               | 450.00    | 2026-01-28, 2026-01-28, 2026-01-28

-- RESULTADO ESPERADO (después de limpiar):
-- (No debería mostrar nada, o solo registros con 1 cobro)

-- ============================================================================
-- BONUS: Crear restricción para evitar duplicados futuros
-- ============================================================================
-- Esto evita que se puedan crear cobros duplicados en el futuro

-- NOTA: Solo ejecuta esto DESPUÉS de limpiar los duplicados
-- ALTER TABLE ingresos
-- ADD CONSTRAINT unique_cliente_mes_aplicado 
-- UNIQUE (cliente_id, mes_aplicado);

-- Si ejecutas esto ANTES de limpiar, fallará porque hay duplicados existentes

-- ============================================================================
-- RESUMEN DE LIMPIEZA
-- ============================================================================

-- Para limpieza rápida de prueba (recomendado):
-- 1. Ejecuta PASO 1 para ver los duplicados
-- 2. Ejecuta PASO 2A para eliminar duplicados (mantiene el primero)
-- 3. Ejecuta PASO 3 para verificar
-- 4. Ejecuta PASO 4 para auditar todos los clientes

-- Si quieres empezar de cero con Cashboom:
-- 1. Descomenta y ejecuta PASO 2B (opción nuclear)
-- 2. Verifica con PASO 3

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================

-- 1. Los montos eliminados NO afectan PST.NET (eso viene de API externa)
-- 2. Los montos eliminados SÍ afectan el dashboard de honorarios
-- 3. Si eliminaste algo por error, NO HAY UNDO - deberás re-registrar manualmente
-- 4. Antes de ejecutar DELETE, SIEMPRE ejecuta el SELECT equivalente primero
-- 5. Considera hacer backup de la tabla antes de eliminar:
--    CREATE TABLE ingresos_backup_20260128 AS SELECT * FROM ingresos;

-- ============================================================================
