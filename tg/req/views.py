from django.http import HttpResponse

from .utils.request_executer import RequestExecuter
from .utils import jsona as jsn
from uuid import uuid4

import tg.settings as settings

import json
import os


async def response_wrapper(data) -> HttpResponse:
    if type(data) == dict:
        return HttpResponse(json.dumps(data))
    
    return HttpResponse(data)


async def ping(request):
    async def get_requests(params, *args, **kwargs):
        return {
            'success': True,
            'type': 'get',
            'params': params,
        }

    async def post_requests(params, *args, **kwargs):
        return {
            'success': True,
            'type': 'post',
            'params': params,
        }

    result = {
        'success': True,
        'type': 'unknown',
    }

    try:
        reqexe = RequestExecuter(request = request, get = get_requests, post = post_requests)
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)
    
    return await response_wrapper(result)


async def message(request):
    async def post_requests(params, *args, **kwargs):
        params = params.get('data', {})

        if not params.get('id'):
            params['id'] = uuid4()

        jsona = jsn.Jsona(
            path_file=settings.FOLDER_QUEUE, 
            name_file='%s.json' % (params["id"]),
        )

        return jsona.save_json(data = params)

    async def get_requests(params, *args, **kwargs):
        params = params.get('data', {})

        id_data = None

        if params.get('id'):
            jsona = jsn.Jsona(
                path_file=settings.FOLDER_QUEUE, 
                name_file='%s.json' % (params["id"]),
            )

            id_data = jsona.return_json().get('data')

        return await response_wrapper(
            data = {
                'id_data': id_data,
                'queue_files': os.listdir(
                    path = settings.FOLDER_QUEUE,
                )
            }
        )
    
    result = {"success": False}

    try:
        reqexe = RequestExecuter(request = request, get = get_requests, post = post_requests)
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)
    
    return await response_wrapper(result)