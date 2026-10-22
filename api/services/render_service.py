import json
import pika
from config.settings import settings
from typing import Dict, Any
import uuid


def submit_render_task(
    project_id: int, execution_plan: Dict[str, Any], owner_id: int = None
) -> str:
    """Submit render task to RabbitMQ queue"""
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()

    # Declare queue
    channel.queue_declare(queue=settings.rabbitmq_queue, durable=True)

    # Create task
    task_id = str(uuid.uuid4())
    task = {
        "task_id": task_id,
        "project_id": project_id,
        "owner_id": owner_id,
        "execution_plan": execution_plan,
    }

    # Publish task
    channel.basic_publish(
        exchange="",
        routing_key=settings.rabbitmq_queue,
        body=json.dumps(task),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        ),
    )

    connection.close()
    return task_id
