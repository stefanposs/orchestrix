# Orchestrix Benchmarks

Performance baseline tests for the Orchestrix event sourcing framework.

## Running Benchmarks

### Prerequisites

```bash
pip install -e ".[dev]"
```

### Run All Benchmarks

```bash
pytest benchmarks/ -v
```

### Run Specific Benchmark Group

```bash
# Message bus benchmarks
pytest benchmarks/test_message_bus_benchmark.py -v

# Event store benchmarks
pytest benchmarks/test_event_store_benchmark.py -v
```

### Generate Histogram

```bash
pytest benchmarks/ --benchmark-histogram
```

### Save Baseline

```bash
pytest benchmarks/ --benchmark-save=baseline
```

### Compare with Baseline

```bash
pytest benchmarks/ --benchmark-compare=baseline
```

### Only Run Fast Benchmarks

```bash
pytest benchmarks/ -m "not slow"
```

## Performance Targets

### Message Bus
- **Single message**: <1ms
- **1,000 messages**: <1 second (>1,000 msg/sec)
- **Concurrent publishes**: Linear scaling up to CPU cores

### Event Store (In-Memory)
- **Single event save**: <0.1ms
- **10,000 events save**: <100ms (>100,000 events/sec)
- **10,000 events load**: <50ms (>200,000 events/sec)
- **Snapshot operations**: <1ms

### Memory Usage
- **100,000 events**: <100MB
- **1,000,000 events**: <1GB

## Benchmark Structure

### test_message_bus_benchmark.py
- Single message publishing
- Batch publishing (100, 1,000 messages)
- Multiple handlers (5, 10 handlers)
- Payload sizes (small, medium, large)
- Concurrent publishing (10, 100 messages)

### test_event_store_benchmark.py
- Single event operations (save, load)
- Batch operations (100, 1,000, 10,000 events)
- Partial loading (from version)
- Snapshot operations
- Multiple aggregates
- Concurrent operations

## Interpreting Results

### Example Output

```
--------------------------------------------------------------------------------------- benchmark: 12 tests ------------------------------------------------------------------------
Name (time in us)                              Min                 Max                Mean            StdDev              Median               IQR            Outliers       OPS            Rounds  Iterations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_publish_single_command                 12.1000 (1.0)       45.2000 (1.0)       14.3500 (1.0)      2.1000 (1.0)       13.9000 (1.0)      1.3000 (1.0)          15;18  69,686.4115 (1.0)         500           1
test_save_single_event                      23.4000 (1.93)      78.9000 (1.75)      26.1500 (1.82)     3.4000 (1.62)      25.3000 (1.82)     2.1000 (1.62)          8;12  38,240.9172 (0.55)        400           1
```

### Key Metrics
- **Min/Max**: Best and worst execution times
- **Mean**: Average execution time
- **Median**: Middle value (more robust than mean)
- **StdDev**: Consistency of results
- **OPS**: Operations per second
- **Rounds**: How many times the benchmark ran

### Performance Issues
- **High StdDev**: Inconsistent performance (investigate caching, GC)
- **Many Outliers**: Check for background processes
- **Slow OPS**: Compare with targets above

## Profiling

### CPU Profiling

```bash
pytest benchmarks/test_message_bus_benchmark.py::test_publish_1000_messages \
    --benchmark-cprofile=tottime
```

### Memory Profiling

```bash
pytest benchmarks/test_event_store_benchmark.py::test_save_10000_events \
    --benchmark-cprofile=cumulative
```

## CI/CD Integration

Benchmarks run automatically on each PR to detect performance regressions:

```yaml
# .github/workflows/benchmarks.yml
- name: Run benchmarks
  run: pytest benchmarks/ --benchmark-compare=baseline --benchmark-compare-fail=mean:10%
```

This fails the build if performance degrades by >10% compared to baseline.

## Adding New Benchmarks

### Benchmark Template

```python
import pytest
import asyncio
from orchestrix.infrastructure import InMemoryMessageBus

@pytest.mark.benchmark(group="your-group")
def test_your_benchmark(benchmark):
    \"\"\"Describe what this benchmark measures.\"\"\"
    # Setup
    bus = InMemoryMessageBus()
    
    # Benchmark function
    async def operation():
        # Your code here
        pass
    
    # Run benchmark
    benchmark(lambda: asyncio.run(operation()))
```

### Best Practices
1. **Isolate setup**: Don't include setup time in benchmark
2. **Use realistic data**: Match production scenarios
3. **Document expectations**: Add docstring with expected range
4. **Test at scale**: Include large-scale scenarios (1k, 10k, 100k)
5. **Group related tests**: Use `@pytest.mark.benchmark(group="...")`

## Troubleshooting

### Benchmarks too slow
```bash
# Run only fast benchmarks
pytest benchmarks/ -k "not 10000"
```

### Inconsistent results
```bash
# Increase rounds to get more stable results
pytest benchmarks/ --benchmark-min-rounds=100
```

### Compare specific benchmarks
```bash
pytest benchmarks/ --benchmark-only --benchmark-compare=baseline \
    -k "test_publish_1000_messages"
```

## Related Documentation

- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [Performance Guide](../docs/performance.md)
- [Optimization Tips](../docs/optimization.md)
