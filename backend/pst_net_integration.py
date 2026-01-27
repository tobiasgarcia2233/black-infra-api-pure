#!/usr/bin/env python3
"""
PST.NET API Integration
========================
Módulo para integrar la API de PST.NET con el Sistema BLACK
Automatiza el registro de ingresos desde la plataforma de pagos

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 1.0.0
"""

import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# CONFIGURACIÓN DE PST.NET
# ============================================================================

# TODO: Obtener estos valores del usuario
PST_NET_API_URL = os.getenv("PST_NET_API_URL", "https://api.pst.net/v1")
PST_NET_API_KEY = os.getenv("PST_NET_API_KEY", "")
PST_NET_SECRET = os.getenv("PST_NET_SECRET", "")

# ============================================================================
# FUNCIONES DE INTEGRACIÓN
# ============================================================================

def get_pst_net_headers() -> Dict[str, str]:
    """
    Genera los headers necesarios para las peticiones a PST.NET
    
    Returns:
        dict: Headers con autenticación
    """
    # TODO: Adaptar según el tipo de autenticación que use PST.NET
    # Opciones comunes:
    # - API Key en header: 'Authorization': f'Bearer {PST_NET_API_KEY}'
    # - Basic Auth: requests.auth.HTTPBasicAuth(username, password)
    # - Custom header: 'X-API-Key': PST_NET_API_KEY
    
    return {
        'Authorization': f'Bearer {PST_NET_API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'BLACK-Infrastructure/1.0',
    }


