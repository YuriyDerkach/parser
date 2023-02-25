import asyncio
from parsers import RealtParser, DomovitaParser


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


realt = RealtParser()
domovita = DomovitaParser()


asyncio.run(realt.get_last_flats())
asyncio.run(domovita.get_last_flats())
