from utils import jsona as jsn
from pathlib import Path
import os

import asyncio
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


async def main():
    print(FOLDER_QUEUE)

    jsona = jsn.Jsona(name_file='settings.json', path_file=BASE_DIR / 'sender')

    login_data = jsona.return_json().get('data', {})

    app = TelegramClient(
        session = str(BASE_DIR / 'sender/sessions' / login_data['token'].split(':')[0]),
        api_id = login_data['api_id'],
        api_hash = login_data['api_hash'],
    )
    
    await app.start(
        bot_token = login_data['token'],
    )


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
    

    asyncio.get_event_loop().create_task(ticker(app))

    await app.run_until_disconnected()


if __name__ == '__main__':
    app = asyncio.run(
        main()
    )