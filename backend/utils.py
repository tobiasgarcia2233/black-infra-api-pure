#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - UTILIDADES
==================================
Funciones auxiliares y utilidades comunes

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 2.0.0
"""

import re


def limpiar_id(callback_data: str) -> str:
    """
    Limpia y extrae el UUID de un callback_data.
    
    SEGURIDAD: Esta función garantiza que solo se envíe el UUID puro a la base de datos,
    evitando el error 22P02 (invalid input syntax for type uuid).
    
    Args:
        callback_data: String como 'borrar_costo_UUID' o 'confirmar_borrar_costo_UUID'
    
    Returns:
        str: Solo el UUID (formato: 8-4-4-4-12 caracteres hexadecimales)
    
    Ejemplos:
        >>> limpiar_id('borrar_costo_550e8400-e29b-41d4-a716-446655440000')
        '550e8400-e29b-41d4-a716-446655440000'
        
        >>> limpiar_id('confirmar_borrar_costo_550e8400-e29b-41d4-a716-446655440000')
        '550e8400-e29b-41d4-a716-446655440000'
    """
    # Método 1: Regex (más robusto)
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    match = re.search(uuid_pattern, callback_data, re.IGNORECASE)
    
    if match:
        return match.group(0)
    
    # Método 2: Split simple (fallback)
    # Si el callback_data es 'prefijo_UUID', devuelve 'UUID'
    return callback_data.split('_')[-1]


def formato_argentino(numero: float) -> str:
    """
    Formatea números al estilo argentino: punto para miles, coma para decimales.
    
    Args:
        numero: Número a formatear
    
    Returns:
        str: Número formateado (ej: "270.000,00")
    
    Ejemplo:
        >>> formato_argentino(270000)
        '270.000,00'
    """
    entero = int(numero)
    decimal = numero - entero
    
    # Formatear parte entera con puntos
    entero_str = f"{entero:,}".replace(',', '.')
    
    # Formatear parte decimal con coma
    decimal_str = f"{decimal:.2f}".split('.')[1]
    
    return f"{entero_str},{decimal_str}"
