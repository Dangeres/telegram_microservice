import functools

from req.database import DataBase
from django.http import HttpResponse

import tg.settings as settings

import hashlib
import datetime
import json


def access(func):

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request = args[0]

        token = hashlib.sha256(
            request.headers.get('token').encode()
        ).hexdigest()

        db = DataBase()

        connect = await db.create_connect()

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
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'error': 'access denied',
                })
            )

        return await func(*args, **kwargs)
    
    return wrapper