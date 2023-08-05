import functools

from django.http import JsonResponse
from tg.settings import settings_database_dsn

import asyncpg
import hashlib
import datetime
import json


def access(func):

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request = args[0]

        token = hashlib.sha256(
            request.headers.get('token', '').encode()
        ).hexdigest()

        async with asyncpg.create_pool(
            dsn = settings_database_dsn,
        ) as pool:
            async with pool.acquire() as connect:
                query = """
select id, untill_dt from tokens where id = $1;
"""
                args_query = (
                    token,
                )

                data = await connect.fetchrow(
                    query,
                    *args_query
                )

        if not data or (data['untill_dt'] < datetime.datetime.now()):
            return JsonResponse(
                data = {
                    'success': False,
                    'error': 'access denied',
                },
                status = 403,
            )

        return await func(*args, **kwargs)
    
    return wrapper