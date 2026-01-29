#!/usr/bin/env python3
"""
Snapshot Manager - BLACK INFRASTRUCTURE
========================================
Gestiona snapshots mensuales de saldos PST.NET para preservar historia financiera.

Autor: Senior Backend Developer
Fecha: 28/01/2026
Versión: v106.0

FUNCIONALIDAD:
- Tomar snapshot del mes anterior (cierre de mes)
- Obtener snapshot de un periodo específico
- Listar todos los snapshots históricos
- Verificar si existe snapshot para un periodo

USO:
- Manual: python snapshot_manager.py
- API: POST /snapshot-mes-anterior
- Cron: Ejecutar el día 1 de cada mes a las 02:00 AM
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def tomar_snapshot_mes_anterior() -> Dict:
    """
    Toma un snapshot del mes anterior con los valores actuales de PST.NET.
    
    Returns:
        dict: Resultado con success, periodo, y datos del snapshot
    """
    print(f"\n{'='*60}")
    print(f"📸 TOMANDO SNAPSHOT DEL MES ANTERIOR")
    print(f"{'='*60}\n")
    
    try:
        # Verificar configuración de Supabase
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            error_msg = "Supabase no está configurado correctamente"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Calcular periodo anterior (mes que acaba de cerrar)
        fecha_anterior = datetime.now() - timedelta(days=30)
        anio_anterior = fecha_anterior.year
        mes_anterior = fecha_anterior.month
        periodo_anterior = f"{str(mes_anterior).zfill(2)}-{anio_anterior}"
        
        print(f"📅 Periodo a fotografiar: {periodo_anterior}")
        
        # Verificar si ya existe snapshot para este periodo
        result_check = supabase.table('historial_saldos').select('id').eq('periodo', periodo_anterior).execute()
        
        if result_check.data and len(result_check.data) > 0:
            print(f"⚠️  Ya existe un snapshot para el periodo {periodo_anterior}")
            return {
                'success': True,
                'periodo': periodo_anterior,
                'message': f'Snapshot ya existe para {periodo_anterior}',
                'already_exists': True
            }
        
        # Obtener valores actuales de configuración
        print(f"\n💾 Obteniendo valores actuales de configuración...")
        
        # 1. Balance neto (50% de cuentas)
        result_neto = supabase.table('configuracion').select('valor_numerico').eq('clave', 'pst_balance_neto').single().execute()
        neto_reparto = float(result_neto.data['valor_numerico']) if result_neto.data else 0.0
        
        # Calcular balance total de cuentas (neto * 2)
        balance_cuentas_total = neto_reparto * 2
        
        # 2. Cashback aprobado
        result_aprobado = supabase.table('configuracion').select('valor_numerico').eq('clave', 'pst_cashback_aprobado').single().execute()
        cashback_aprobado = float(result_aprobado.data['valor_numerico']) if result_aprobado.data else 0.0
        
        # 3. Cashback hold
        result_hold = supabase.table('configuracion').select('valor_numerico').eq('clave', 'pst_cashback_hold').single().execute()
        cashback_hold = float(result_hold.data['valor_numerico']) if result_hold.data else 0.0
        
        print(f"   💰 Balance cuentas (ID 15+2): ${balance_cuentas_total:,.2f}")
        print(f"   💰 Neto reparto (50%): ${neto_reparto:,.2f}")
        print(f"   🎁 Cashback aprobado: ${cashback_aprobado:,.2f}")
        print(f"   🔒 Cashback hold: ${cashback_hold:,.2f}")
        
        # Insertar snapshot
        print(f"\n📸 Creando snapshot...")
        
        snapshot_data = {
            'periodo': periodo_anterior,
            'anio': anio_anterior,
            'mes': mes_anterior,
            'balance_cuentas_total': balance_cuentas_total,
            'neto_reparto': neto_reparto,
            'cashback_aprobado': cashback_aprobado,
            'cashback_hold': cashback_hold,
            'fecha_snapshot': datetime.now().isoformat(),
            'notas': 'Snapshot automático de cierre de mes'
        }
        
        result_insert = supabase.table('historial_saldos').insert(snapshot_data).execute()
        
        print(f"✅ Snapshot creado exitosamente para periodo {periodo_anterior}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'periodo': periodo_anterior,
            'snapshot': snapshot_data,
            'message': f'Snapshot creado exitosamente para {periodo_anterior}'
        }
        
    except Exception as e:
        error_msg = f"Error al crear snapshot: {str(e)}"
        print(f"\n❌ {error_msg}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': error_msg
        }


def obtener_snapshot(periodo: str) -> Optional[Dict]:
    """
    Obtiene el snapshot de un periodo específico.
    
    Args:
        periodo: Periodo en formato MM-YYYY (ej: '12-2025')
    
    Returns:
        dict: Datos del snapshot o None si no existe
    """
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return None
        
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        result = supabase.table('historial_saldos').select('*').eq('periodo', periodo).single().execute()
        
        if result.data:
            return result.data
        
        return None
        
    except Exception as e:
        print(f"Error al obtener snapshot: {e}")
        return None


def listar_snapshots() -> List[Dict]:
    """
    Lista todos los snapshots disponibles, ordenados por fecha descendente.
    
    Returns:
        list: Lista de snapshots
    """
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return []
        
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        result = supabase.table('historial_saldos').select('*').order('anio', desc=True).order('mes', desc=True).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error al listar snapshots: {e}")
        return []


def verificar_snapshot_existe(periodo: str) -> bool:
    """
    Verifica si existe un snapshot para un periodo.
    
    Args:
        periodo: Periodo en formato MM-YYYY
    
    Returns:
        bool: True si existe, False si no
    """
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return False
        
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        result = supabase.table('historial_saldos').select('id').eq('periodo', periodo).execute()
        
        return result.data and len(result.data) > 0
        
    except Exception as e:
        print(f"Error al verificar snapshot: {e}")
        return False


# ============================================================================
# SCRIPT DE PRUEBA
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 TEST - Snapshot Manager\n")
    
    # Opción 1: Tomar snapshot del mes anterior
    print("1️⃣  Tomando snapshot del mes anterior...")
    resultado = tomar_snapshot_mes_anterior()
    
    print("\n" + "="*60)
    print("📋 RESULTADO:")
    print("="*60)
    print(f"Success: {resultado.get('success')}")
    print(f"Periodo: {resultado.get('periodo')}")
    print(f"Message: {resultado.get('message')}")
    
    if resultado.get('snapshot'):
        snapshot = resultado['snapshot']
        print(f"\nDatos del snapshot:")
        print(f"  Balance cuentas: ${snapshot.get('balance_cuentas_total', 0):,.2f}")
        print(f"  Neto reparto (50%): ${snapshot.get('neto_reparto', 0):,.2f}")
        print(f"  Cashback aprobado: ${snapshot.get('cashback_aprobado', 0):,.2f}")
        print(f"  Cashback hold: ${snapshot.get('cashback_hold', 0):,.2f}")
    
    print("="*60 + "\n")
    
    # Opción 2: Listar todos los snapshots
    print("\n2️⃣  Listando todos los snapshots...")
    snapshots = listar_snapshots()
    
    if snapshots:
        print(f"\n📊 {len(snapshots)} snapshot(s) encontrado(s):\n")
        for snap in snapshots:
            print(f"  📸 {snap['periodo']}")
            print(f"     Neto: ${snap['neto_reparto']:,.2f}")
            print(f"     Fecha: {snap['fecha_snapshot']}")
            print()
    else:
        print("⚠️  No se encontraron snapshots")
    
    print("="*60 + "\n")
