#!/usr/bin/env python3
"""
BLACK INFRASTRUCTURE - FUNCIONES DE COSTOS DINÁMICOS
=====================================================
Funciones para calcular costos con lógica dinámica

Autor: Senior Backend Developer
Fecha: 21/01/2026
Versión: 3.0.0
"""

from supabase import Client


def get_valor_dolar(supabase: Client) -> float:
    """
    Obtiene el valor del dólar desde la tabla de configuración.
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        float: Valor del dólar o 1500.0 por defecto
    """
    try:
        response = supabase.table('configuracion') \
            .select('valor_numerico') \
            .eq('clave', 'dolar_conversion') \
            .single() \
            .execute()
        
        if response.data:
            return float(response.data.get('valor_numerico', 1500.0))
        
        return 1500.0
    except Exception as e:
        print(f"⚠️ Error al obtener valor del dólar, usando default: {e}")
        return 1500.0


def get_honorario_por_cliente(supabase: Client) -> float:
    """
    Obtiene el honorario por cliente desde configuración.
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        float: Honorario por cliente o 55.0 por defecto
    """
    try:
        response = supabase.table('configuracion') \
            .select('valor_numerico') \
            .eq('clave', 'honorario_por_cliente') \
            .single() \
            .execute()
        
        if response.data:
            return float(response.data.get('valor_numerico', 55.0))
        
        return 55.0
    except Exception as e:
        print(f"⚠️ Error al obtener honorario por cliente, usando default: {e}")
        return 55.0


def calcular_costo_agustin(supabase: Client) -> dict:
    """
    Calcula el costo de Agustín basado en clientes activos.
    Fórmula: cantidad_clientes_activos × $55 USD
    
    Args:
        supabase: Cliente de Supabase
    
    Returns:
        dict: {
            'cantidad_clientes': int,
            'honorario_unitario': float,
            'total_usd': float
        }
    """
    try:
        # Obtener cantidad de clientes activos
        response = supabase.table('clientes') \
            .select('id', count='exact') \
            .eq('activo', True) \
            .execute()
        
        cantidad_clientes = response.count if hasattr(response, 'count') else 0
        honorario_unitario = get_honorario_por_cliente(supabase)
        total_usd = cantidad_clientes * honorario_unitario
        
        print(f"💰 Costo Agustín: {cantidad_clientes} clientes × ${honorario_unitario} = ${total_usd:.2f} USD")
        
        return {
            'cantidad_clientes': cantidad_clientes,
            'honorario_unitario': honorario_unitario,
            'total_usd': total_usd
        }
    except Exception as e:
        print(f"❌ Error al calcular costo de Agustín: {e}")
        return {
            'cantidad_clientes': 0,
            'honorario_unitario': 55.0,
            'total_usd': 0.0
        }


def get_costos_con_conversion(supabase: Client, start_date: str = '2026-01-01', end_date: str = '2026-01-31') -> dict:
    """
    Obtiene todos los costos con conversión ARS→USD actualizada y cálculo dinámico de Agustín.
    
    Args:
        supabase: Cliente de Supabase
        start_date: Fecha de inicio
        end_date: Fecha de fin
    
    Returns:
        dict: Costos agrupados con totales calculados
    """
    try:
        dolar_actual = get_valor_dolar(supabase)
        print(f"💱 Usando dólar: ${dolar_actual:,.2f}")
        
        # Obtener costos de la base de datos
        response = supabase.table('costos') \
            .select('nombre, monto_ars, monto_usd, tipo, observacion, es_calculo_dinamico, formula') \
            .gte('created_at', start_date) \
            .lte('created_at', end_date) \
            .execute()
        
        if not response.data:
            return {
                'error': 'No hay costos en el período especificado',
                'dolar_actual': dolar_actual
            }
        
        costos_fijos = []
        costos_variables = []
        total_fijo = 0.0
        total_variable = 0.0
        
        for costo in response.data:
            nombre = costo.get('nombre')
            es_dinamico = costo.get('es_calculo_dinamico', False)
            
            # Calcular monto USD
            if nombre == 'Agustin' or es_dinamico:
                # Cálculo dinámico para Agustín
                calc_agustin = calcular_costo_agustin(supabase)
                monto_usd = calc_agustin['total_usd']
                observacion = f"Calculado: {calc_agustin['cantidad_clientes']} clientes × ${calc_agustin['honorario_unitario']} USD"
            elif costo.get('monto_ars'):
                # Conversión ARS → USD
                monto_usd = round(costo['monto_ars'] / dolar_actual, 2)
                observacion = costo.get('observacion', '')
            else:
                # Monto fijo en USD
                monto_usd = float(costo.get('monto_usd', 0))
                observacion = costo.get('observacion', '')
            
            item = {
                'nombre': nombre,
                'monto_usd': monto_usd,
                'monto_ars': costo.get('monto_ars'),
                'observacion': observacion,
                'es_dinamico': es_dinamico
            }
            
            if costo.get('tipo') == 'Fijo':
                costos_fijos.append(item)
                total_fijo += monto_usd
            else:
                costos_variables.append(item)
                total_variable += monto_usd
        
        total_general = total_fijo + total_variable
        
        print(f"✅ Costos calculados - Fijo: ${total_fijo:,.2f} | Variable: ${total_variable:,.2f} | Total: ${total_general:,.2f}")
        
        return {
            'Fijo': costos_fijos,
            'Variable': costos_variables,
            'total_fijo': total_fijo,
            'total_variable': total_variable,
            'total_general': total_general,
            'dolar_actual': dolar_actual
        }
        
    except Exception as e:
        print(f"❌ Error en get_costos_con_conversion: {e}")
        return {
            'error': str(e),
            'dolar_actual': 1500.0
        }


def actualizar_valor_dolar(supabase: Client, nuevo_valor: float) -> bool:
    """
    Actualiza el valor del dólar en la configuración.
    
    Args:
        supabase: Cliente de Supabase
        nuevo_valor: Nuevo valor del dólar
    
    Returns:
        bool: True si se actualizó correctamente
    """
    try:
        supabase.table('configuracion') \
            .update({
                'valor_numerico': nuevo_valor,
                'updated_at': 'NOW()'
            }) \
            .eq('clave', 'dolar_conversion') \
            .execute()
        
        print(f"✅ Valor del dólar actualizado a: ${nuevo_valor:,.2f}")
        return True
    except Exception as e:
        print(f"❌ Error al actualizar valor del dólar: {e}")
        return False
