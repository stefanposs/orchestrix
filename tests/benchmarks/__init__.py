"""Orchestrix Benchmark Suite.

Performance baseline tests using pytest-benchmark to ensure the framework
maintains acceptable performance characteristics.

Running benchmarks:
    pytest benchmarks/ -v

Running with profiling:
    pytest benchmarks/ --benchmark-histogram

Comparing with baseline:
    pytest benchmarks/ --benchmark-compare=baseline

Goals:
- Message throughput: >1,000 messages/sec
- Event store operations: >10,000 events/sec (in-memory)
- Saga coordination: <10ms per state transition
- Memory efficiency: <100MB for 100k events
"""
