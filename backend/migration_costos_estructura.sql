-- ============================================================================
-- MIGRACIÓN: Actualizar estructura de tabla costos
-- ============================================================================
-- Fecha: 21/01/2026
-- Propósito: Agregar campos 'tipo' y 'observacion' para sincronizar con Google Sheets
--
-- EJECUTAR EN SUPABASE SQL EDITOR
-- ============================================================================

-- 1. Agregar columnas nuevas a la tabla costos
ALTER TABLE costos 
ADD COLUMN IF NOT EXISTS tipo VARCHAR(50),
ADD COLUMN IF NOT EXISTS observacion TEXT;

-- 2. Crear índice para búsquedas por tipo
CREATE INDEX IF NOT EXISTS idx_costos_tipo ON costos(tipo);

-- 3. Actualizar costos existentes con valores por defecto
UPDATE costos 
SET tipo = 'Variable', 
    observacion = 'Migrado automáticamente'
WHERE tipo IS NULL;

-- 4. OPCIONAL: Limpiar datos antiguos y cargar costos reales de Enero 2026
-- NOTA: Descomentar solo si quieres eliminar costos de prueba

-- DELETE FROM costos WHERE created_at >= '2026-01-01' AND created_at < '2026-02-01';

-- 5. Insertar costos reales de Enero 2026 (según Google Sheets)
INSERT INTO costos (nombre, monto_usd, tipo, observacion, created_at)
VALUES 
  ('Agustin', 605, 'Variable', 'Operatividad', '2026-01-15T10:00:00Z'),
  ('Juana', 267, 'Fijo', 'ARS Fijo', '2026-01-15T10:00:00Z'),
  ('Maxi', 253, 'Fijo', 'Pago Semanal', '2026-01-15T10:00:00Z'),
  ('Yazmin', 133, 'Fijo', 'ARS Fijo', '2026-01-15T10:00:00Z')
ON CONFLICT DO NOTHING;

-- 6. Verificar que el total suma $1,258 USD
SELECT 
  SUM(monto_usd) as total_costos,
  COUNT(*) as cantidad_costos
FROM costos 
WHERE created_at >= '2026-01-01' 
  AND created_at < '2026-02-01';

-- 7. Ver costos agrupados por tipo
SELECT 
  tipo,
  COUNT(*) as cantidad,
  SUM(monto_usd) as total_usd
FROM costos 
WHERE created_at >= '2026-01-01' 
  AND created_at < '2026-02-01'
GROUP BY tipo
ORDER BY total_usd DESC;

-- ============================================================================
-- RESULTADO ESPERADO:
-- Total costos: $1,258 USD
-- 
-- Por tipo:
-- - Variable: $605 (Agustin)
-- - Fijo: $653 (Juana + Maxi + Yazmin)
-- ============================================================================
