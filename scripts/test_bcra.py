#!/usr/bin/env python3
"""
Script de prueba para testear todas las funciones del cliente BCRA.
Prueba con CUIT: 30-69163759-6
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.services.bcra_client import BCRAClient
from src.app.core.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_section(title: str):
    """Imprime un separador de sección."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_json(data: dict, indent: int = 2):
    """Imprime un diccionario como JSON formateado."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


async def test_cuit_conversion(bcra_client: BCRAClient, cuit: str):
    """Prueba la conversión de CUIT a identificación."""
    print_section("1. PRUEBA: Conversión de CUIT a Identificación")
    
    identificacion = bcra_client._cuit_to_identificacion(cuit)
    print(f"CUIT: {cuit}")
    print(f"Identificación (número): {identificacion}")
    
    if identificacion:
        print("✅ Conversión exitosa")
    else:
        print("❌ Error en la conversión")
    
    return identificacion


async def test_get_deudas(bcra_client: BCRAClient, cuit: str):
    """Prueba la consulta de deudas."""
    print_section("2. PRUEBA: Consulta de Deudas Actuales")
    
    print(f"Consultando deudas para CUIT: {cuit}")
    print(f"URL Base: {bcra_client.base_url}")
    print(f"Endpoint: /centraldedeudores/v1.0/Deudas/{{Identificacion}}\n")
    
    try:
        result = await bcra_client.get_deudas(cuit)
        
        if result.get("status") == 0:
            print("✅ Consulta exitosa")
            print("\nResultado:")
            print_json(result)
            
            # Extraer información relevante
            if "results" in result:
                results = result["results"]
                print(f"\n📊 Resumen:")
                print(f"  - Identificación: {results.get('identificacion', 'N/A')}")
                print(f"  - Denominación: {results.get('denominacion', 'N/A')}")
                
                if "periodos" in results:
                    periodos = results["periodos"]
                    print(f"  - Períodos encontrados: {len(periodos)}")
                    
                    for periodo in periodos:
                        print(f"\n  Período: {periodo.get('periodo', 'N/A')}")
                        if "entidades" in periodo:
                            for entidad in periodo["entidades"]:
                                print(f"    - Entidad: {entidad.get('entidad', 'N/A')}")
                                print(f"      Situación: {entidad.get('situacion', 0)}")
                                print(f"      Monto: ${entidad.get('monto', 0):,.2f}")
        elif result.get("status") == -1:
            print("❌ Error en la consulta")
            print_json(result)
        else:
            print("⚠️  Respuesta inesperada")
            print_json(result)
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_get_cheques_rechazados(bcra_client: BCRAClient, cuit: str):
    """Prueba la consulta de cheques rechazados."""
    print_section("3. PRUEBA: Consulta de Cheques Rechazados")
    
    print(f"Consultando cheques rechazados para CUIT: {cuit}")
    print(f"Endpoint: /centraldedeudores/v1.0/Deudas/ChequesRechazados/{{Identificacion}}\n")
    
    try:
        result = await bcra_client.get_cheques_rechazados(cuit)
        
        if result.get("status") == 0:
            print("✅ Consulta exitosa")
            print("\nResultado:")
            print_json(result)
            
            # Contar cheques rechazados
            if "results" in result:
                results = result["results"]
                print(f"\n📊 Resumen:")
                print(f"  - Identificación: {results.get('identificacion', 'N/A')}")
                print(f"  - Denominación: {results.get('denominacion', 'N/A')}")
                
                total_cheques = 0
                if "causales" in results:
                    print(f"  - Causales encontradas: {len(results['causales'])}")
                    
                    for causal in results["causales"]:
                        causal_name = causal.get("causal", "N/A")
                        print(f"\n  Causal: {causal_name}")
                        
                        if "entidades" in causal:
                            for entidad in causal["entidades"]:
                                entidad_id = entidad.get("entidad", "N/A")
                                if "detalle" in entidad:
                                    cheques_count = len(entidad["detalle"])
                                    total_cheques += cheques_count
                                    print(f"    - Entidad {entidad_id}: {cheques_count} cheque(s) rechazado(s)")
                
                print(f"\n  📌 Total de cheques rechazados: {total_cheques}")
        elif result.get("status") == -1:
            print("❌ Error en la consulta")
            print_json(result)
        else:
            print("⚠️  Respuesta inesperada")
            print_json(result)
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_get_deudas_historicas(bcra_client: BCRAClient, cuit: str):
    """Prueba la consulta de deudas históricas."""
    print_section("4. PRUEBA: Consulta de Deudas Históricas")
    
    print(f"Consultando deudas históricas para CUIT: {cuit}")
    print(f"Endpoint: /centraldedeudores/v1.0/Deudas/Historicas/{{Identificacion}}\n")
    
    try:
        result = await bcra_client.get_deudas_historicas(cuit)
        
        if result.get("status") == 0:
            print("✅ Consulta exitosa")
            print("\nResultado:")
            print_json(result)
            
            if "results" in result:
                results = result["results"]
                print(f"\n📊 Resumen:")
                print(f"  - Identificación: {results.get('identificacion', 'N/A')}")
                print(f"  - Denominación: {results.get('denominacion', 'N/A')}")
                
                if "periodos" in results:
                    print(f"  - Períodos históricos encontrados: {len(results['periodos'])}")
        elif result.get("status") == -1:
            print("❌ Error en la consulta")
            print_json(result)
        else:
            print("⚠️  Respuesta inesperada")
            print_json(result)
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_check_credit_status(bcra_client: BCRAClient, cuit: str):
    """Prueba el método principal check_credit_status."""
    print_section("5. PRUEBA: Check Credit Status (Método Principal)")
    
    print(f"Consultando estado crediticio completo para CUIT: {cuit}\n")
    
    try:
        result = await bcra_client.check_credit_status(cuit)
        
        print("✅ Consulta completada")
        print("\n📋 Resultado Consolidado:")
        print(f"  Estado BCRA: {result.get('estado_bcra', 'N/A')}")
        print(f"  Cheques Rechazados: {result.get('cheques_rechazados', 0)}")
        print(f"  Riesgo Crediticio: {result.get('riesgo_crediticio', 'N/A')}")
        
        if "detalles" in result:
            detalles = result["detalles"]
            print(f"\n📊 Detalles:")
            print(f"  - Monto Total: ${detalles.get('monto_total', 0):,.2f}")
            print(f"  - Tiene Deuda Actual: {detalles.get('tiene_deuda_actual', False)}")
            print(f"  - Situaciones: {detalles.get('situaciones', [])}")
        
        print("\n📄 Resultado completo:")
        print_json(result)
        
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Función principal de prueba."""
    cuit = "30-69163759-6"
    
    print("\n" + "=" * 80)
    print("  TESTEO LOCAL - CLIENTE BCRA")
    print("=" * 80)
    print(f"\nCUIT de prueba: {cuit}")
    print(f"URL Base BCRA: {settings.bcra_api_url}")
    print(f"\nIniciando pruebas...\n")
    
    # Inicializar cliente
    bcra_client = BCRAClient()
    
    # Ejecutar todas las pruebas
    try:
        # 1. Conversión de CUIT
        await test_cuit_conversion(bcra_client, cuit)
        
        # 2. Consulta de deudas
        await test_get_deudas(bcra_client, cuit)
        
        # 3. Consulta de cheques rechazados
        await test_get_cheques_rechazados(bcra_client, cuit)
        
        # 4. Consulta de deudas históricas
        await test_get_deudas_historicas(bcra_client, cuit)
        
        # 5. Check credit status (método principal)
        await test_check_credit_status(bcra_client, cuit)
        
        print_section("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("Revisa los resultados arriba para verificar el funcionamiento.\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

