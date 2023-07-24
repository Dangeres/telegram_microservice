
from tg.settings import settings_database

import asyncpg

class DataBase():
    def __init__(self) -> None:
        pass

    async def create_connect(self) -> asyncpg.Connection:
        return await asyncpg.connect(
            dsn = 'postgres://{user}:{password}@{host}:{port}/{database}'.format(
                **settings_database
            )
        )
    
    