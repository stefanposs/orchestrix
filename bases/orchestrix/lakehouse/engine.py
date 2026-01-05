"""Anonymization strategies implementation."""

import hashlib
import random
import string
from dataclasses import dataclass
from typing import Any


@dataclass
class AnonymizationEngine:
    """Engine for applying anonymization strategies."""

    seed: int = 42  # For reproducible pseudonymization

    def masking(self, value: str, preserve_format: bool = False) -> str:
        """Replace characters with asterisks."""
        if not value:
            return value

        if preserve_format:
            # Keep format (e.g., email: a***@e******.com)
            if "@" in value:  # Email
                local, domain = value.split("@", 1)
                domain_parts = domain.split(".")
                return f"{local[0]}***@{domain_parts[0][0]}{'*' * (len(domain_parts[0]) - 1)}.{domain_parts[-1]}"
            if "-" in value:  # Phone with dashes
                parts = value.split("-")
                return "-".join("*" * len(part) for part in parts)

        # Simple masking
        if len(value) <= 4:
            return "*" * len(value)
        return value[:2] + "*" * (len(value) - 4) + value[-2:]

    def hashing(self, value: str) -> str:
        """Generate SHA-256 hash."""
        if not value:
            return value
        return hashlib.sha256(value.encode()).hexdigest()

    def tokenization(self, value: str, length: int | None = None) -> str:
        """Replace with random token."""
        if not value:
            return value
        token_length = length or len(value)
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=token_length))

    def generalization(self, value: str | int | float, value_type: str) -> str:
        """Reduce precision/specificity."""
        if value is None:
            return None

        if value_type == "age":
            # Age ranges: 0-17, 18-29, 30-39, 40-49, 50-59, 60+
            age = int(value)
            if age < 18:
                return "0-17"
            if age < 30:
                return "18-29"
            if age < 40:
                return "30-39"
            if age < 50:
                return "40-49"
            if age < 60:
                return "50-59"
            return "60+"

        if value_type == "salary":
            # Salary ranges
            salary = float(value)
            if salary < 30000:
                return "<30k"
            if salary < 50000:
                return "30k-50k"
            if salary < 75000:
                return "50k-75k"
            if salary < 100000:
                return "75k-100k"
            if salary < 150000:
                return "100k-150k"
            return "150k+"

        if value_type == "date":
            # Only keep year
            if isinstance(value, str):
                return value[:4]
            return str(value)

        if value_type == "zipcode":
            # Keep only first 3 digits
            return str(value)[:3] + "**"

        return str(value)

    def suppression(self, value: str) -> None:
        """Delete value entirely."""
        return

    def pseudonymization(self, value: str, value_type: str) -> str:
        """Replace with consistent fake data."""
        if not value:
            return value

        # Use hash as seed for consistency
        hash_val = int(hashlib.md5(value.encode()).hexdigest()[:8], 16)
        random.seed(hash_val)

        if value_type == "email":
            names = ["john", "jane", "alice", "bob", "charlie", "diana", "eve", "frank"]
            domains = ["example", "test", "demo", "sample"]
            tlds = ["com", "org", "net"]
            name = random.choice(names)
            domain = random.choice(domains)
            tld = random.choice(tlds)
            return f"{name}{random.randint(1, 999)}@{domain}.{tld}"

        if value_type == "name":
            first_names = [
                "John",
                "Jane",
                "Alice",
                "Bob",
                "Charlie",
                "Diana",
                "Eve",
                "Frank",
            ]
            last_names = [
                "Smith",
                "Johnson",
                "Williams",
                "Brown",
                "Jones",
                "Garcia",
                "Miller",
            ]
            return f"{random.choice(first_names)} {random.choice(last_names)}"

        if value_type == "phone":
            return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"

        if value_type == "address":
            streets = ["Main St", "Oak Ave", "Elm St", "Maple Dr", "Pine Rd"]
            cities = ["Springfield", "Franklin", "Clinton", "Georgetown", "Salem"]
            states = ["CA", "NY", "TX", "FL", "IL"]
            return f"{random.randint(100, 9999)} {random.choice(streets)}, {random.choice(cities)}, {random.choice(states)}"

        # Generic pseudonymization
        return self.tokenization(value)

    def aggregation(self, values: list[Any], bucket_size: int = 5) -> str | None:
        """Aggregate into buckets."""
        if not values:
            return None
        avg = sum(float(v) for v in values if v is not None) / len(values)
        return f"~{avg:.0f}"

    def noise(self, value: float, noise_percent: float = 10.0) -> float:
        """Add random noise to numeric values."""
        if value is None:
            return None
        noise_amount = value * (noise_percent / 100.0)
        noise_value = random.uniform(-noise_amount, noise_amount)
        return value + noise_value


# Simulated data store


@dataclass
class LakehouseTable:
    """Simulated lakehouse table."""

    database: str
    schema_name: str
    table_name: str
    data: list[dict[str, Any]]
    _backup: list[dict[str, Any]] | None = None

    def backup(self) -> str:
        """Create backup before anonymization."""
        self._backup = [row.copy() for row in self.data]
        backup_location = (
            f"s3://backups/{self.database}/{self.schema_name}/{self.table_name}/backup.parquet"
        )
        return backup_location

    def restore(self) -> None:
        """Restore from backup."""
        if self._backup:
            self.data = [row.copy() for row in self._backup]
            self._backup = None

    def anonymize_column(
        self,
        column_name: str,
        engine: AnonymizationEngine,
        strategy_name: str,
        preserve_format: bool = False,
        preserve_null: bool = True,
        **kwargs: Any,
    ) -> int:
        """Anonymize a specific column."""
        rows_affected = 0

        for row in self.data:
            if column_name not in row:
                continue

            value = row[column_name]

            # Preserve NULL if requested
            if preserve_null and value is None:
                continue

            # Apply strategy
            if strategy_name == "masking":
                row[column_name] = engine.masking(str(value), preserve_format)
            elif strategy_name == "hashing":
                row[column_name] = engine.hashing(str(value))
            elif strategy_name == "tokenization":
                row[column_name] = engine.tokenization(str(value))
            elif strategy_name == "generalization":
                row[column_name] = engine.generalization(value, kwargs.get("value_type", "generic"))
            elif strategy_name == "suppression":
                row[column_name] = None
            elif strategy_name == "pseudonymization":
                row[column_name] = engine.pseudonymization(
                    str(value), kwargs.get("value_type", "generic")
                )
            elif strategy_name == "noise":
                row[column_name] = engine.noise(float(value), kwargs.get("noise_percent", 10.0))

            rows_affected += 1

        return rows_affected

    def get_sample(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get sample rows."""
        return self.data[:limit]
