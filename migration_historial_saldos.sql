-- ============================================================================
-- MIGRACIÓN: Historial de Saldos (Snapshots Mensuales)
-- ============================================================================
-- Fecha: 28/01/2026
-- Versión: v106.0
-- Autor: Senior Backend Developer
--
-- PROPÓSITO:
-- Crear tabla para almacenar "snapshots" mensuales del estado financiero
-- de PST.NET. Esto previene que los datos históricos se pierdan cuando
-- los valores en vivo de la API cambien.
--
-- FEATURES:
-- - Snapshot automático el día 1 de cada mes
-- - Preserva balance de cuentas, cashback aprobado y hold
-- - Permite navegar la historia sin perder datos
-- - El "Cashback Stacking" siempre muestra valor actual (no snapshot)
-- ============================================================================

-- Crear tabla de historial de saldos
CREATE TABLE IF NOT EXISTS historial_saldos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificación del periodo
    periodo VARCHAR(7) NOT NULL UNIQUE, -- Formato: MM-YYYY (ej: 01-2026)
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    
    -- Snapshot de PST.NET al cierre del mes
    balance_cuentas_total DECIMAL(12, 2) NOT NULL DEFAULT 0, -- Total de cuentas ID 15 + ID 2
    neto_reparto DECIMAL(12, 2) NOT NULL DEFAULT 0,           -- 50% del balance de cuentas
    
    -- Cashback al momento del snapshot (informativo)
    cashback_aprobado DECIMAL(12, 2) NOT NULL DEFAULT 0,      -- Cashback aprobado
    cashback_hold DECIMAL(12, 2) NOT NULL DEFAULT 0,          -- Cashback en hold
    
    -- Desglose por currency_id (JSON)
    desglose_por_currency JSONB,                              -- {"1": {"name": "USD", "total": 1234.56}, ...}
    
    -- Metadata
    fecha_snapshot TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    notas TEXT,                                                -- Notas adicionales del cierre
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para búsquedas eficientes
CREATE INDEX IF NOT EXISTS idx_historial_saldos_periodo ON historial_saldos(periodo);
CREATE INDEX IF NOT EXISTS idx_historial_saldos_anio_mes ON historial_saldos(anio, mes);
CREATE INDEX IF NOT EXISTS idx_historial_saldos_fecha_snapshot ON historial_saldos(fecha_snapshot);

-- Constraint para asegurar formato de periodo
ALTER TABLE historial_saldos
ADD CONSTRAINT chk_periodo_formato CHECK (periodo ~ '^\d{2}-\d{4}$');

-- Constraint para mes válido (1-12)
ALTER TABLE historial_saldos
ADD CONSTRAINT chk_mes_valido CHECK (mes >= 1 AND mes <= 12);

-- Comentarios en la tabla
COMMENT ON TABLE historial_saldos IS 'Snapshots mensuales de saldos PST.NET para preservar historia financiera';
COMMENT ON COLUMN historial_saldos.periodo IS 'Periodo en formato MM-YYYY (ej: 01-2026)';
COMMENT ON COLUMN historial_saldos.balance_cuentas_total IS 'Balance total de cuentas ID 15 + ID 2 al cierre del mes';
COMMENT ON COLUMN historial_saldos.neto_reparto IS '50% del balance de cuentas (valor conservador)';
COMMENT ON COLUMN historial_saldos.cashback_aprobado IS 'Cashback aprobado al momento del snapshot (informativo)';
COMMENT ON COLUMN historial_saldos.cashback_hold IS 'Cashback en hold al momento del snapshot (informativo)';

-- ============================================================================
-- FUNCIÓN: Crear Snapshot del Mes Anterior
-- ============================================================================
-- Toma una "foto" del estado actual de PST.NET y la guarda como snapshot
-- del mes que acaba de cerrar.
--
-- Uso:
--   SELECT crear_snapshot_mes_anterior();
--
-- Retorna: Periodo del snapshot creado (ej: '12-2025')
-- ============================================================================

CREATE OR REPLACE FUNCTION crear_snapshot_mes_anterior()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_periodo_anterior TEXT;
    v_anio_anterior INTEGER;
    v_mes_anterior INTEGER;
    v_balance_cuentas DECIMAL(12, 2);
    v_neto_reparto DECIMAL(12, 2);
    v_cashback_aprobado DECIMAL(12, 2);
    v_cashback_hold DECIMAL(12, 2);
    v_snapshot_existente INTEGER;
