#!/bin/bash



celery -A todo__core worker --loglevel=info &

celery -A todo__core beat --loglevel=info
