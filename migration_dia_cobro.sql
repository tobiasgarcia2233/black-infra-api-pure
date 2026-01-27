-- ============================================================================
-- MIGRACIÓN: Agregar columna dia_cobro a la tabla clientes
-- ============================================================================
-- Fecha: 27/01/2026
-- Autor: Senior Full Stack Developer
-- Descripción: Agregar día de cobro mensual para calcular próximos pagos
-- ============================================================================

-- 1. Agregar columna dia_cobro a la tabla clientes
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS dia_cobro INTEGER;

-- 2. Agregar constraint para validar que el día esté entre 1 y 31
ALTER TABLE clientes
ADD CONSTRAINT dia_cobro_valido CHECK (dia_cobro >= 1 AND dia_cobro <= 31);

-- 3. Crear índice para queries de vencimientos
CREATE INDEX IF NOT EXISTS idx_clientes_dia_cobro ON clientes(dia_cobro);

-- 4. Función para calcular el próximo vencimiento de un cliente
CREATE OR REPLACE FUNCTION calcular_proximo_vencimiento(p_dia_cobro INTEGER)
RETURNS DATE AS $$
DECLARE
    v_hoy DATE := CURRENT_DATE;
    v_mes_actual INTEGER := EXTRACT(MONTH FROM v_hoy);
    v_anio_actual INTEGER := EXTRACT(YEAR FROM v_hoy);
    v_dia_actual INTEGER := EXTRACT(DAY FROM v_hoy);
    v_proximo_vencimiento DATE;
BEGIN
    -- Si el día ya pasó este mes, el próximo vencimiento es el mes siguiente
    IF v_dia_actual > p_dia_cobro THEN
        -- Calcular próximo mes
        IF v_mes_actual = 12 THEN
            v_proximo_vencimiento := make_date(v_anio_actual + 1, 1, p_dia_cobro);
        ELSE
            v_proximo_vencimiento := make_date(v_anio_actual, v_mes_actual + 1, p_dia_cobro);
        END IF;
    ELSE
        -- El vencimiento es este mes
        v_proximo_vencimiento := make_date(v_anio_actual, v_mes_actual, p_dia_cobro);
    END IF;
    
    RETURN v_proximo_vencimiento;
EXCEPTION
    WHEN OTHERS THEN
        -- Si hay error (ej: 31 de febrero), usar el último día del mes
        IF v_dia_actual > p_dia_cobro THEN
            IF v_mes_actual = 12 THEN
                RETURN (make_date(v_anio_actual + 1, 1, 1) + INTERVAL '1 month - 1 day')::DATE;
            ELSE
                RETURN (make_date(v_anio_actual, v_mes_actual + 1, 1) + INTERVAL '1 month - 1 day')::DATE;
            END IF;
        ELSE
            RETURN (make_date(v_anio_actual, v_mes_actual, 1) + INTERVAL '1 month - 1 day')::DATE;
        END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 5. Vista para obtener clientes con próximos vencimientos
CREATE OR REPLACE VIEW v_clientes_vencimientos AS
SELECT 
    c.id,
    c.nombre,
    c.estado,
    c.fee_mensual,
    c.dia_cobro,
    CASE 
        WHEN c.dia_cobro IS NOT NULL THEN calcular_proximo_vencimiento(c.dia_cobro)
        ELSE NULL
    END AS proximo_vencimiento,
    CASE 
        WHEN c.dia_cobro IS NOT NULL THEN 
            calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE
        ELSE NULL
    END AS dias_hasta_vencimiento
FROM clientes c
WHERE c.estado = 'Activo'
ORDER BY proximo_vencimiento ASC NULLS LAST;

-- 6. Función para obtener cobros pendientes de la semana
CREATE OR REPLACE FUNCTION obtener_cobros_semana()
RETURNS TABLE(
    cliente_id UUID,
    nombre VARCHAR,
    fee_mensual NUMERIC,
    proximo_vencimiento DATE,
    dias_hasta_vencimiento INTEGER,
    estado_urgencia VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.nombre,
        c.fee_mensual,
        calcular_proximo_vencimiento(c.dia_cobro) AS proximo_vencimiento,
        (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE)::INTEGER AS dias_hasta_vencimiento,
        CASE 
            WHEN (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) < 0 THEN 'ATRASADO'
            WHEN (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) = 0 THEN 'HOY'
            WHEN (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) <= 3 THEN 'URGENTE'
            WHEN (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) <= 7 THEN 'ESTA_SEMANA'
            ELSE 'NORMAL'
        END AS estado_urgencia
    FROM clientes c
    WHERE c.estado = 'Activo' 
        AND c.dia_cobro IS NOT NULL
        AND (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) <= 7
    ORDER BY proximo_vencimiento ASC;
END;
$$ LANGUAGE plpgsql;

-- 7. Función para obtener detalle completo de cobros de la semana (NUEVA)
CREATE OR REPLACE FUNCTION obtener_detalle_cobros_semana()
RETURNS TABLE(
    cliente_id UUID,
    nombre VARCHAR,
    fee_mensual NUMERIC,
    dia_cobro INTEGER,
    proximo_vencimiento DATE,
    dias_hasta_vencimiento INTEGER,
    estado_urgencia VARCHAR,
    total_semana NUMERIC
) AS $$
DECLARE
    v_total_semana NUMERIC;
BEGIN
    -- Calcular el total de cobros de la semana
    SELECT COALESCE(SUM(c.fee_mensual), 0) INTO v_total_semana
    FROM clientes c
    WHERE c.estado = 'Activo' 
        AND c.dia_cobro IS NOT NULL
        AND (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) <= 7
        AND (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) >= 0;
    
    -- Retornar el detalle de cada cliente
    RETURN QUERY
    SELECT 
        c.id,
        c.nombre,
        c.fee_mensual,
        c.dia_cobro,
        calcular_proximo_vencimiento(c.dia_cobro) AS proximo_vencimiento,
        (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE)::INTEGER AS dias_hasta_vencimiento,
        CASE 
            WHEN (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) < 0 THEN 'ATRASADO'
            WHEN (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) = 0 THEN 'HOY'
            WHEN (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) <= 3 THEN 'URGENTE'
            WHEN (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) <= 7 THEN 'ESTA_SEMANA'
            ELSE 'NORMAL'
        END AS estado_urgencia,
        v_total_semana AS total_semana
    FROM clientes c
    WHERE c.estado = 'Activo' 
        AND c.dia_cobro IS NOT NULL
        AND (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) <= 7
        AND (calcular_proximo_vencimiento(c.dia_cobro) - CURRENT_DATE) >= 0
    ORDER BY proximo_vencimiento ASC, c.nombre ASC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- QUERIES DE VERIFICACIÓN
-- ============================================================================

-- Ver clientes con sus próximos vencimientos
-- SELECT * FROM v_clientes_vencimientos LIMIT 10;

-- Ver cobros de esta semana
-- SELECT * FROM obtener_cobros_semana();

-- Actualizar día de cobro de un cliente específico
-- UPDATE clientes SET dia_cobro = 15 WHERE nombre = 'Cliente Ejemplo';
