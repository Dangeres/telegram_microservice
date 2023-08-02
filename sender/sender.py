from utils import jsona as jsn
from pathlib import Path
import os

import asyncio
import functools
import json
import pika
import time

from telethon import TelegramClient, events, Button, types, utils
from telethon import errors

from telethon.tl.functions.users import GetFullUserRequest


BASE_DIR = Path(__file__).resolve().parent.parent

FOLDER_QUEUE = BASE_DIR / 'queue'
FOLDER_ERRORS = BASE_DIR / 'errors'
FOLDER_DOWNLOADS = BASE_DIR / 'downloads'


async def ticker(app):
    while True:
        for file in os.listdir(FOLDER_QUEUE):
            if not file.endswith('.json'):
                continue

            jsona = jsn.Jsona(FOLDER_QUEUE, file)

            data = jsona.return_json().get('data', {})

            now_time = int(time.time())

            if data.get('send_time', now_time) > now_time:
                continue

            if not (
                data.get('sender') and (
                    data.get('text') or 
                    (
                        data.get('file') and 
                        os.path.exists(FOLDER_DOWNLOADS / data['file'])
                    )
                )
            ):
                continue

            try:
                result = await app.send_message(
                    entity = data.get('sender'), 
                    message = data.get('text', ''),
                    reply_to = data.get('reply_to'),
                    file = FOLDER_DOWNLOADS / data['file'] if data.get('file') else None,
                    force_document = data.get('force_document', False),
                    link_preview = data.get('preview', False),
                    parse_mode = data.get('parse_mode', 'HTML'),
                )

                if result.id:
                    try:
                        if data.get('file') and not data.get('not_remove_file'):
                            os.remove(FOLDER_DOWNLOADS / data['file'])
                        
                        os.remove(FOLDER_QUEUE / file)
                    except Exception as e:
                        print(e)
            
            except errors.rpcerrorlist.FloodWaitError as e:
                print(f'Need wait {e.seconds}')

            except Exception as e:
                print(e)

                send_time_grade = data.get('send_time_grade', 0)

                send_time_grade += 1

                data['send_time'] = int(time.time()) + (send_time_grade * send_time_grade * 5) * 60 # send_time_grade^2
                data['send_time_grade'] = send_time_grade

                jsona.save_json(
                    data=data,
                )

                jsona_error = jsn.Jsona(FOLDER_ERRORS, f'{int(time.time())}.json')

                jsona_error.save_json(
                    data = {
                        'error': type(e),
                        'description': e.__str__,
                    }
                )

        await asyncio.sleep(1)


async def send_message(
    app: TelegramClient,
    data: dict,
) -> dict:
    now_time = int(time.time())

    message_id = data.get('id', 'unknown')

    if data.get('send_time', now_time) > now_time:
        print(f'AWAIT QUEUE TIME {message_id}')

        return {
            "success": False,
            "code": "error.send_time_retry",
            "dt": data.get('send_time', now_time),
            "error": "Need wait for send that message",
        }

    if not (
        data.get('sender') and (
            data.get('text') or 
            (
                data.get('file') and 
                os.path.exists(FOLDER_DOWNLOADS / data['file']) 
            )
        )
    ):
        {
            "success": False,
            "code": "error.notcorrectfields",
            "error": "No sender or one field of [text,file]",
        }

    try:
        result = await app.send_message(
            entity = data.get('sender'), 
            message = data.get('text', ''),
            reply_to = data.get('reply_to'),
            file = FOLDER_DOWNLOADS / data['file'] if data.get('file') else None,
            force_document = data.get('force_document', False),
            link_preview = data.get('preview', False),
            parse_mode = data.get('parse_mode', 'HTML'),
        )

        if result.id:
            try:
                if data.get('file') and not data.get('not_remove_file'):
                    os.remove(FOLDER_DOWNLOADS / data['file'])
                
            except Exception as e:
                print(e)
    
    except errors.rpcerrorlist.FloodWaitError as e:
        print(f'Need wait {e.seconds} for {message_id}')

        return {
            "success": False,
            "code": "error.floodwait",
            "error": f"Flood wait {e.seconds} seconds for sending this message",
            "dt": (int(time.time()) + e.seconds),
        }

    except Exception as e:
        print(f'Unknown exception for {message_id}')

        return {
            "success": False,
            "code": "error.unknown",
            "error": type(e),
        }

    return {
        "success": True,
        "message_id": result.id if result else None,
        "dt": int(time.time()),
    }


async def main():
    jsona = jsn.Jsona(name_file='settings.json', path_file=BASE_DIR / 'sender')
    login_data = jsona.return_json().get('data', {})

    jsona = jsn.Jsona(path_file=BASE_DIR, name_file='settings_rabbitmq.json')
    rabbit_config = jsona.return_json().get('data', {})


    app = TelegramClient(
        session = str(
            BASE_DIR / 'sender/sessions' / login_data['token'].split(':')[0]
        ),
        api_id = login_data['api_id'],
        api_hash = login_data['api_hash'],
        flood_sleep_threshold = 0,
    )
    
    await app.start(
        bot_token = login_data['token'],
    )

    connection = pika.BlockingConnection(
        parameters = pika.URLParameters(
            'amqp://{user}:{password}@{host}:{port}/%2F'.format(
                **rabbit_config
            )
        )
    )

    channel = connection.channel()


    async def create_consumer():
        print('[X] Created consumer')

        while True:
            method_frame, header_frame, body = channel.basic_get(
                queue = 'message',
                auto_ack = False,
            )

            if method_frame:
                try:
                    data = json.loads(body)
                except json.decoder.JSONDecodeError:
                    data = body

                print(f" [x] Received {data}")

                result = await send_message(
                    app = app,
                    data = data,
                )

                if result.get('success'):
                    print(f'success sended {data}')

                elif result.get('code') in [
                    'error.send_time_retry',
                    'error.floodwait',
                ]:
                    data['send_time'] = result.get('dt', int(time.time()))

                    channel.basic_publish(
                        exchange = 'message',
                        routing_key = 'message',
                        body = json.dumps(
                            obj = data,
                        ),
                    )

                else:
                    print(f'Unknown error is {result}')

                channel.basic_ack(method_frame.delivery_tag)
            
            else:
                print('[A] AWAIT')

                await asyncio.sleep(1)


    @app.on(
        events.NewMessage(
            incoming=True,
            pattern=r"(\/((start)))",
        )
    )
    async def handle_start(message):
        sender_id = getattr(message, 'chat_id', None)
        usernname = getattr(message.chat, 'username', None)

        username_text = f'Ваш username = <code>{usernname}</code>\n' if usernname else ''
        userid_text = f'Ваш id = <code>{sender_id}</code>\n' if sender_id else ''
        
        if not sender_id:
            return
        
        await app.send_message(
            entity=sender_id,
            message=f'Добро пожаловать!\n\n{userid_text}{username_text}'.strip(),
            parse_mode="HTML",
        )
    

    asyncio.create_task(
        create_consumer()
    )

    await app.run_until_disconnected()


if __name__ == '__main__':
    app = asyncio.run(
        main()
    )