"""Command handlers for anonymization jobs."""
from dataclasses import dataclass
from datetime import datetime, timezone

from orchestrix.core.aggregate import AggregateRepository
from orchestrix.core.messaging import MessageBus

from .aggregate import AnonymizationJob
from .models import CreateAnonymizationJob


@dataclass
class AnonymizationHandlers:
    """Handlers for anonymization commands."""

    repository: AggregateRepository
    message_bus: MessageBus

    async def handle_create_job(self, command: CreateAnonymizationJob) -> None:
        """Create a new anonymization job."""
        job = AnonymizationJob()
        job.create(
            job_id=command.job_id,
            table_schema=command.table_schema,
            rules=command.rules,
            requester=command.requester,
            reason=command.reason,
        )

        await self.repository.save_async(job)

        # Publish events
        for event in job.uncommitted_events:
            await self.message_bus.publish_async(event)


def register_handlers(
    message_bus: MessageBus, repository: AggregateRepository
) -> AnonymizationHandlers:
    """Register command handlers with message bus."""
    handlers = AnonymizationHandlers(repository=repository, message_bus=message_bus)

    message_bus.subscribe(CreateAnonymizationJob, handlers.handle_create_job)

    return handlers
