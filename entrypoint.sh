#!/bin/bash

# Выполняем миграции
python manage.py migrate --noinput



# Запускаем Django
exec "$@"