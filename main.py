import asyncio
from fatura_isleyici import FaturaIsleyici

async def main():
    isleyici = FaturaIsleyici()
    await isleyici.tum_yillari_isle()

if __name__ == "__main__":
    asyncio.run(main()) 