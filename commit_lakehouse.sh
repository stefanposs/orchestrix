#!/bin/bash
set -e

cd /Users/stefanposs/Repos/orchestrix

# Add all lakehouse example files
git add examples/lakehouse/

# Commit
git commit -m "feat: add lakehouse data anonymization example

Lakehouse Platform Example - Table Anonymization:
- Production-ready anonymization workflow
- Dry-run validation before actual anonymization
- 8 anonymization strategies (masking, hashing, pseudonymization, etc.)
- GDPR compliance (Article 5, 17, 32)
- Automatic backup before changes
- Rollback capability on failure
- Complete audit trail via event sourcing
- Saga pattern for workflow coordination

Anonymization Strategies:
1. Masking - Replace with asterisks (preserve format)
2. Hashing - SHA-256 for consistency
3. Tokenization - Random alphanumeric
4. Generalization - Reduce precision (age ranges, salary bands)
5. Suppression - Delete entirely (NULL)
6. Pseudonymization - Consistent fake data
7. Noise - Add random noise to numbers
8. Aggregation - Group into buckets

Workflow:
Create Job → Dry-Run → Validation → Backup → Anonymize → Complete
(with automatic rollback on failure)

Features:
- Sample before/after preview
- Progress tracking per column
- Estimated duration
- Warning detection
- Integration examples (Delta Lake, Iceberg, Databricks)

Example creates customers table with PII and anonymizes:
- Email: pseudonymization
- Name: pseudonymization  
- Phone: masking
- Address: suppression
- SSN: hashing
- Salary: generalization
- Credit Card: suppression

Complete with runnable demo and comprehensive documentation.
Task: Advanced Example - Lakehouse Platform ✅"

# Push to GitHub
git push origin main

echo "✅ Lakehouse example committed and pushed!"