BEGIN
    -- Calcular periodo anterior (mes que acaba de cerrar)
    v_anio_anterior := EXTRACT(YEAR FROM (CURRENT_DATE - INTERVAL '1 month'));
    v_mes_anterior := EXTRACT(MONTH FROM (CURRENT_DATE - INTERVAL '1 month'));
    v_periodo_anterior := LPAD(v_mes_anterior::TEXT, 2, '0') || '-' || v_anio_anterior::TEXT;
    
    RAISE NOTICE '📸 Creando snapshot para periodo: %', v_periodo_anterior;
    
    -- Verificar si ya existe un snapshot para este periodo
    SELECT COUNT(*) INTO v_snapshot_existente
    FROM historial_saldos
    WHERE periodo = v_periodo_anterior;
    
    IF v_snapshot_existente > 0 THEN
        RAISE NOTICE '⚠️  Ya existe un snapshot para el periodo %', v_periodo_anterior;
        RETURN v_periodo_anterior;
    END IF;
    
    -- Obtener valores actuales de configuración (valores en vivo de PST.NET)
    SELECT 
        COALESCE(
            (SELECT valor_numerico FROM configuracion WHERE clave = 'pst_balance_neto'),
            0
        ) INTO v_neto_reparto;
    
    -- Calcular balance total (neto_reparto * 2, ya que neto es el 50%)
    v_balance_cuentas := v_neto_reparto * 2;
    
    SELECT 
        COALESCE(
            (SELECT valor_numerico FROM configuracion WHERE clave = 'pst_cashback_aprobado'),
            0
        ) INTO v_cashback_aprobado;
    
    SELECT 
        COALESCE(
            (SELECT valor_numerico FROM configuracion WHERE clave = 'pst_cashback_hold'),
            0
        ) INTO v_cashback_hold;
    
    RAISE NOTICE '💰 Balance cuentas: $%', v_balance_cuentas;
    RAISE NOTICE '💰 Neto reparto (50%%): $%', v_neto_reparto;
    RAISE NOTICE '🎁 Cashback aprobado: $%', v_cashback_aprobado;
    RAISE NOTICE '🔒 Cashback hold: $%', v_cashback_hold;
    
    -- Insertar snapshot
    INSERT INTO historial_saldos (
        periodo,
        anio,
        mes,
        balance_cuentas_total,
        neto_reparto,
        cashback_aprobado,
        cashback_hold,
        fecha_snapshot,
        notas
    ) VALUES (
        v_periodo_anterior,
        v_anio_anterior,
        v_mes_anterior,
        v_balance_cuentas,
        v_neto_reparto,
        v_cashback_aprobado,
        v_cashback_hold,
        NOW(),
        'Snapshot automático de cierre de mes'
    );
    
    RAISE NOTICE '✅ Snapshot creado exitosamente para periodo %', v_periodo_anterior;
    
    RETURN v_periodo_anterior;
END;
$$;

-- Comentario de la función
COMMENT ON FUNCTION crear_snapshot_mes_anterior() IS 'Crea snapshot del mes anterior con los valores actuales de PST.NET';

-- ============================================================================
-- FUNCIÓN: Obtener Snapshot de un Periodo
-- ============================================================================
-- Retorna el snapshot de un periodo específico, o NULL si no existe.
--
-- Uso:
--   SELECT * FROM obtener_snapshot_periodo('12-2025');
-- ============================================================================

CREATE OR REPLACE FUNCTION obtener_snapshot_periodo(p_periodo TEXT)
RETURNS TABLE (
    periodo TEXT,
    balance_cuentas_total DECIMAL(12, 2),
    neto_reparto DECIMAL(12, 2),
    cashback_aprobado DECIMAL(12, 2),
    cashback_hold DECIMAL(12, 2),
    fecha_snapshot TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        hs.periodo,
        hs.balance_cuentas_total,
        hs.neto_reparto,
        hs.cashback_aprobado,
        hs.cashback_hold,
        hs.fecha_snapshot
    FROM historial_saldos hs
    WHERE hs.periodo = p_periodo;
END;
$$;

-- Comentario de la función
COMMENT ON FUNCTION obtener_snapshot_periodo(TEXT) IS 'Obtiene el snapshot de un periodo específico (formato: MM-YYYY)';

-- ============================================================================
-- GRANTS (Permisos)
-- ============================================================================

-- Dar permisos a usuarios autenticados
GRANT SELECT ON historial_saldos TO authenticated;
GRANT SELECT ON historial_saldos TO anon;

-- Permisos para service_role (puede insertar/actualizar)
GRANT ALL ON historial_saldos TO service_role;

-- ============================================================================
-- DATOS DE PRUEBA (Opcional - Comentar si no se necesita)
-- ============================================================================

-- Crear snapshot del mes actual como ejemplo
-- SELECT crear_snapshot_mes_anterior();

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

-- Ver todos los snapshots
-- SELECT 
--     periodo,
--     balance_cuentas_total,
--     neto_reparto,
--     cashback_aprobado,
--     cashback_hold,
--     fecha_snapshot
-- FROM historial_saldos
-- ORDER BY anio DESC, mes DESC;

-- ============================================================================
-- ROLLBACK (Si se necesita deshacer)
-- ============================================================================

-- DROP FUNCTION IF EXISTS obtener_snapshot_periodo(TEXT);
-- DROP FUNCTION IF EXISTS crear_snapshot_mes_anterior();
-- DROP TABLE IF EXISTS historial_saldos;
