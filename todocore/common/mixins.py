from celery.result import AsyncResult
from common.config import config
from django.utils import timezone
from redis import Redis


class CeleryTaskMixin:
    """
    Mixin for managing Celery tasks.
    """

    redis_host = config.redis.host
    redis_port = config.redis.port
    redis_db = config.redis.db
    redis_client = Redis(host=redis_host, port=redis_port, db=redis_db)

    def schedule_task(self, task, task_id, eta) -> AsyncResult:
        """
        Schedule a Celery task and save its ID in Redis.
        """
        task_result = task.apply_async(args=[task_id], eta=eta)
        self.redis_client.set(f"task: {task_id}", task_result.id)
        return task_result

    def revoke_task(self, task_id) -> None:
        """
        Revoke a Celery task and delete its ID from Redis.
        """
        stored_task_id = self.redis_client.get(f"task : {task_id}")
        if stored_task_id:
            AsyncResult(stored_task_id.decode()).revoke()
            self.redis_client.delete(f"task: {task_id}")

    def reschedule_task(self, task, task_id, old_deadline, new_deadline) -> AsyncResult | None:
        """
        Revoke the old task and schedule a new one if the deadline has changed.
        """
        if old_deadline != new_deadline:
            notification_time = new_deadline - timezone.timedelta(hours=1)
            self.revoke_task(task_id)
            return self.schedule_task(task, task_id, notification_time)
        return None