def obtener_pagos_pendientes() -> List[Dict]:
    """
    Consulta los pagos pendientes de sincronizar desde PST.NET
    
    Returns:
        list: Lista de pagos pendientes
        
    Ejemplo de respuesta esperada:
    [
        {
            'id': 'pago_123',
            'cliente_id': 'cliente_abc',
            'monto': 1500.00,
            'moneda': 'USD',
            'fecha': '2026-01-15T10:30:00Z',
            'estado': 'completado'
        }
    ]
    """
    try:
        # TODO: Adaptar endpoint según documentación de PST.NET
        # Ejemplos de endpoints comunes:
        # - GET /pagos?estado=completado&sincronizado=false
        # - GET /transacciones/pendientes
        # - GET /ingresos?desde=YYYY-MM-DD
        
        endpoint = f"{PST_NET_API_URL}/pagos"
        params = {
            'estado': 'completado',
            'sincronizado': 'false',
            'limit': 100
        }
        
        print(f"🔍 Consultando pagos pendientes en PST.NET...")
        
        response = requests.get(
            endpoint,
            headers=get_pst_net_headers(),
            params=params,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # TODO: Adaptar según la estructura de respuesta de PST.NET
        # Algunas APIs devuelven { 'data': [...] }, otras directamente [...]
        pagos = data.get('data', data) if isinstance(data, dict) else data
        
        print(f"✅ {len(pagos)} pagos pendientes encontrados")
        return pagos
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al consultar PST.NET: {e}")
        return []
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return []


def marcar_pago_sincronizado(pago_id: str) -> bool:
    """
    Marca un pago como sincronizado en PST.NET
    
    Args:
        pago_id (str): ID del pago en PST.NET
        
    Returns:
        bool: True si se marcó exitosamente
    """
    try:
        # TODO: Adaptar según documentación de PST.NET
        # Ejemplos:
        # - PATCH /pagos/{id} con { 'sincronizado': true }
        # - POST /pagos/{id}/marcar-sincronizado
        # - PUT /transacciones/{id}/sync
        
        endpoint = f"{PST_NET_API_URL}/pagos/{pago_id}"
        payload = {
            'sincronizado': True,
            'sincronizado_en': datetime.now().isoformat()
        }
        
        response = requests.patch(
            endpoint,
            headers=get_pst_net_headers(),
            json=payload,
            timeout=10
        )
        
        response.raise_for_status()
        print(f"✅ Pago {pago_id} marcado como sincronizado")
        return True
        
    except Exception as e:
        print(f"⚠️ No se pudo marcar pago {pago_id} como sincronizado: {e}")
        return False


def procesar_pago_pst_net(pago: Dict, supabase_client) -> Optional[str]:
    """
    Procesa un pago de PST.NET y lo registra en Supabase
    
    Args:
        pago (dict): Datos del pago desde PST.NET
        supabase_client: Cliente de Supabase
        
    Returns:
        str: ID del ingreso creado en Supabase, o None si falla
    """
    try:
        # TODO: Mapear los campos según la estructura real de PST.NET
        
        # Extraer datos del pago (adaptar según respuesta real)
        pago_id = pago.get('id')
        cliente_id = pago.get('cliente_id')  # Debe coincidir con UUID en Supabase
        monto_usd = float(pago.get('monto', 0))
        fecha_pago = pago.get('fecha', datetime.now().isoformat())
        
        # Validaciones
        if not cliente_id:
            print(f"⚠️ Pago {pago_id} sin cliente_id, omitiendo...")
            return None
            
        if monto_usd <= 0:
            print(f"⚠️ Pago {pago_id} con monto inválido, omitiendo...")
            return None
        
        # Obtener cotización del dólar (importar desde bot_main.py)
        from bot_main import get_dolar_blue
        
        cotizacion = get_dolar_blue()
        dolar_venta = cotizacion.get('venta', 1500.0) if 'error' not in cotizacion else 1500.0
        
        # Calcular equivalente en ARS
        monto_ars = monto_usd * dolar_venta
        
        # Crear registro en Supabase
        ingreso_data = {
            'cliente_id': str(cliente_id),
            'monto_usd_total': monto_usd,
            'monto_ars': monto_ars,
            'fecha_cobro': fecha_pago.split('T')[0],  # Solo la fecha
            'created_at': datetime.now().isoformat(),
            # Campo opcional para rastrear origen
            'metadata': {
                'fuente': 'PST.NET',
                'pago_id_pst': pago_id
            }
        }
        
        # Insertar en Supabase
        response = supabase_client.table('ingresos').insert(ingreso_data).execute()
        
        if response.data and len(response.data) > 0:
            ingreso_id = response.data[0].get('id')
            print(f"✅ Ingreso creado en Supabase: {ingreso_id}")
            
            # Marcar como sincronizado en PST.NET
            marcar_pago_sincronizado(pago_id)
            
            return ingreso_id
        else:
            print(f"❌ Error al insertar ingreso en Supabase")
            return None
        
    except Exception as e:
        print(f"❌ Error al procesar pago: {e}")
        return None


def sincronizar_pagos_pst_net(supabase_client) -> Dict[str, int]:
    """
    Sincroniza todos los pagos pendientes de PST.NET a Supabase
    
    Args:
        supabase_client: Cliente de Supabase
        
    Returns:
        dict: Estadísticas de la sincronización
    """
    print("\n" + "="*60)
    print("🔄 SINCRONIZACIÓN PST.NET → SUPABASE")
    print("="*60 + "\n")
    
    # Obtener pagos pendientes
    pagos = obtener_pagos_pendientes()
    
    if not pagos:
        print("ℹ️ No hay pagos pendientes de sincronizar")
        return {
            'total': 0,
            'exitosos': 0,
            'fallidos': 0
        }
    
    # Procesar cada pago
    exitosos = 0
    fallidos = 0
    
    for idx, pago in enumerate(pagos, 1):
        print(f"\n[{idx}/{len(pagos)}] Procesando pago {pago.get('id')}...")
        
        ingreso_id = procesar_pago_pst_net(pago, supabase_client)
        
        if ingreso_id:
            exitosos += 1
        else:
            fallidos += 1
    
    # Resumen
    print("\n" + "="*60)
    print(f"✅ Sincronización completada:")
    print(f"   Total: {len(pagos)}")
    print(f"   Exitosos: {exitosos}")
    print(f"   Fallidos: {fallidos}")
    print("="*60 + "\n")
    
    return {
        'total': len(pagos),
        'exitosos': exitosos,
        'fallidos': fallidos
    }


# ============================================================================
# WEBHOOK HANDLER (Opcional - para sincronización automática)
# ============================================================================

def validar_webhook_pst_net(payload: Dict, signature: str) -> bool:
    """
    Valida que un webhook provenga realmente de PST.NET
    
    Args:
        payload (dict): Datos del webhook
        signature (str): Firma del webhook
        
    Returns:
        bool: True si la firma es válida
    """
    # TODO: Implementar validación según documentación de PST.NET
    # Ejemplo común:
    # import hmac
    # import hashlib
    # 
    # expected_signature = hmac.new(
    #     PST_NET_SECRET.encode(),
    #     json.dumps(payload).encode(),
    #     hashlib.sha256
    # ).hexdigest()
    # 
    # return hmac.compare_digest(signature, expected_signature)
    
    return True  # Placeholder


def procesar_webhook_pst_net(payload: Dict, supabase_client) -> bool:
    """
    Procesa un webhook de PST.NET (pago recibido en tiempo real)
    
    Args:
        payload (dict): Datos del webhook
        supabase_client: Cliente de Supabase
        
    Returns:
        bool: True si se procesó exitosamente
    """
    try:
        # TODO: Adaptar según estructura de webhook de PST.NET
        evento = payload.get('event', 'pago.completado')
        
        if evento == 'pago.completado':
            pago = payload.get('data', {})
            ingreso_id = procesar_pago_pst_net(pago, supabase_client)
            return ingreso_id is not None
        
        return False
        
    except Exception as e:
        print(f"❌ Error al procesar webhook: {e}")
        return False


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def verificar_configuracion_pst_net() -> bool:
    """
    Verifica que las credenciales de PST.NET estén configuradas
    
    Returns:
        bool: True si la configuración es válida
    """
    if not PST_NET_API_KEY:
        print("⚠️ PST_NET_API_KEY no está configurada")
        return False
    
    if not PST_NET_API_URL:
        print("⚠️ PST_NET_API_URL no está configurada")
        return False
    
    print("✅ Configuración de PST.NET válida")
    return True


def test_conexion_pst_net() -> bool:
    """
    Prueba la conexión con la API de PST.NET
    
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        # TODO: Adaptar endpoint de health check según PST.NET
        endpoint = f"{PST_NET_API_URL}/health"
        
        response = requests.get(
            endpoint,
            headers=get_pst_net_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Conexión con PST.NET exitosa")
            return True
        else:
            print(f"⚠️ Respuesta inesperada de PST.NET: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al conectar con PST.NET: {e}")
        return False


# ============================================================================
# SCRIPT DE PRUEBA
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 TEST - PST.NET Integration\n")
    
    # 1. Verificar configuración
    if not verificar_configuracion_pst_net():
        print("\n❌ Configura las variables de entorno primero:")
        print("   - PST_NET_API_URL")
        print("   - PST_NET_API_KEY")
        print("   - PST_NET_SECRET (opcional)")
        exit(1)
    
    # 2. Test de conexión
    print("\n📡 Probando conexión con PST.NET...")
    test_conexion_pst_net()
    
    # 3. Obtener pagos pendientes (sin sincronizar)
    print("\n📥 Obteniendo pagos pendientes...")
    pagos = obtener_pagos_pendientes()
    
    if pagos:
        print(f"\n✅ Se encontraron {len(pagos)} pagos:")
        for pago in pagos[:5]:  # Mostrar solo los primeros 5
            print(f"   - {pago.get('id')}: ${pago.get('monto', 0)} {pago.get('moneda', 'USD')}")
    else:
        print("\nℹ️ No hay pagos pendientes")
    
    print("\n✅ Test completado")
    print("\n💡 Para sincronizar pagos reales, ejecuta:")
    print("   from pst_net_integration import sincronizar_pagos_pst_net")
    print("   sincronizar_pagos_pst_net(supabase_client)")
