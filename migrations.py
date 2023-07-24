import asyncio
import logging
import os

import asyncpg
from tg.req.utils import jsona as jsn


DSN = 'postgres://{user}:{password}@{host}:{port}/{database}'
FOLDER_MIGRATIONS = 'migrations/'


async def run_migrations(dsn=None, db_config=None):
    if not dsn:
        jsona = jsn.Jsona(path_file='', name_file='settings_database.json')
        db_config = jsona.return_json().get('data', {})
        dsn = DSN.format(**db_config)

    connection = await asyncpg.connect(dsn)

    migrations = sorted([m for m in os.listdir(f'{FOLDER_MIGRATIONS}') if m.endswith('.sql')])
    first_migration = next((m for m in migrations), None)

    if not first_migration:
        logging.error('Initial migration not found')
        return

    with open(f'{FOLDER_MIGRATIONS}{first_migration}') as migration_file:
        await connection.execute(migration_file.read())

    result = await connection.fetch('''SELECT id, migration_name FROM migration''')
    completed_migrations = {stage['migration_name'] for stage in result}

    migrations_for_run = sorted(set(migrations) - completed_migrations)

    for migration in migrations_for_run:
        logging.info('Running migration {}'.format(migration))

        async with connection.transaction():
            with open(f'{FOLDER_MIGRATIONS}{migration}') as migration_file:
                await connection.execute(migration_file.read())

            values = (
                int(migration.split('.')[0].split('_')[0]),
                migration,
            )
            
            await connection.execute(
                'INSERT INTO migration (id, migration_name) VALUES ($1, $2)', 
                *values,
            )
    
    await connection.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.run_until_complete(
        asyncio.ensure_future(
            run_migrations()
        )
    )