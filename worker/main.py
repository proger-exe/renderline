import json
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pika
from config.settings import settings
from worker.processors.render_processor import RenderProcessor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_message(ch, method, properties, body):
    """Process a message from RabbitMQ"""
    task = None
    try:
        task = json.loads(body)
        logger.info(
            f"Received task: {task['task_id']} for project {task['project_id']}"
        )

        processor = RenderProcessor()
        output_path = processor.process_task(task)

        logger.info(f"Task {task['task_id']} completed successfully: {output_path}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Message acknowledged for task {task['task_id']}")
    except Exception as e:
        logger.error(f"Error processing task: {str(e)}", exc_info=True)
        # Update project status to failed
        if task:
            try:
                from database.base import SessionLocal
                from database.models import Project

                db = SessionLocal()
                project = (
                    db.query(Project).filter(Project.id == task["project_id"]).first()
                )
                if project:
                    project.status = "failed"
                    db.commit()
                    logger.info(
                        f"Project {task['project_id']} status updated to failed"
                    )
                db.close()
            except Exception as db_error:
                logger.error(f"Failed to update project status: {str(db_error)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """Main function to run the worker"""
    logger.info("Starting render worker...")

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()

    # Declare queue
    channel.queue_declare(queue=settings.rabbitmq_queue, durable=True)

    # Set QoS
    channel.basic_qos(prefetch_count=settings.worker_concurrency)

    # Start consuming
    channel.basic_consume(
        queue=settings.rabbitmq_queue, on_message_callback=process_message
    )

    logger.info(f"Waiting for messages in queue '{settings.rabbitmq_queue}'...")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Worker stopped")
