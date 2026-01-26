-- ============================================================================
-- MIGRACIÓN: Agregar columna periodo (MM-YYYY) a ingresos y costos
-- ============================================================================
-- Fecha: 24/01/2026
-- Autor: Senior Backend Developer
-- Descripción: Agregar columna periodo para filtrar por mes de manera eficiente
-- ============================================================================

-- 1. Agregar columna periodo a la tabla ingresos
ALTER TABLE ingresos 
ADD COLUMN IF NOT EXISTS periodo VARCHAR(7);

-- 2. Agregar columna periodo a la tabla costos (si existe)
ALTER TABLE costos 
ADD COLUMN IF NOT EXISTS periodo VARCHAR(7);

-- 3. Crear índice para mejorar performance de queries por periodo
CREATE INDEX IF NOT EXISTS idx_ingresos_periodo ON ingresos(periodo);
CREATE INDEX IF NOT EXISTS idx_costos_periodo ON costos(periodo);

-- 4. Actualizar registros existentes en ingresos con periodo basado en fecha_cobro
UPDATE ingresos
SET periodo = TO_CHAR(fecha_cobro::date, 'MM-YYYY')
WHERE periodo IS NULL AND fecha_cobro IS NOT NULL;

-- 5. Actualizar registros existentes en costos con periodo basado en created_at o fecha
UPDATE costos
SET periodo = TO_CHAR(
    COALESCE(
        fecha_cobro::date,
        created_at::date,
        CURRENT_DATE
    ), 
    'MM-YYYY'
)
WHERE periodo IS NULL;

-- 6. Hacer periodo NOT NULL en ingresos (después de actualizar existentes)
-- Descomentar esta línea después de verificar que todos los registros tienen periodo
-- ALTER TABLE ingresos ALTER COLUMN periodo SET NOT NULL;

-- 7. Crear vista para consultas rápidas del mes actual
CREATE OR REPLACE VIEW ingresos_mes_actual AS
SELECT *
FROM ingresos
WHERE periodo = TO_CHAR(CURRENT_DATE, 'MM-YYYY');

CREATE OR REPLACE VIEW costos_mes_actual AS
SELECT *
FROM costos
WHERE periodo = TO_CHAR(CURRENT_DATE, 'MM-YYYY');

-- 8. Función helper para obtener periodo actual
CREATE OR REPLACE FUNCTION get_periodo_actual()
RETURNS VARCHAR(7) AS $$
BEGIN
    RETURN TO_CHAR(CURRENT_DATE, 'MM-YYYY');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 9. Función para obtener periodos disponibles (últimos 12 meses)
CREATE OR REPLACE FUNCTION get_periodos_disponibles(limite INT DEFAULT 12)
RETURNS TABLE(periodo VARCHAR(7), mes INT, anio INT) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        TO_CHAR(fecha, 'MM-YYYY') AS periodo,
        EXTRACT(MONTH FROM fecha)::INT AS mes,
        EXTRACT(YEAR FROM fecha)::INT AS anio
    FROM (
        SELECT generate_series(
            CURRENT_DATE - INTERVAL '11 months',
            CURRENT_DATE,
            '1 month'::interval
        )::date AS fecha
    ) AS fechas
    ORDER BY anio DESC, mes DESC
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- QUERIES DE VERIFICACIÓN
-- ============================================================================

-- Ver ingresos por periodo
-- SELECT periodo, COUNT(*), SUM(monto_usd_total) as total_usd
-- FROM ingresos
-- GROUP BY periodo
-- ORDER BY periodo DESC;

-- Ver costos por periodo
-- SELECT periodo, COUNT(*), SUM(monto_usd) as total_usd
-- FROM costos
-- GROUP BY periodo
-- ORDER BY periodo DESC;

-- Ver periodos disponibles
-- SELECT * FROM get_periodos_disponibles();
