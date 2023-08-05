<h1 align="center">
  Микросервис по отправке сообщений в телеграм
</h1>

<h4 align="center">Оглавление README:</h4>
<div align="center">
    <a href="#про-микросервис"> • Для чего нужен этот микросервис • </a><br>
    <a href="#установка"> • Установка • </a><br>
    <a href="#внутрянка"> • Что внутри • </a><br>
    <a href="#файлы-settings"> • Файлы settings • </a><br>
    <a href="#структура"> • Структура проекта • </a><br>
    <a href="#примечание"> • Примечание • </a>
</div>


## Про микросервис
Так как у меня имеется пачка скриптов, и у меня остро стоит проблема с уведомлением о каких-то полученных данных - будь это изменение цен, будь это напоминание или что-то еще. Так как мне удобно пользоваться телеграмом, было решено сделать микросервис с возможностью отправить сообщение в какой-то канал или напрямую на аккаунт. Именно для этого и был создан данный репозиторий.


## Установка
1. Скачиваете ветку;
2. Устанавливаете python 3.9, rabbitmq 3.8.2, postgres;
3. Создаете виртуальное окружение `python3.9 -m venv env`
4. Активируете виртуальное окружение и устанавливаете зависимости `pip install -r requirements.txt`
5. Редактируете файлы settings под себя;
6. Скачиваете и настраиваете все необходимое для разворачивания микросервиса на сервере - я конфигурировал django, gunicorn, postgres, rabbitmq и сам сервис отправки.


## Внутрянка
Если абстрагировать, то микросервис имеет:

* ``PostgreSQL`` используется для хранения информации по микросервисам, сообщениям;

* ``RabbitMQ`` который используется для очереди сообщений;

* ``юнит отправки`` сообщений в телеграм (используется библиотека telethon);

* ``юнит взаимодействия`` с микросервисов (используется django, взаимодействие производится с помощью RESTAPI).


## Файлы settings
Файл ``settings.json`` (внутри юнита django [tg/settings.json]) имеет формат json, с следующими ключами:

* "allowed_hosts": [list] список доступных хостов для django,

* "debug": [bool] булевое значение для сервера django,

* "secret_key": [str] строковое значение ключа криптографии для сервера django.

Файл ``settings.json`` (внутри юнита отправителя [папка sender/settings.json]) имеет формат json, с следующими ключами:

* "token": [str] строковое значение токена бота;

* "api_hash": [str] строковое значение api хеша бота,

* "api_id": [int] числовое значение айдишника бота.

Файл ``settings_database.json`` (внутри корня проекта) имеет формат json, с следующими ключами:

* "host": [str] строковое значение айпишника базы данных;

* "user": [str] строковое значение имя пользователя базы данных;

* "password": [str] строковое значение пароля пользователя базы данных;

* "database": [str] строковое значение названия базы данных;

* "port": [int] числовое значение порта базы данных.

Файл ``settings_rabbitmq.json`` (внутри корня проекта) имеет формат json, с следующими ключами:

* "host": [str] строковое значение айпишника кролика;

* "user": [str] строковое значение имя пользователя кролика;

* "password": [str] строковое значение пароля пользователя кролика;

* "port": [int] числовое значение порта кролика.


*Если возникают какие-то сложности с файлами `settings` то можно переименовать файл с базовыми настройками например `sample_settings.json` в `settings.json`.*

## Структура

`migrations` - папка с миграциями для postgres базы, используется совместно с скриптом миграций

`migrations.py` - скрипт для запуска миграций postgres;

`schema/pathts.yaml` - доступные эндпоинты для микросервиса;

`sender` - папка с юнитом отправителя сообщений ботом телеграм;

`tg` - папка с django юнитом который осуществляет логику работы микросервиса.

## Примечание
<b>!!!Микросервис еще совсем сырой, нужно много чего переделать, поэтому пока что использовать на свой страх и риск!!!</b>

По работе с виртуальными окружениями можно почитать <a href="https://docs.python.org/3/library/venv.html#how-venvs-work"> docs.python.org</a>