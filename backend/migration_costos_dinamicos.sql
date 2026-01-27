-- ============================================================================
-- MIGRACIÓN: Costos Dinámicos con ARS y Configuración de Dólar
-- ============================================================================
-- Fecha: 21/01/2026
-- Propósito: Implementar costos dinámicos con conversión ARS→USD
--
-- EJECUTAR EN SUPABASE SQL EDITOR
-- ============================================================================

-- 1. Crear tabla de configuración para valores del sistema
CREATE TABLE IF NOT EXISTS configuracion (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clave VARCHAR(100) UNIQUE NOT NULL,
  valor_texto TEXT,
  valor_numerico DECIMAL(10, 2),
  descripcion TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Insertar valor del dólar en configuración
INSERT INTO configuracion (clave, valor_numerico, descripcion)
VALUES ('dolar_conversion', 1500.00, 'Valor del dólar para conversión de costos ARS a USD')
ON CONFLICT (clave) DO UPDATE 
SET valor_numerico = 1500.00, updated_at = NOW();

-- 3. Insertar valor de honorario por cliente (Agustín)
INSERT INTO configuracion (clave, valor_numerico, descripcion)
VALUES ('honorario_por_cliente', 55.00, 'Honorario en USD por cliente activo (Agustín)')
ON CONFLICT (clave) DO UPDATE 
SET valor_numerico = 55.00, updated_at = NOW();

-- 4. Actualizar tabla costos para incluir campos de ARS
ALTER TABLE costos 
ADD COLUMN IF NOT EXISTS monto_ars DECIMAL(12, 2),
ADD COLUMN IF NOT EXISTS es_calculo_dinamico BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS formula VARCHAR(255);

-- 5. LIMPIEZA: Borrar TODOS los costos existentes
DELETE FROM costos;

-- 6. Recrear costos con la nueva lógica

-- 6.1 Juana (ARS Fijo)
INSERT INTO costos (nombre, monto_ars, monto_usd, tipo, observacion, es_calculo_dinamico, created_at)
VALUES (
  'Juana',
  400000.00,
  ROUND(400000.00 / (SELECT valor_numerico FROM configuracion WHERE clave = 'dolar_conversion'), 2),
  'Fijo',
  'ARS Fijo - Administrativo',
  false,
  '2026-01-15T10:00:00Z'
);

-- 6.2 Yazmin (ARS Fijo)
INSERT INTO costos (nombre, monto_ars, monto_usd, tipo, observacion, es_calculo_dinamico, created_at)
VALUES (
  'Yazmin',
  200000.00,
  ROUND(200000.00 / (SELECT valor_numerico FROM configuracion WHERE clave = 'dolar_conversion'), 2),
  'Fijo',
  'ARS Fijo - Soporte',
  false,
  '2026-01-15T10:00:00Z'
);

-- 6.3 Maxi (ARS Semanal → Mensual)
-- $87,500 ARS semanales × 4 semanas = $350,000 ARS/mes
INSERT INTO costos (nombre, monto_ars, monto_usd, tipo, observacion, es_calculo_dinamico, created_at)
VALUES (
  'Maxi',
  350000.00,
  ROUND(350000.00 / (SELECT valor_numerico FROM configuracion WHERE clave = 'dolar_conversion'), 2),
  'Fijo',
  'Pago Semanal ($87,500 × 4)',
  false,
  '2026-01-15T10:00:00Z'
);

-- 6.4 Agustín (Dinámico - calculado por clientes activos)
-- NOTA: Este registro es un placeholder. El monto real se calcula dinámicamente
-- en el código Python basado en: (cantidad_clientes_activos × $55 USD)
INSERT INTO costos (nombre, monto_ars, monto_usd, tipo, observacion, es_calculo_dinamico, formula, created_at)
VALUES (
  'Agustin',
  NULL,
  0.00,  -- Se calculará dinámicamente
  'Variable',
  'Calculado: Clientes Activos × $55 USD',
  true,
  'clientes_activos * 55',
  '2026-01-15T10:00:00Z'
);

-- 7. Crear vista para costos con conversión actualizada
CREATE OR REPLACE VIEW vista_costos_calculados AS
SELECT 
  c.id,
  c.nombre,
  c.tipo,
  c.observacion,
  c.monto_ars,
  CASE 
    WHEN c.es_calculo_dinamico = false AND c.monto_ars IS NOT NULL THEN
      ROUND(c.monto_ars / conf.valor_numerico, 2)
    ELSE
      c.monto_usd
  END as monto_usd_calculado,
  c.es_calculo_dinamico,
  c.formula,
  c.created_at,
  conf.valor_numerico as dolar_actual
FROM costos c
CROSS JOIN (SELECT valor_numerico FROM configuracion WHERE clave = 'dolar_conversion') conf;

-- 8. Verificar resultados
SELECT 
  nombre,
  tipo,
  monto_ars,
  monto_usd,
  observacion,
  es_calculo_dinamico
FROM costos
ORDER BY tipo DESC, nombre;

-- 9. Ver totales calculados
SELECT 
  tipo,
  SUM(
    CASE 
      WHEN monto_ars IS NOT NULL THEN 
        ROUND(monto_ars / (SELECT valor_numerico FROM configuracion WHERE clave = 'dolar_conversion'), 2)
      ELSE 
        monto_usd
    END
  ) as total_usd
FROM costos
WHERE es_calculo_dinamico = false
GROUP BY tipo;

-- 10. Ver configuración
SELECT * FROM configuracion;

-- ============================================================================
-- RESULTADO ESPERADO:
-- 
-- Configuración:
-- - dolar_conversion: 1500.00
-- - honorario_por_cliente: 55.00
--
-- Costos Fijos (con conversión ARS→USD a $1,500):
-- - Juana: $400,000 ARS = $266.67 USD
-- - Yazmin: $200,000 ARS = $133.33 USD
-- - Maxi: $350,000 ARS = $233.33 USD
-- Total Fijos: $633.33 USD
--
-- Costos Variables (dinámico):
-- - Agustín: Se calcula en código Python
--   Fórmula: clientes_activos × $55 USD
--   Ejemplo: 11 clientes × $55 = $605 USD
--
-- TOTAL ESTIMADO: ~$1,238 USD (depende de clientes activos)
-- ============================================================================
