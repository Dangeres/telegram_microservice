from django.http import HttpResponse

from req.utils.request_executer import RequestExecuter
from req.utils.jsona import Jsona
from req.utils import rabbitmq
from req.decorators import access
from uuid import uuid4

import tg.settings as settings

from req.database import DataBase

import datetime
import functools
import hashlib
import secrets
import pika
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

        message_id = str(uuid4())

        secret = secrets.token_urlsafe()

        secret_hash = hashlib.sha256(message_id.encode())
        secret_hash.update(secret.encode())

        token = hashlib.sha256(
            request.headers.get('token').encode()
        ).hexdigest()

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
        

        build_message = {
            'id': message_id,
            'token': token,
            'secret': secret_hash.hexdigest(),
            'time': int(time.time()),
            'sender': params.get('sender'),
            'text': params.get('text', None),
            'file': params.get('file', None),
            'reply_to': params.get('reply_to', None),
            'preview': params.get('preview', True),
            'force_document': params.get('force_document', False),
        }

        query = """
insert into message_secret(id, secret, token_service, dt) values ($1, $2, $3, $4)
on conflict (id) do update set
token_service = excluded.token_service,
secret = excluded.secret,
dt = excluded.dt
returning *;
"""

        db = DataBase()
        connect = await db.create_connect()

        args_query = (
            build_message['id'],
            build_message['secret'],
            build_message['token'],
            datetime.datetime.now(),
        )

        result_db = await connect.fetchrow(
            query,
            *args_query,
        )

        if not result_db:
            return {
                'success': False,
                'error': 'Unknown error',
            }

        connection = pika.BlockingConnection(
            parameters = pika.URLParameters(
                'amqp://{user}:{password}@{host}:{port}/%2F'.format(
                    **settings.settings_rabbitmq
                )
            )
        )

        channel = connection.channel()

        rabbitmq.init(channel)

        channel.basic_publish(
            exchange = settings.rabbitmq.exchange_name,
            routing_key = settings.rabbitmq.routing_key,
            body = json.dumps(
                obj = build_message,
            ),
        )

        connection.close()
        
        result = {
            'success': True,
            'id': build_message['id'],
            'secret': secret,
        }

        return result


    async def get_requests(params, *args, **kwargs):
        params = params.get('data', {})

        query = """
with finded_result as (
	select * from message_result where id = $1
),
finded_secret as (
	select * from message_secret where id = $1
)
select
fr.id,
fr.dt,
fr.message_id,
fr.sender,
fr.error,
fs.token_service,
fs.secret
from finded_secret fs inner join finded_result fr on fr.id = fs.id;
"""

        db = DataBase()
        connect = await db.create_connect()

        args_query = (
            params.get('id', ''),
        )

        id_data = await connect.fetchrow(
            query,
            *args_query,
        )

        error = None

        hash_obj = hashlib.sha256(params.get('id', '').encode())
        hash_obj.update(params.get('secret', '').encode())

        token = hashlib.sha256(
            request.headers.get('token', '').encode()
        ).hexdigest()
        
        if not id_data:
            error = 'No data for this id yet'
        
        elif id_data.get('secret') != hash_obj.hexdigest():
            error = 'Secret is not correct'
            id_data = None

        elif id_data.get('token_service') != token:
            error = 'Token is not correct'
            id_data = None

        return await response_wrapper(
            data = {
                'success': True,
                'data': {
                    'id': id_data['id'],
                    'message_id': id_data['message_id'],
                    'sender': id_data['sender'],
                    'error': id_data['error'],
                },
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
        )
        
        result = await reqexe.execute()
    except Exception as e:
        print(e)

        jsona = Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

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

        jsona = Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

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

        jsona = Jsona(settings.FOLDER_ERRORS, f'{int(time.time())}.json')

        jsona.save_json(
            data = {
                'error': str(type(e)),
                'description': str(e),
            }
        )
    
    return await response_wrapper(result)