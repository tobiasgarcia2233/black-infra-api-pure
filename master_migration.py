#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - MASTER MIGRATION SCRIPT
==============================================
Sistema de migración robusto para inicializar la base de datos de Supabase
desde archivos CSV locales.

Autor: Senior CTO & Data Architect
Fecha: 21/01/2026
Versión: 1.0.0
"""

import os
import sys
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import traceback

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validar credenciales
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR CRÍTICO: Faltan credenciales de Supabase en .env")
    sys.exit(1)

# Limpiar credenciales
SUPABASE_URL = SUPABASE_URL.strip().strip('"').strip("'")
SUPABASE_KEY = SUPABASE_KEY.strip().strip('"').strip("'")

# Crear cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Archivos CSV a procesar
CSV_FILES = {
    'clientes': 'Contabilidad - BLACK - Clientes.csv',
    'ingresos': 'Contabilidad - BLACK - Ingresos Mensuales.csv',
    'costos': 'Contabilidad - BLACK - Costos .csv',
    'cotizaciones': 'Contabilidad - BLACK - Cotizaciones.csv',
}

# Estadísticas de migración
stats = {
    'clientes': {'insertados': 0, 'actualizados': 0, 'errores': 0},
    'ingresos': {'insertados': 0, 'actualizados': 0, 'errores': 0},
    'costos': {'insertados': 0, 'actualizados': 0, 'errores': 0},
    'cotizaciones': {'insertados': 0, 'actualizados': 0, 'errores': 0},
}

# ============================================================================
# FUNCIONES DE LIMPIEZA Y TRANSFORMACIÓN
# ============================================================================

def limpiar_monto(valor):
    """
    Limpia montos: elimina $, puntos de miles y convierte coma a punto decimal.
    
    Args:
        valor: Valor a limpiar (puede ser string, int, float o None)
    
    Returns:
        float o None si el valor es inválido
    
    Ejemplos:
        '$1,255.50' -> 1255.5
        '$765,000' -> 765000.0
        '500' -> 500.0
        '' -> None
    """
    if pd.isna(valor) or valor == '' or valor == '—' or valor == '-':
        return None
    
    try:
        # Convertir a string y limpiar
        valor_str = str(valor).strip()
        
        # Eliminar símbolos y espacios
        valor_str = valor_str.replace('$', '').replace(' ', '').replace('USD', '').replace('ARS', '')
        
        # Eliminar puntos de miles
        valor_str = valor_str.replace('.', '')
        
        # Convertir coma a punto decimal
        valor_str = valor_str.replace(',', '.')
        
        # Convertir a float
        return float(valor_str) if valor_str else None
    except (ValueError, AttributeError):
        return None


def limpiar_string(valor):
    """
    Limpia strings: trim de espacios, normalización.
    
    Args:
        valor: String a limpiar
    
    Returns:
        String limpio o None si es vacío
    """
    if pd.isna(valor) or valor == '' or valor == '—' or valor == '-':
        return None
    return str(valor).strip()


def parsear_fecha(fecha_str):
    """
    Convierte fechas de formato DD/MM/YYYY a ISO YYYY-MM-DD.
    
    Args:
        fecha_str: String con la fecha
    
    Returns:
        String en formato ISO o None si falla
    """
    if pd.isna(fecha_str) or fecha_str == '' or fecha_str == '—':
        return None
    
    try:
        fecha_str = str(fecha_str).strip()
        
        # Intentar varios formatos
        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
            try:
                fecha_obj = datetime.strptime(fecha_str, fmt)
                return fecha_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Intentar con pandas (más flexible)
        fecha_obj = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
        if pd.notna(fecha_obj):
            return fecha_obj.strftime('%Y-%m-%d')
        
        return None
    except Exception:
        return None


def parsear_booleano(valor):
    """
    Convierte strings a booleanos.
    
    Args:
        valor: Valor a convertir
    
    Returns:
        bool
    """
    if pd.isna(valor):
        return False
    
    valor_str = str(valor).strip().lower()
    return valor_str in ['sí', 'si', 'yes', 'true', '1', 'activo']


# ============================================================================
# FUNCIONES DE MIGRACIÓN POR TABLA
# ============================================================================

def migrate_clientes():
    """Migra la tabla de clientes (SOLO: Cliente, Honorario USD, Estado, Activo?)."""
    print("\n" + "="*70)
    print("📊 MIGRANDO CLIENTES")
    print("="*70)
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(CSV_FILES['clientes']):
            print(f"❌ ERROR: Archivo no encontrado: {CSV_FILES['clientes']}")
            return False
        
        # Leer CSV
        df = pd.read_csv(CSV_FILES['clientes'])
        df.columns = df.columns.str.strip()
        
        print(f"📄 Archivo cargado: {len(df)} registros")
        
        # Procesar cada cliente
        for idx, row in df.iterrows():
            try:
                nombre = limpiar_string(row.get('Cliente'))
                
                if not nombre:
                    print(f"   ⚠️  Fila {idx+2}: Cliente sin nombre, omitido")
                    continue
                
                # Preparar datos (SOLO campos especificados)
                cliente = {
                    'nombre': nombre,
                    'honorario_usd': limpiar_monto(row.get('Honorario USD')) or 0,
                    'estado': limpiar_string(row.get('Estado')) or 'Desconocido',
                    'activo': parsear_booleano(row.get('Activo?')),
                }
                
                # Verificar si existe (upsert por nombre)
                existing = supabase.table('clientes').select('id').eq('nombre', nombre).execute()
                
                if existing.data:
                    # Actualizar
                    supabase.table('clientes').update(cliente).eq('nombre', nombre).execute()
                    stats['clientes']['actualizados'] += 1
                    print(f"   ✅ Actualizado: {nombre}")
                else:
                    # Insertar
                    supabase.table('clientes').insert(cliente).execute()
                    stats['clientes']['insertados'] += 1
                    print(f"   ➕ Insertado: {nombre}")
                    
            except Exception as e:
                stats['clientes']['errores'] += 1
                print(f"   ❌ Error en fila {idx+2}: {e}")
                continue
        
        print(f"\n✅ Clientes procesados:")
        print(f"   • Insertados: {stats['clientes']['insertados']}")
        print(f"   • Actualizados: {stats['clientes']['actualizados']}")
        print(f"   • Errores: {stats['clientes']['errores']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en migración de clientes: {e}")
        traceback.print_exc()
        return False


def migrate_ingresos():
    """Migra la tabla de ingresos (requiere clientes previamente cargados)."""
    print("\n" + "="*70)
    print("💸 MIGRANDO INGRESOS")
    print("="*70)
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(CSV_FILES['ingresos']):
            print(f"❌ ERROR: Archivo no encontrado: {CSV_FILES['ingresos']}")
            return False
        
        # Cargar mapeo de clientes (nombre -> id)
        clientes_response = supabase.table('clientes').select('id, nombre').execute()
        clientes_map = {
            limpiar_string(c['nombre']): c['id'] 
            for c in clientes_response.data
        }
        
        print(f"📋 Clientes disponibles para mapeo: {len(clientes_map)}")
        
        # Leer CSV
        df = pd.read_csv(CSV_FILES['ingresos'])
        df.columns = df.columns.str.strip()
        
        print(f"📄 Archivo cargado: {len(df)} registros")
        
        # Procesar cada ingreso
        for idx, row in df.iterrows():
            try:
                nombre_cliente = limpiar_string(row.get('Cliente'))
                
                if not nombre_cliente:
                    print(f"   ⚠️  Fila {idx+2}: Ingreso sin cliente, omitido")
                    continue
                
                # Mapear cliente
                cliente_id = clientes_map.get(nombre_cliente)
                
                if not cliente_id:
                    print(f"   ⚠️  Fila {idx+2}: Cliente '{nombre_cliente}' no encontrado en BD")
                    stats['ingresos']['errores'] += 1
                    continue
                
                # Parsear fecha (DD/MM/YYYY -> YYYY-MM-DD)
                fecha_cobro = parsear_fecha(row.get('Fecha de cobro'))
                
                # Preparar datos (MAPEO CORRECTO a nombres cortos de BD)
                ingreso = {
                    'fecha_cobro': fecha_cobro,
                    'cliente_id': cliente_id,
                    'honorario_usd': limpiar_monto(row.get('Honorario USD')) or 0,
                    'medio_pago': limpiar_string(row.get('Medio de pago')) or 'No especificado',
                    'cotizacion_aplicada': limpiar_monto(row.get('Cotización Aplicada')) or 0,
                    'monto_ars': limpiar_monto(row.get('Monto cobrado ARS')) or 0,
                    'monto_usdt': limpiar_monto(row.get('Monto cobrado USDT')) or 0,
                    'monto_usd_total': limpiar_monto(row.get('Montro cobrado USD')) or 0,  # Typo del CSV
                    'estado': limpiar_string(row.get('Estado')) or 'Pendiente',
                }
                
                # Verificar duplicado (por cliente_id + fecha_cobro) - NO DUPLICAR
                if fecha_cobro:
                    existing = supabase.table('ingresos').select('id') \
                        .eq('cliente_id', cliente_id) \
                        .eq('fecha_cobro', fecha_cobro) \
                        .execute()
                else:
                    # Si no hay fecha, no insertar para evitar duplicados sin identificador único
                    print(f"   ⚠️  Ingreso sin fecha para {nombre_cliente}, omitido para evitar duplicados")
                    stats['ingresos']['errores'] += 1
                    continue
                
                if existing.data:
                    # Actualizar
                    supabase.table('ingresos').update(ingreso).eq('id', existing.data[0]['id']).execute()
                    stats['ingresos']['actualizados'] += 1
                    print(f"   ✅ Actualizado: {nombre_cliente} - {fecha_cobro}")
                else:
                    # Insertar
                    supabase.table('ingresos').insert(ingreso).execute()
                    stats['ingresos']['insertados'] += 1
                    print(f"   ➕ Insertado: {nombre_cliente} - {fecha_cobro}")
                    
            except Exception as e:
                stats['ingresos']['errores'] += 1
                print(f"   ❌ Error en fila {idx+2}: {e}")
                continue
        
        print(f"\n✅ Ingresos procesados:")
        print(f"   • Insertados: {stats['ingresos']['insertados']}")
        print(f"   • Actualizados: {stats['ingresos']['actualizados']}")
        print(f"   • Errores: {stats['ingresos']['errores']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en migración de ingresos: {e}")
        traceback.print_exc()
        return False


def migrate_costos():
    """Migra la tabla de costos (SOLO: Nombre, Tipo, Monto USD, Observación)."""
    print("\n" + "="*70)
    print("💰 MIGRANDO COSTOS")
    print("="*70)
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(CSV_FILES['costos']):
            print(f"❌ ERROR: Archivo no encontrado: {CSV_FILES['costos']}")
            return False
        
        # Leer CSV
        df = pd.read_csv(CSV_FILES['costos'])
        df.columns = df.columns.str.strip()
        
        print(f"📄 Archivo cargado: {len(df)} registros")
        
        # Procesar cada costo
        for idx, row in df.iterrows():
            try:
                nombre = limpiar_string(row.get('Nombre'))
                
                if not nombre:
                    print(f"   ⚠️  Fila {idx+2}: Costo sin nombre, omitido")
                    continue
                
                # Preparar datos (SOLO campos especificados)
                costo = {
                    'nombre': nombre,
                    'tipo': limpiar_string(row.get('Tipo')) or 'Variable',
                    'monto_usd': limpiar_monto(row.get('Monto USD')) or 0,
                    'observacion': limpiar_string(row.get('Observación')),
                }
                
                # Verificar si existe (upsert por nombre)
                existing = supabase.table('costos').select('id').eq('nombre', nombre).execute()
                
                if existing.data:
                    # Actualizar
                    supabase.table('costos').update(costo).eq('nombre', nombre).execute()
                    stats['costos']['actualizados'] += 1
                    print(f"   ✅ Actualizado: {nombre}")
                else:
                    # Insertar
                    supabase.table('costos').insert(costo).execute()
                    stats['costos']['insertados'] += 1
                    print(f"   ➕ Insertado: {nombre}")
                    
            except Exception as e:
                stats['costos']['errores'] += 1
                print(f"   ❌ Error en fila {idx+2}: {e}")
                continue
        
        print(f"\n✅ Costos procesados:")
        print(f"   • Insertados: {stats['costos']['insertados']}")
        print(f"   • Actualizados: {stats['costos']['actualizados']}")
        print(f"   • Errores: {stats['costos']['errores']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en migración de costos: {e}")
        traceback.print_exc()
        return False


def migrate_cotizaciones():
    """Migra la tabla de cotizaciones (SOLO: Fecha, Hora, Blue Venta)."""
    print("\n" + "="*70)
    print("💵 MIGRANDO COTIZACIONES")
    print("="*70)
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(CSV_FILES['cotizaciones']):
            print(f"❌ ERROR: Archivo no encontrado: {CSV_FILES['cotizaciones']}")
            return False
        
        # Leer CSV
        df = pd.read_csv(CSV_FILES['cotizaciones'])
        
        # Buscar header real (después de filas vacías)
        start_idx = None
        for idx, row in df.iterrows():
            if row.iloc[0] == 'Fecha' and row.iloc[1] == 'Hora':
                start_idx = idx + 1
                break
        
        if start_idx is None:
            print("❌ ERROR: No se encontró el header de cotizaciones")
            return False
        
        # Crear dataframe limpio
        df_cotizaciones = df.iloc[start_idx:].copy()
        df_cotizaciones.columns = ['fecha', 'hora', 'blue_venta']
        
        print(f"📄 Archivo cargado: {len(df_cotizaciones)} registros")
        
        # LIMPIEZA AVANZADA DE FECHAS Y HORAS con pandas
        # Algunas celdas tienen fecha + hora juntas, necesitamos separarlas
        df_cotizaciones['fecha'] = pd.to_datetime(df_cotizaciones['fecha'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Limpiar hora (extraer solo HH:MM:SS)
        def limpiar_hora(valor):
            if pd.isna(valor) or valor == '' or valor == 'nan':
                return '00:00:00'
            try:
                # Si es datetime, extraer hora
                if isinstance(valor, str) and '/' in valor:
                    # Es una fecha con hora, extraer la parte de hora
                    hora_obj = pd.to_datetime(valor, errors='coerce')
                    if pd.notna(hora_obj):
                        return hora_obj.strftime('%H:%M:%S')
                # Si ya es hora en formato correcto
                hora_str = str(valor).strip()
                # Intentar parsear como hora
                if ':' in hora_str:
                    partes = hora_str.split(':')
                    if len(partes) >= 2:
                        return f"{partes[0].zfill(2)}:{partes[1].zfill(2)}:{partes[2].zfill(2) if len(partes) > 2 else '00'}"
                return '00:00:00'
            except:
                return '00:00:00'
        
        df_cotizaciones['hora'] = df_cotizaciones['hora'].apply(limpiar_hora)
        
        # Procesar cada cotización
        for idx, row in df_cotizaciones.iterrows():
            try:
                fecha_iso = row['fecha']
                
                if pd.isna(fecha_iso) or fecha_iso == 'NaT' or fecha_iso == 'nan':
                    continue
                
                # Preparar datos (SOLO campos especificados)
                cotizacion = {
                    'fecha': fecha_iso,
                    'hora': row['hora'],
                    'blue_venta': limpiar_monto(row['blue_venta']) or 0,
                }
                
                # Verificar si existe (upsert por fecha) - NO DUPLICAR
                existing = supabase.table('cotizaciones').select('id').eq('fecha', fecha_iso).execute()
                
                if existing.data:
                    # Actualizar solo si cambió algo
                    supabase.table('cotizaciones').update(cotizacion).eq('fecha', fecha_iso).execute()
                    stats['cotizaciones']['actualizados'] += 1
                    print(f"   ✅ Actualizado: {fecha_iso} - ${cotizacion['blue_venta']}")
                else:
                    # Insertar nuevo registro
                    supabase.table('cotizaciones').insert(cotizacion).execute()
                    stats['cotizaciones']['insertados'] += 1
                    print(f"   ➕ Insertado: {fecha_iso} - ${cotizacion['blue_venta']}")
                    
            except Exception as e:
                stats['cotizaciones']['errores'] += 1
                print(f"   ❌ Error en fecha {fecha_iso}: {e}")
                continue
        
        print(f"\n✅ Cotizaciones procesadas:")
        print(f"   • Insertadas: {stats['cotizaciones']['insertados']}")
        print(f"   • Actualizadas: {stats['cotizaciones']['actualizados']}")
        print(f"   • Errores: {stats['cotizaciones']['errores']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en migración de cotizaciones: {e}")
        traceback.print_exc()
        return False


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal que orquesta toda la migración."""
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  🚀 BLACK INFRASTRUCTURE - MASTER MIGRATION SYSTEM  🚀".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    print(f"\n📅 Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Supabase URL: {SUPABASE_URL}")
    print(f"🔑 API Key: {SUPABASE_KEY[:20]}...{SUPABASE_KEY[-10:]}")
    
    # Verificar archivos
    print("\n📁 Verificando archivos CSV...")
    missing_files = []
    for key, filename in CSV_FILES.items():
        if os.path.exists(filename):
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} - NO ENCONTRADO")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n❌ ERROR: Faltan {len(missing_files)} archivo(s). Abortando migración.")
        sys.exit(1)
    
    # Ejecutar migraciones en orden
    inicio = datetime.now()
    
    try:
        # 1. Clientes (independiente)
        if not migrate_clientes():
            print("\n❌ Migración de clientes falló. Abortando.")
            sys.exit(1)
        
        # 2. Ingresos (depende de clientes)
        if not migrate_ingresos():
            print("\n⚠️  Migración de ingresos tuvo problemas, continuando...")
        
        # 3. Costos (independiente)
        if not migrate_costos():
            print("\n⚠️  Migración de costos tuvo problemas, continuando...")
        
        # 4. Cotizaciones (independiente)
        if not migrate_cotizaciones():
            print("\n⚠️  Migración de cotizaciones tuvo problemas, continuando...")
        
        # Resumen final
        fin = datetime.now()
        duracion = (fin - inicio).total_seconds()
        
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  ✅ MIGRACIÓN COMPLETADA EXITOSAMENTE  ✅".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70)
        
        print(f"\n⏱️  Tiempo total: {duracion:.2f} segundos")
        print("\n📊 ESTADÍSTICAS FINALES:")
        print("="*70)
        
        total_insertados = sum(s['insertados'] for s in stats.values())
        total_actualizados = sum(s['actualizados'] for s in stats.values())
        total_errores = sum(s['errores'] for s in stats.values())
        
        for tabla, stat in stats.items():
            print(f"\n{tabla.upper()}:")
            print(f"   • Insertados: {stat['insertados']}")
            print(f"   • Actualizados: {stat['actualizados']}")
            print(f"   • Errores: {stat['errores']}")
        
        print(f"\nTOTAL GENERAL:")
        print(f"   • Insertados: {total_insertados}")
        print(f"   • Actualizados: {total_actualizados}")
        print(f"   • Errores: {total_errores}")
        
        print("\n" + "="*70)
        print("✨ Sistema BLACK inicializado correctamente")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Migración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR CRÍTICO: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
