from django.http import HttpResponse

from req.utils.request_executer import RequestExecuter
from req.utils import jsona as jsn
from req.decorators import access
from uuid import uuid4

import tg.settings as settings

from req.database import DataBase

import datetime
import functools
import hashlib
import secrets
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
        reqexe = RequestExecuter(
            request = request,
            get = get_requests,
            post = post_requests,
        )
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)
    
    return await response_wrapper(result)


async def queue(request):
    async def get_requests(params, *args, **kwargs):
        params = params.get('data', {})

        return await response_wrapper(
            data = {
                'data': list(
                    map(
                        lambda x: x.replace('.json', ''), 
                        os.listdir(settings.FOLDER_QUEUE)
                    )
                ),
            }
        )
    
    result = {"success": False}

    try:
        reqexe = RequestExecuter(
            request = request,
            get = get_requests,
        )
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)

        jsona = jsn.Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

        jsona.save_json(
            data = {
                'error': str(type(e)),
                'description': str(e),
            }
        )
    
    return await response_wrapper(result)


@access
async def message(request):
    def has_one_of_field(x, y):
        for field in x:
            if field in y:
                return True
        
        return False


    async def post_requests(params, *args, **kwargs):
        one_of_required_fields = [
            'text',
            'file',
        ]

        params = params.get('data', {})

        params['id'] = str(uuid4())

        jsona = jsn.Jsona(
            path_file=settings.FOLDER_QUEUE, 
            name_file='%s.json' % (params["id"]),
        )

        secret = secrets.token_urlsafe()

        hash_obj = hashlib.sha256(params.get('id', '').encode())
        hash_obj.update(secret.encode())

        token = hashlib.sha256(
            request.headers.get('token').encode()
        ).hexdigest()

        params['secret'] = hash_obj.hexdigest()
        params['time'] = int(time.time())
        params['token'] = token

        if not (
            params.get('sender') and 
            has_one_of_field(one_of_required_fields, params)
        ):
            return {
                'success': False,
                'error': 'Need one of field [%s]' % (
                    '/'.join(one_of_required_fields),
                )
            }

        if params.get('file') and not os.path.exists(
            os.path.join(
                settings.FOLDER_DOWNLOADS,
                params.get('file'),
            )
        ):
            return {
                'success': False,
                'error': f'File {params["file"]} doesn\'t exist'
            }

#         query = """
# insert into message_secret(token, secret) values ($1, $2);
# """

#         db = DataBase()

#         connect = db.create_connect()

#         args_query = (
#             token,
#             hash_obj.hexdigest(),
#             datetime.datetime.now(),
#         )

#         result_db = await connect.fetchrow(
#             query,
#             *args_query,
#         )

#         result_queue = jsona.save_json(data = params).get('success')

#         result = {
#             'success': False
#         }

#         if result_queue and result_db:
#             result = {
#                 'success': True,
#                 'id': params['id'],
#                 'secret': secret,
#             }

#         elif result_queue and not result_db:
#             try:
#                 os.remove()
#             except Exception as e:
#                 pass
        
        result = {
            'success': jsona.save_json(data = params).get('success'),
        }

        if result.get('success'):
            result['id'] = params['id']
            result['secret'] = secret

        return result


    async def get_requests(params, *args, **kwargs):
        restrict_fields = [
            'secret',
            'token',
        ]

        params = params.get('data', {})

        id_data = None
        error = None

        if params.get('id'):
            jsona = jsn.Jsona(
                path_file=settings.FOLDER_QUEUE, 
                name_file='%s.json' % (params["id"]),
            )

            id_data = jsona.return_json().get('data')

        hash_obj = hashlib.sha256(params.get('id', '').encode())
        hash_obj.update(params.get('secret', '').encode())

        token = hashlib.sha256(
            request.headers.get('token', '').encode()
        ).hexdigest()
        
        if not id_data:
            error = 'No data for this id'
        
        elif id_data.get('secret') != hash_obj.hexdigest():
            error = 'Secret is not correct'
            id_data = None

        elif id_data.get('token') != token:
            error = 'Token is not correct'
            id_data = None

        if id_data:
            for key in restrict_fields:
                id_data.pop(key, None)

        return await response_wrapper(
            data = {
                'success': True,
                'data': id_data,
            } if not error else {
                'success': False,
                'data': id_data,
                'error': error,
            }
        )
    

    async def delete_requests(params, *args, **kwargs):
        params = params.get('data', {})

        if params.get('id'):
            jsona = jsn.Jsona(
                path_file=settings.FOLDER_QUEUE, 
                name_file='%s.json' % (params["id"]),
            )

            id_data = jsona.return_json().get('data')

        hash_obj = hashlib.sha256(id_data.get('id', '').encode())
        hash_obj.update(params.get('secret', '').encode())

        token = hashlib.sha256(
            request.headers.get('token').encode()
        ).hexdigest()

        error = None

        if not id_data:
            error = 'No data for this id'

        elif id_data.get('secret') != hash_obj.hexdigest():
            error = 'Secret is not correct'

        elif id_data.get('token') != token:
            error = 'Token is not correct'

        if not error:
            os.remove(
                os.path.join(
                    settings.FOLDER_QUEUE, '%s.json' % (params["id"])
                )
            )

        return await response_wrapper(
            data = {
                'success': True,
            } if not error else {
                'success': False,
                'error': error,
            }
        )
    
    result = {"success": False}

    try:
        reqexe = RequestExecuter(
            request = request, 
            get = get_requests, 
            post = post_requests, 
            delete = delete_requests,
        )
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)

        jsona = jsn.Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

        jsona.save_json(
            data = {
                'error': str(type(e)),
                'description': str(e),
            }
        )
    
    return await response_wrapper(result)


@access
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
        reqexe = RequestExecuter(
            request = request,
            get = get_requests,
            post = post_requests,
        )
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)

        jsona = jsn.Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

        jsona.save_json(
            data = {
                'error': str(type(e)),
                'description': str(e),
            }
        )
    
    return await response_wrapper(result)


async def user(request):
    async def post_requests(params, *args, **kwargs):
        params = params.get('data', {})

        token = str(uuid4())

        hashed_token = hashlib.sha256(
            token.encode()
        ).hexdigest()

        query = """insert into tokens(id, create_dt, untill_dt) 
values ($1, $2, $3)
on conflict (id) do update set
untill_dt = excluded.untill_dt
returning *;"""

        args_query = (
            hashed_token,
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days = 31),
        )

        db = DataBase()
        connect = await db.create_connect()

        result = await connect.fetchrow(
            query,
            *args_query,
        )

        return {
            'success': True,
            'token': result['id'],
        }


    async def get_requests(params, *args, **kwargs):
        params = params.get('data', {})

        return {
            'success': True,
            'type': 'get',
        }
    

    result = {"success": False}

    try:
        reqexe = RequestExecuter(
            request = request,
            get = get_requests,
            post = post_requests,
        )
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)

        jsona = jsn.Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

        jsona.save_json(
            data = {
                'error': str(type(e)),
                'description': str(e),
            }
        )
    
    return await response_wrapper(result)