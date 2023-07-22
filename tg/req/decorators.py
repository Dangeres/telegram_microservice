import functools

from .utils import jsona as jsn
from django.http import HttpResponse

import tg.settings as settings

import hashlib
import time
import json


def access(func):

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request = args[0]

        token = hashlib.sha256(
            request.headers.get('token').encode()
        ).hexdigest()

        jsona = jsn.Jsona(
            path_file=settings.FOLDER_TOKENS,
            name_file=f'{token}.json',
        )
        
        data = jsona.return_json().get('data', {}) if token else {}

        if data.get('untill_time', 0) < int(time.time()):
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'error': 'access denied',
                })
            )

        return await func(*args, **kwargs)
    
    return wrapper