#!/usr/bin/env python3
"""
Script auxiliar para obtener la IP pública del servidor
Útil para configurar la lista blanca de PST.NET
"""

import requests

def get_public_ip():
    """
    Obtiene la IP pública del servidor usando servicios externos
    """
    print("\n" + "="*60)
    print("🌐 OBTENIENDO IP PÚBLICA DEL SERVIDOR")
    print("="*60 + "\n")
    
    services = [
        'https://api.ipify.org?format=json',
        'https://ifconfig.me/ip',
        'https://icanhazip.com',
        'https://ident.me',
    ]
    
    for service in services:
        try:
            print(f"📡 Consultando {service}...")
            response = requests.get(service, timeout=5)
            
            if response.status_code == 200:
                # Algunos servicios devuelven JSON, otros plain text
                try:
                    ip = response.json().get('ip')
                except:
                    ip = response.text.strip()
                
                print(f"✅ IP detectada: {ip}\n")
                print("="*60)
                print(f"\n📋 IP A AGREGAR EN PST.NET: {ip}/32\n")
                print("="*60)
                
                return ip
        except Exception as e:
            print(f"❌ Error con {service}: {e}")
            continue
    
    print("\n❌ No se pudo obtener la IP pública")
    return None

if __name__ == "__main__":
    get_public_ip()
