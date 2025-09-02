import asyncio
import aiohttp
import json
from typing import Optional, Dict, Union

async def fetch_with_timeout(url: str, method: str = 'GET', headers: Optional[Dict] = None, 
                            data: Optional[str] = None, timeout: int = 10):
    """
    Función auxiliar para hacer peticiones HTTP con timeout
    """
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        if method.upper() == 'POST':
            async with session.post(url, headers=headers, data=data) as response:
                return await response.json()
        else:
            async with session.get(url, headers=headers) as response:
                return await response.json()

async def get_binance_p2p_rate() -> Optional[Dict[str, Union[float, None]]]:
    """
    FUNCIÓN ACTUALIZADA: Obtiene las tasas de Binance P2P y devuelve un objeto
    con los promedios de compra, venta y el promedio de mercado.
    """
    url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
    
    async def fetch_trade_type_average(trade_type: str) -> Optional[float]:
        try:
            payload = {
                "fiat": "VES",
                "tradeType": trade_type,
                "asset": "USDT",
                "page": 1,
                "rows": 10,
                "merchantCheck": False,
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            }

            data = await fetch_with_timeout(
                url, 
                method='POST', 
                headers=headers, 
                data=json.dumps(payload)
            )
            
            is_success = data.get('code') == "000000" or data.get('success') == True
            has_data = data.get('data') and len(data.get('data', [])) > 0

            if is_success and has_data:
                prices = [float(ad['adv']['price']) for ad in data['data']]
                return sum(prices) / len(prices)
            
            return None
            
        except Exception as error:
            print(f"Error al obtener tasa de Binance P2P ({trade_type}): {str(error)}")
            return None

    try:
        # Ejecutar ambas peticiones concurrentemente
        buy_avg, sell_avg = await asyncio.gather(
            fetch_trade_type_average('BUY'),
            fetch_trade_type_average('SELL')
        )

        # Devolvemos un objeto con todos los datos
        if buy_avg and sell_avg:
            market_average = (buy_avg + sell_avg) / 2
            result = {
                'buy': round(buy_avg, 2),
                'sell': round(sell_avg, 2),
                'average': round(market_average, 2)
            }
            
            # Imprimir los promedios en consola
            print(f"Promedio de Compra: {result['buy']}")
            print(f"Promedio de Venta: {result['sell']}")
            print(f"Promedio de Mercado: {result['average']}")
            
            return result
        
        # Si uno de los dos falla, devolvemos lo que tengamos
        result = {
            'buy': round(buy_avg, 2) if buy_avg else None,
            'sell': round(sell_avg, 2) if sell_avg else None,
            'average': None  # No se puede calcular el promedio si falta un valor
        }
        
        # Imprimir los promedios disponibles
        if result['buy']:
            print(f"Promedio de Compra: {result['buy']}")
        if result['sell']:
            print(f"Promedio de Venta: {result['sell']}")
        if not result['buy'] or not result['sell']:
            print("No se pudo calcular el promedio de mercado (falta información)")
            
        return result

    except Exception as error:
        print(f"Error general al procesar tasas de Binance P2P: {str(error)}")
        return None  # Devuelve None si hay un error catastrófico

# Función para ejecutar el código principal
async def main():
    """
    Función principal para ejecutar y mostrar los resultados
    """
    print("Obteniendo tasas de Binance P2P...")
    result = await get_binance_p2p_rate()
    
    if result:
        print("\n--- Resultado Final ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("No se pudieron obtener las tasas")

# Ejecutar el código si se ejecuta directamente
if __name__ == "__main__":
    asyncio.run(main())
