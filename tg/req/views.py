from django.http import HttpResponse

from .utils.request_executer import RequestExecuter
from .utils import jsona as jsn
from uuid import uuid4

import tg.settings as settings

import json
import time
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
            params['id'] = str(uuid4())

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

        jsona = jsn.Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

        jsona.save_json(
            data = {
                'error': type(e),
                'description': e.__str__,
            }
        )
    
    return await response_wrapper(result)


async def file(request):
    async def post_requests(params, *args, **kwargs):
        params = params.get('data', {})

        request_file = request.FILES['file']

        file_name = '.'.join(
            [
                str(uuid4()),
                request_file._get_name().rsplit(".", 1)[-1] 
                    if len(request_file._get_name().rsplit(".", 1)) > 1 
                    else ''
            ]
        )

        file_path = os.path.join(
            settings.FOLDER_DOWNLOADS,
            file_name,
        )

        with open(file_path, "wb") as file:
            content = request_file.read()
            file.seek(0)
            file.write(content)

        return {
            'success': True,
            'type': 'post',
            'file_name': file_name,
        }


    async def get_requests(params, *args, **kwargs):
        params = params.get('data', {})

        return {
            'success': True,
            'type': 'get',
        }
    

    result = {"success": False}

    try:
        reqexe = RequestExecuter(request = request, get = get_requests, post = post_requests)
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)

        jsona = jsn.Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

        jsona.save_json(
            data = {
                'error': type(e),
                'description': e.__str__,
            }
        )
    
    return await response_wrapper(result)