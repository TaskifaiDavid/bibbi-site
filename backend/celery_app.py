from celery import Celery
from celery.schedules import crontab
from celery.signals import task_prerun, task_postrun, task_failure, task_success
from app.utils.config import get_settings
from app.utils.logging_config import get_logger, LoggingContext
import logging
import os
import time

logger = get_logger(__name__)

settings = get_settings()

# Create Celery app with enhanced configuration
celery_app = Celery(
    "bibbi_cleaner",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.processing', 'app.tasks.ai_tasks', 'app.tasks.maintenance']
)

# Enhanced Celery configuration
celery_app.conf.update(
    # Timezone settings
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Enhanced worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    worker_send_task_events=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    result_compression='gzip',
    
    # Task routing and priority
    task_default_queue='default',
    task_routes={
        'app.tasks.ai_tasks.*': {'queue': 'ai_processing'},
        'app.tasks.processing.*': {'queue': 'file_processing'},
        'app.tasks.maintenance.*': {'queue': 'maintenance'},
    },
    
    # Performance settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_pool_limit=10,
    
    # Security settings
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Monitoring and visibility
    task_send_sent_event=True,
    worker_send_task_events=True,
    task_track_started=True,
    
    # Beat scheduler settings for periodic tasks
    beat_schedule={
        'cleanup-old-uploads': {
            'task': 'app.tasks.maintenance.cleanup_old_uploads',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        'cleanup-old-conversations': {
            'task': 'app.tasks.maintenance.cleanup_old_conversations',
            'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        'health-check': {
            'task': 'app.tasks.maintenance.system_health_check',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes
        },
    },
)

# Task monitoring and logging
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwargs_extra):
    """Log task start with context"""
    with LoggingContext(request_id=task_id):
        logger.info(
            f"Task started: {task.name}",
            extra={
                "task_id": task_id,
                "task_name": task.name,
                "args_count": len(args) if args else 0,
                "kwargs_keys": list(kwargs.keys()) if kwargs else []
            }
        )

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kwargs_extra):
    """Log task completion"""
    with LoggingContext(request_id=task_id):
        logger.info(
            f"Task completed: {task.name}",
            extra={
                "task_id": task_id,
                "task_name": task.name,
                "state": state,
                "duration": getattr(task, '_start_time', None) and time.time() - task._start_time
            }
        )

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs_extra):
    """Log task failures with detailed information"""
    with LoggingContext(request_id=task_id):
        logger.error(
            f"Task failed: {sender.name}",
            extra={
                "task_id": task_id,
                "task_name": sender.name,
                "error_type": type(exception).__name__,
                "error_message": str(exception)
            },
            exc_info=True
        )

@task_success.connect  
def task_success_handler(sender=None, result=None, **kwargs):
    """Log successful task completion"""
    logger.debug(f"Task succeeded: {sender.name}")

# Custom task base class with enhanced features
class EnhancedTask(celery_app.Task):
    """Enhanced task class with retry logic and monitoring"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(
            f"Task {self.name} failed permanently after retries",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "error": str(exc),
                "args": args,
                "kwargs": kwargs
            },
            exc_info=True
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        logger.warning(
            f"Task {self.name} retrying",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "error": str(exc),
                "retry_count": self.request.retries
            }
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(
            f"Task {self.name} completed successfully",
            extra={
                "task_id": task_id,
                "task_name": self.name
            }
        )

# Set the enhanced task class as default
celery_app.Task = EnhancedTask

if __name__ == "__main__":
    celery_app.start()