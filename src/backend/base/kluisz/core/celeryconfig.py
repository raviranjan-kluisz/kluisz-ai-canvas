# celeryconfig.py
import os

kluisz_redis_host = os.environ.get("KLUISZ_REDIS_HOST")
kluisz_redis_port = os.environ.get("KLUISZ_REDIS_PORT")
# broker default user

if kluisz_redis_host and kluisz_redis_port:
    broker_url = f"redis://{kluisz_redis_host}:{kluisz_redis_port}/0"
    result_backend = f"redis://{kluisz_redis_host}:{kluisz_redis_port}/0"
else:
    # RabbitMQ
    mq_user = os.environ.get("RABBITMQ_DEFAULT_USER", "kluisz")
    mq_password = os.environ.get("RABBITMQ_DEFAULT_PASS", "kluisz")
    broker_url = os.environ.get("BROKER_URL", f"amqp://{mq_user}:{mq_password}@localhost:5672//")
    result_backend = os.environ.get("RESULT_BACKEND", "redis://localhost:6379/0")
# tasks should be json or pickle
accept_content = ["json", "pickle"]
