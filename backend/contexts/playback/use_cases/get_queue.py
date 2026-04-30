from shared.domain.interfaces import QueueManager


class GetQueueUseCase:
    def __init__(self, queue_manager: QueueManager):
        self.queue_manager = queue_manager

    async def execute(self) -> dict:
        tracks = await self.queue_manager.get_all()
        current = await self.queue_manager.get_current()

        return {
            "tracks": [t.model_dump() for t in tracks] if tracks else [],
            "current_id": current.id if current else None,
        }
