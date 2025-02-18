from celery.result import AsyncResult
from common.containers.client import ClientContainer
from dependency_injector.wiring import Provide
from django.utils import timezone
from redis import Redis
from task.models import TaskTypeCelery


class CeleryTaskMixin:
    """
    Mixin for managing Celery tasks.
    """

    @staticmethod
    def schedule_task(
        task,
        task_id,
        eta,
        task_type: TaskTypeCelery = TaskTypeCelery.SEND_MAIL,
        redis_client: Redis = Provide[ClientContainer.redis_client],
    ) -> AsyncResult:
        """
        Schedule a Celery task and save its ID in Redis with task type.
        """
        task_result = task.apply_async(args=[task_id], eta=eta)
        redis_key = f"task: {task_type.value}: {task_id}"
        redis_client.set(redis_key, task_result.id)
        return task_result

    @staticmethod
    def revoke_task(
        task_id,
        task_type: TaskTypeCelery = TaskTypeCelery.SEND_MAIL,
        redis_client: Redis = Provide[ClientContainer.redis_client],
    ) -> None:
        """
        Revoke a Celery task and delete its ID from Redis.
        """
        redis_key = f"task: {task_type.value}: {task_id}"
        stored_task_id = redis_client.get(redis_key)
        if stored_task_id:
            AsyncResult(stored_task_id.decode()).revoke()
            redis_client.delete(redis_key)

    def reschedule_task(
        self,
        task,
        task_id,
        old_deadline,
        new_deadline,
        task_type: TaskTypeCelery = TaskTypeCelery.SEND_MAIL,
    ) -> AsyncResult | None:
        """
        Revoke the old task and schedule a new one if the deadline has changed.
        """
        if old_deadline != new_deadline:
            notification_time = new_deadline - timezone.timedelta(hours=1)
            self.revoke_task(task_id, task_type)
            return self.schedule_task(task, task_id, notification_time, task_type)
        return None
