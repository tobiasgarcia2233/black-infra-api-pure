-- ============================================================================
-- SCRIPT DE VERIFICACIÓN DE ESQUEMA DE BASE DE DATOS
-- ============================================================================
-- Fecha: 28/01/2026
-- Propósito: Verificar que la tabla ingresos tenga todas las columnas necesarias
-- ============================================================================

-- 1. Verificar columnas de la tabla ingresos
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ingresos'
ORDER BY ordinal_position;

-- RESULTADO ESPERADO:
-- ✅ Deberías ver estas columnas:
--    - id (uuid)
--    - cliente_id (uuid)
--    - monto_usd_total (numeric)
--    - monto_ars (numeric)
--    - fecha_cobro (date)
--    - periodo (varchar)
--    - mes_aplicado (varchar) ← ESTA ES LA NUEVA
--    - detalle (text)
--    - created_at (timestamp)

-- ============================================================================

-- 2. Verificar específicamente si existe la columna mes_aplicado
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'ingresos' 
            AND column_name = 'mes_aplicado'
        ) THEN '✅ La columna mes_aplicado EXISTE'
        ELSE '❌ La columna mes_aplicado NO EXISTE - Ejecuta migration_atribucion_temporal.sql'
    END as estado_mes_aplicado;

-- ============================================================================

-- 3. Verificar funciones SQL helpers
SELECT 
    routine_name,
    routine_type,
    data_type as return_type
FROM information_schema.routines
WHERE routine_name IN (
    'calcular_mes_aplicado',
    'obtener_ingresos_dashboard'
)
ORDER BY routine_name;

-- RESULTADO ESPERADO:
-- ✅ calcular_mes_aplicado (function, returns varchar)
-- ✅ obtener_ingresos_dashboard (function, returns TABLE)

-- ============================================================================

-- 4. Verificar vistas creadas
SELECT 
    table_name,
    table_type
FROM information_schema.tables
WHERE table_name IN (
    'vista_liquidez_total',
    'vista_performance_mensual'
)
ORDER BY table_name;

-- RESULTADO ESPERADO:
-- ✅ vista_liquidez_total (VIEW)
-- ✅ vista_performance_mensual (VIEW)

-- ============================================================================

-- 5. Verificar índices de performance
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'ingresos'
AND indexname IN (
    'idx_ingresos_mes_aplicado',
    'idx_ingresos_fecha_cobro'
);

-- RESULTADO ESPERADO:
-- ✅ idx_ingresos_mes_aplicado
-- ✅ idx_ingresos_fecha_cobro

-- ============================================================================

-- 6. Verificar políticas RLS (Row Level Security)
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'ingresos';

-- RESULTADO:
-- Verifica que existan políticas que permitan:
-- ✅ INSERT para usuarios autenticados
-- ✅ SELECT para usuarios autenticados
-- ✅ UPDATE para usuarios autenticados (si es necesario)

-- ============================================================================

-- 7. Probar la función calcular_mes_aplicado (si existe)
-- Descomentar esta línea si la función ya existe:
-- SELECT calcular_mes_aplicado(CURRENT_DATE) as mes_siguiente;

-- RESULTADO ESPERADO:
-- Si hoy es 28/01/2026, debería retornar: '02-2026' (Febrero)

-- ============================================================================

-- 8. Ver algunos registros de ingresos (si existen)
SELECT 
    id,
    fecha_cobro,
    periodo,
    mes_aplicado,
    monto_usd_total,
    detalle,
    created_at
FROM ingresos
ORDER BY created_at DESC
LIMIT 5;

-- RESULTADO:
-- Verifica si los registros tienen mes_aplicado poblado
-- Si ves NULL en mes_aplicado para registros antiguos, es normal
-- Los nuevos cobros deberían tener mes_aplicado poblado

-- ============================================================================
-- DIAGNÓSTICO RÁPIDO
-- ============================================================================

-- Si alguno de estos faltan, ejecuta migration_atribucion_temporal.sql:
-- [ ] Columna mes_aplicado existe
-- [ ] Función calcular_mes_aplicado existe
-- [ ] Función obtener_ingresos_dashboard existe
-- [ ] Vista vista_liquidez_total existe
-- [ ] Vista vista_performance_mensual existe
-- [ ] Índices de performance existen

-- ============================================================================
-- TROUBLESHOOTING
-- ============================================================================

-- PROBLEMA: "Column mes_aplicado does not exist"
-- SOLUCIÓN: Ejecuta migration_atribucion_temporal.sql

-- PROBLEMA: "Permission denied for table ingresos"
-- SOLUCIÓN: Verifica políticas RLS. Ejecuta:
--   ALTER TABLE ingresos ENABLE ROW LEVEL SECURITY;
--   
--   CREATE POLICY "Usuarios autenticados pueden insertar" 
--   ON ingresos FOR INSERT 
--   TO authenticated 
--   WITH CHECK (true);
--
--   CREATE POLICY "Usuarios autenticados pueden leer" 
--   ON ingresos FOR SELECT 
--   TO authenticated 
--   USING (true);

-- PROBLEMA: "Duplicate key value violates unique constraint"
-- SOLUCIÓN: Ya existe un cobro para ese cliente en ese mes_aplicado
--           Verifica en la tabla si ya fue registrado

-- ============================================================================
