-- ============================================================================
-- MIGRACIÓN: ATRIBUCIÓN TEMPORAL DE INGRESOS
-- ============================================================================
-- Fecha: 28/01/2026
-- Autor: Black Infrastructure Dashboard Team
-- 
-- OBJETIVO:
-- Separar la fecha de cobro del mes al que pertenece el ingreso.
-- Los cobros son por adelantado, entonces si cobro hoy (28/01), el dinero
-- ya es mío (liquidez), pero corresponde al trabajo de Febrero (performance).
--
-- COLUMNAS:
-- - fecha_cobro: Fecha real del cobro (cuándo entró el dinero)
-- - periodo: Periodo del sistema cuando se registra (para context histórico)
-- - mes_aplicado: Mes al que pertenece el servicio/trabajo (para performance)
-- ============================================================================

-- 1. Agregar columna mes_aplicado a la tabla ingresos
ALTER TABLE ingresos
ADD COLUMN IF NOT EXISTS mes_aplicado VARCHAR(7);

-- 2. Comentar las columnas para documentar la lógica
COMMENT ON COLUMN ingresos.fecha_cobro IS 'Fecha real en que se cobró (cuándo entró el dinero a la cuenta)';
COMMENT ON COLUMN ingresos.periodo IS 'Periodo del sistema cuando se registró el cobro (contexto histórico)';
COMMENT ON COLUMN ingresos.mes_aplicado IS 'Mes al que pertenece el servicio/trabajo (para cálculo de performance mensual)';

-- 3. Migrar datos existentes (IMPORTANTE: ejecutar solo si hay datos previos)
-- Los ingresos antiguos se asume que fecha_cobro = mes_aplicado
UPDATE ingresos
SET mes_aplicado = periodo
WHERE mes_aplicado IS NULL;

-- 4. Crear índices para mejorar performance de queries
CREATE INDEX IF NOT EXISTS idx_ingresos_mes_aplicado ON ingresos(mes_aplicado);
CREATE INDEX IF NOT EXISTS idx_ingresos_fecha_cobro ON ingresos(fecha_cobro);

-- 5. Crear vista para Liquidez Total (todo lo cobrado)
CREATE OR REPLACE VIEW vista_liquidez_total AS
SELECT 
    periodo,
    SUM(monto_usd_total) as total_usd,
    SUM(monto_ars) as total_ars,
    COUNT(*) as cantidad_cobros,
    MIN(fecha_cobro) as primer_cobro,
    MAX(fecha_cobro) as ultimo_cobro
FROM ingresos
GROUP BY periodo
ORDER BY periodo DESC;

-- 6. Crear vista para Performance Mensual (solo lo que corresponde a ese mes)
CREATE OR REPLACE VIEW vista_performance_mensual AS
SELECT 
    mes_aplicado,
    SUM(monto_usd_total) as total_usd,
    SUM(monto_ars) as total_ars,
    COUNT(*) as cantidad_servicios,
    COUNT(DISTINCT cliente_id) as clientes_unicos
FROM ingresos
WHERE mes_aplicado IS NOT NULL
GROUP BY mes_aplicado
ORDER BY mes_aplicado DESC;

-- 7. Crear función para calcular el mes aplicado (próximo mes)
CREATE OR REPLACE FUNCTION calcular_mes_aplicado(fecha_cobro_param DATE)
RETURNS VARCHAR(7) AS $$
DECLARE
    mes_proximo INTEGER;
    anio_proximo INTEGER;
    fecha_siguiente_mes DATE;
BEGIN
    -- Calcular el primer día del mes siguiente
    fecha_siguiente_mes := DATE_TRUNC('month', fecha_cobro_param) + INTERVAL '1 month';
    
    -- Extraer mes y año
    mes_proximo := EXTRACT(MONTH FROM fecha_siguiente_mes);
    anio_proximo := EXTRACT(YEAR FROM fecha_siguiente_mes);
    
    -- Retornar en formato MM-YYYY
    RETURN LPAD(mes_proximo::TEXT, 2, '0') || '-' || anio_proximo::TEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 8. Crear función para obtener ingresos por tipo de vista
CREATE OR REPLACE FUNCTION obtener_ingresos_dashboard(
    periodo_param VARCHAR(7),
    tipo_vista VARCHAR(20) DEFAULT 'performance'
)
RETURNS TABLE (
    total_usd NUMERIC,
    total_ars NUMERIC,
    cantidad_registros BIGINT
) AS $$
BEGIN
    IF tipo_vista = 'liquidez' THEN
        -- Liquidez: Todo lo cobrado en ese periodo (sin importar mes_aplicado)
        RETURN QUERY
        SELECT 
            COALESCE(SUM(monto_usd_total), 0)::NUMERIC as total_usd,
            COALESCE(SUM(monto_ars), 0)::NUMERIC as total_ars,
            COUNT(*)::BIGINT as cantidad_registros
        FROM ingresos
        WHERE periodo = periodo_param;
    ELSE
        -- Performance: Solo lo que corresponde a ese mes (mes_aplicado)
        RETURN QUERY
        SELECT 
            COALESCE(SUM(monto_usd_total), 0)::NUMERIC as total_usd,
            COALESCE(SUM(monto_ars), 0)::NUMERIC as total_ars,
            COUNT(*)::BIGINT as cantidad_registros
        FROM ingresos
        WHERE mes_aplicado = periodo_param;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- EJEMPLOS DE USO
-- ============================================================================

-- Ejemplo 1: Ver liquidez total del periodo actual (todo lo cobrado)
-- SELECT * FROM obtener_ingresos_dashboard('01-2026', 'liquidez');

-- Ejemplo 2: Ver performance del mes (solo lo que corresponde a enero)
-- SELECT * FROM obtener_ingresos_dashboard('01-2026', 'performance');

-- Ejemplo 3: Calcular mes aplicado para un cobro de hoy
-- SELECT calcular_mes_aplicado(CURRENT_DATE);  -- Retorna '02-2026' si hoy es enero

-- Ejemplo 4: Insertar un cobro con atribución correcta
-- INSERT INTO ingresos (
--     cliente_id, 
--     monto_usd_total, 
--     fecha_cobro, 
--     periodo,
--     mes_aplicado
-- ) VALUES (
--     'uuid-del-cliente',
--     150.00,
--     '2026-01-28',              -- Fecha real del cobro
--     '01-2026',                  -- Periodo actual del sistema
--     calcular_mes_aplicado(CURRENT_DATE)  -- '02-2026' = Febrero
-- );

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================
-- SELECT 
--     fecha_cobro,
--     periodo as periodo_sistema,
--     mes_aplicado as mes_servicio,
--     monto_usd_total,
--     detalle
-- FROM ingresos
-- ORDER BY fecha_cobro DESC
-- LIMIT 10;
