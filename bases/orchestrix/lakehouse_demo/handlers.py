"""Command handlers for anonymization jobs."""

from dataclasses import dataclass

from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.core.messaging import AsyncMessageBus

from .aggregate import AnonymizationJob
from .models import CreateAnonymizationJob


@dataclass
class AnonymizationHandlers:
    """Handlers for anonymization commands."""

    repository: AggregateRepository[AnonymizationJob]
    message_bus: AsyncMessageBus

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
            await self.message_bus.publish(event)


def register_handlers(
    message_bus: AsyncMessageBus, repository: AggregateRepository[AnonymizationJob]
) -> AnonymizationHandlers:
    """Register command handlers with message bus."""
    handlers = AnonymizationHandlers(repository=repository, message_bus=message_bus)

    message_bus.subscribe(CreateAnonymizationJob, handlers.handle_create_job)

    return handlers
