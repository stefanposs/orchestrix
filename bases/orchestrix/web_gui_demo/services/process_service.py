"""Process service for managing predefined processes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .data_service import DataService


class ProcessService:
    """Service for managing predefined processes that can be executed."""

    def __init__(self) -> None:
        """Initialize process service with predefined processes."""
        self.processes: list[dict[str, Any]] = [
            {
                "id": "PROC-001",
                "name": "E-Commerce Order Flow",
                "description": "Complete order processing: Create → Pay → Ship",
                "command_sequence": [
                    {
                        "command_type": "CreateOrder",
                        "data_template": {
                            "order_id": "ORD-{timestamp}",
                            "customer_name": "Customer",
                            "total_amount": 99.99,
                        },
                    },
                    {
                        "command_type": "ProcessPayment",
                        "data_template": {
                            "order_id": "ORD-{timestamp}",
                            "payment_id": "PAY-{timestamp}",
                            "amount": 99.99,
                            "method": "credit_card",
                        },
                    },
                ],
                "category": "E-Commerce",
                "created_at": "2026-01-01",
            },
            {
                "id": "PROC-002",
                "name": "Order Cancellation",
                "description": "Cancel an existing order",
                "command_sequence": [
                    {
                        "command_type": "CancelOrder",
                        "data_template": {
                            "order_id": "ORD-{order_id}",
                        },
                    },
                ],
                "category": "E-Commerce",
                "created_at": "2026-01-01",
            },
            {
                "id": "PROC-003",
                "name": "Batch Order Creation",
                "description": "Create multiple orders at once",
                "command_sequence": [
                    {
                        "command_type": "CreateOrder",
                        "data_template": {
                            "order_id": "ORD-{index}",
                            "customer_name": "Customer {index}",
                            "total_amount": "{amount}",
                        },
                        "repeat": 5,
                    },
                ],
                "category": "Batch Operations",
                "created_at": "2026-01-01",
            },
        ]

    def get_all_processes(self) -> list[dict[str, Any]]:
        """Get all predefined processes.

        Returns:
            List of process dictionaries

        """
        return self.processes

    def get_process_by_id(self, process_id: str) -> dict[str, Any] | None:
        """Get a process by ID.

        Args:
            process_id: The process ID

        Returns:
            Process dictionary or None if not found

        """
        return next((p for p in self.processes if p["id"] == process_id), None)

    def add_process(self, process: dict[str, Any]) -> None:
        """Add a new process.

        Args:
            process: Process dictionary

        """
        self.processes.append(process)

    def execute_process(
        self, process_id: str, data_service: DataService, **kwargs: str
    ) -> dict[str, Any]:
        """Execute a process by dispatching its commands.

        Args:
            process_id: The process ID to execute
            data_service: DataService instance for dispatching commands
            **kwargs: Additional parameters for command templates

        Returns:
            Result dictionary with status and executed commands

        """
        process = self.get_process_by_id(process_id)
        if not process:
            return {"status": "error", "message": f"Process {process_id} not found"}

        executed_commands = []
        errors = []

        for cmd_def in process["command_sequence"]:
            command_type = cmd_def["command_type"]
            data_template = cmd_def.get("data_template", {})
            repeat = cmd_def.get("repeat", 1)

            # Replace template variables
            import time

            timestamp = int(time.time())
            for i in range(repeat):
                data = {}
                for key, value in data_template.items():
                    if isinstance(value, str):
                        # Replace template variables
                        data[key] = (
                            value.replace("{timestamp}", str(timestamp))
                            .replace("{index}", str(i))
                            .replace("{order_id}", kwargs.get("order_id", "ORD-001"))
                            .replace("{amount}", str(kwargs.get("amount", 99.99)))
                        )
                    else:
                        data[key] = value

                result = data_service.dispatch_command(command_type, data)
                executed_commands.append({"command": command_type, "data": data, "result": result})
                if result["status"] == "error":
                    errors.append(result["message"])

        if errors:
            return {
                "status": "partial",
                "message": f"Process executed with {len(errors)} errors",
                "executed_commands": executed_commands,
                "errors": errors,
            }

        return {
            "status": "success",
            "message": f"Process {process_id} executed successfully",
            "executed_commands": executed_commands,
        }
