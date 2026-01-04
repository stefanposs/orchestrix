"""E-commerce example demonstrating order processing with sagas.

This example shows:
- OrderAggregate with state machine
- Multi-aggregate saga (Order → Payment → Inventory)
- Event handlers for notifications
- Saga coordinator pattern with compensation
"""
