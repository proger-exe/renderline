import json
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from worker.renderer.ffmpeg_renderer import FFmpegRenderer
from worker.renderer.subtitle_generator import SubtitleGenerator
from config.settings import settings
from database.base import SessionLocal
from database.models import Project

logger = logging.getLogger(__name__)


class RenderProcessor:
    """Process render tasks"""

    def __init__(self):
        self.renderer = FFmpegRenderer()
        self.subtitle_generator = SubtitleGenerator()

    def process_task(self, task: dict) -> str:
        """Process a render task and return output file path"""
        task_id = task["task_id"]
        project_id = task["project_id"]
        execution_plan = task["execution_plan"]

        logger.info(f"Processing render task {task_id} for project {project_id}")

        db = SessionLocal()
        project = None
        try:
            # Update status to rendering
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = "rendering"
                db.commit()

            # Generate subtitles ASS file
            subtitles = execution_plan.get("subtitles", [])
            preset = execution_plan.get("preset", "tiktok")
            ass_file = None
            if subtitles:
                logger.info(
                    f"Generating subtitles ASS file for {len(subtitles)} subtitles"
                )
                ass_file = self.subtitle_generator.generate_ass(
                    subtitles=subtitles,
                    output_path=settings.storage_output_path
                    / f"{task_id}_subtitles.ass",
                    preset=preset,
                )
                logger.info(f"Subtitle file generated: {ass_file}")
            else:
                logger.info("No subtitles in execution plan")

            # Render video
            output_path = settings.storage_output_path / f"{task_id}_output.mp4"
            logger.info(f"Starting render to: {output_path}")
            self.renderer.render(
                execution_plan=execution_plan,
                output_path=output_path,
                subtitle_file=ass_file,
            )
            logger.info(f"Render finished, checking output file: {output_path}")

            # Verify output file exists
            if not output_path.exists():
                raise Exception(f"Output file was not created: {output_path}")

            logger.info(f"Output file exists, size: {output_path.stat().st_size} bytes")

            # Update status to completed and save output path
            if project:
                project.status = "completed"
                project.output_path = str(output_path)
                db.commit()
                logger.info(
                    f"Project {project_id} status updated to completed, output_path: {output_path}"
                )
            else:
                logger.warning(f"Project {project_id} not found in database")

            logger.info(f"Render task {task_id} completed successfully: {output_path}")
            return str(output_path)
        except Exception as e:
            # Update status to failed
            if project:
                project.status = "failed"
                db.commit()
            logger.error(f"Render task {task_id} failed: {str(e)}")
            raise
        finally:
            db.close()
