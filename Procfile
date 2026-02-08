web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
worker: celery -A backend.tasks worker --loglevel=info
beat: celery -A backend.tasks beat --loglevel=info
