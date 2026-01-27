-- ============================================================================
-- MIGRACIÓN: Gestión Avanzada de Clientes
-- ============================================================================
-- Fecha: 21/01/2026
-- Propósito: Añadir control de estado, fee mensual y comisión de Agustín
--
-- EJECUTAR EN SUPABASE SQL EDITOR
-- ============================================================================

-- 1. Añadir nuevas columnas a la tabla clientes
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS estado VARCHAR(50) DEFAULT 'Activo',
ADD COLUMN IF NOT EXISTS fee_mensual DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS comisiona_agustin BOOLEAN DEFAULT true;

-- 2. Migrar datos existentes del campo 'activo' al campo 'estado'
UPDATE clientes 
SET estado = CASE 
  WHEN activo = true THEN 'Activo'
  ELSE 'Inactivo'
END
WHERE estado = 'Activo'; -- Solo actualizar los que tienen el valor default

-- 3. Actualizar fee_mensual con el valor de honorario_usd si existe
UPDATE clientes 
SET fee_mensual = honorario_usd
WHERE fee_mensual IS NULL AND honorario_usd IS NOT NULL;

-- 4. Crear índices para mejorar performance de consultas
CREATE INDEX IF NOT EXISTS idx_clientes_estado ON clientes(estado);
CREATE INDEX IF NOT EXISTS idx_clientes_comisiona_agustin ON clientes(comisiona_agustin);

-- 5. Crear vista para clientes activos con comisión
CREATE OR REPLACE VIEW vista_clientes_activos_comision AS
SELECT 
  id,
  nombre,
  estado,
  fee_mensual,
  comisiona_agustin,
  honorario_usd,
  activo
FROM clientes
WHERE estado = 'Activo' AND comisiona_agustin = true;

-- 6. Crear vista para resumen de clientes
CREATE OR REPLACE VIEW vista_resumen_clientes AS
SELECT 
  COUNT(*) FILTER (WHERE estado = 'Activo') as clientes_activos,
  COUNT(*) FILTER (WHERE estado = 'Activo' AND comisiona_agustin = true) as clientes_con_comision,
  SUM(fee_mensual) FILTER (WHERE estado = 'Activo') as ingresos_proyectados,
  COUNT(*) FILTER (WHERE estado = 'Activo' AND comisiona_agustin = true) * 55.00 as costo_agustin
FROM clientes;

-- 7. Verificar resultados
SELECT 
  nombre,
  estado,
  fee_mensual,
  comisiona_agustin,
  honorario_usd,
  activo
FROM clientes
ORDER BY estado DESC, nombre;

-- 8. Ver resumen
SELECT * FROM vista_resumen_clientes;

-- ============================================================================
-- RESULTADO ESPERADO:
-- 
-- Nuevas columnas:
-- - estado: 'Activo', 'Inactivo', 'Pausado', etc.
-- - fee_mensual: Ingreso mensual por cliente (USD)
-- - comisiona_agustin: true/false si cuenta para comisión de Agustín
--
-- Cálculos:
-- - Gasto Agustín: COUNT(clientes WHERE estado='Activo' AND comisiona_agustin=true) * $55
-- - Ingresos Proyectados: SUM(fee_mensual WHERE estado='Activo')
-- ============================================================================
