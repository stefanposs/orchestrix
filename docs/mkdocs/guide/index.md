# Production Documentation Index

Welcome to Orchestrix production documentation! This page helps you navigate the different guides based on your needs.

## 📚 Documentation Overview

### For New Projects

**Start here if you're planning a new Orchestrix deployment:**

1. **[Production Deployment Guide](production-deployment.md)** - **(RECOMMENDED)**
   - Complete guide for all project sizes (small/medium/large)
   - Infrastructure recommendations based on scale
   - Step-by-step deployment instructions
   - Migration paths between tiers
   - **Choose this if:** You want comprehensive guidance on the right architecture for your scale

### For Production Readiness

**Use these when preparing for production launch:**

2. **[Production Readiness Guide](production-ready.md)**
   - Detailed production checklist
   - System requirements
   - Environment setup
   - Monitoring and observability
   - Security considerations
   - **Choose this if:** You need a comprehensive pre-launch checklist

### For Specific Topics

3. **[Best Practices](best-practices.md)**
   - Domain modeling patterns
   - Error handling strategies
   - Event design guidelines
   - Testing approaches
   - **Choose this if:** You want to improve code quality and architecture

4. **[Event Store Guide](event-store.md)**
   - EventStore implementations comparison
   - PostgreSQL vs EventSourcingDB vs InMemory
   - Performance tuning
   - Backup strategies
   - **Choose this if:** You need deep dive into event persistence

5. **[Message Bus Guide](message-bus.md)**
   - MessageBus patterns
   - Sync vs Async
   - Error handling
   - Performance optimization
   - **Choose this if:** You're building complex message routing logic

### Additional Resources

6. **[Creating Modules](creating-modules.md)**
   - Module design patterns
   - Registration best practices
   - Dependency injection
   - **Choose this if:** You're structuring your application domains

7. **[Commands & Events](commands-events.md)**
   - Message design patterns
   - Validation strategies
   - CloudEvents compatibility
   - **Choose this if:** You're designing your domain messages

---

## 🎯 Quick Decision Tree

**"What documentation do I need?"**

```
Are you starting a new project?
├─ Yes → Start with Production Deployment Guide
│  └─ What's your scale?
│     ├─ < 10k events/month → Small Projects section
│     ├─ 10k-100k events/month → Medium Projects section
│     └─ > 100k events/month → Large Projects section
│
└─ No → Do you have an existing project?
   ├─ Preparing for launch → Production Readiness Guide
   ├─ Improving code quality → Best Practices
   ├─ Performance issues → Event Store Guide + Message Bus Guide
   └─ Learning patterns → Creating Modules + Commands & Events
```

---

## 📊 Documentation Comparison

| Guide | Audience | Scope | Length | When to Use |
|-------|----------|-------|--------|-------------|
| [Production Deployment](production-deployment.md) | DevOps, Architects | Infrastructure & scaling | Comprehensive | Planning deployment |
| [Production Readiness](production-ready.md) | DevOps, Engineers | Launch checklist | Detailed | Pre-launch audit |
| [Best Practices](best-practices.md) | Developers | Code quality | Focused | Daily development |
| [Event Store Guide](event-store.md) | Developers, DevOps | Persistence | Technical | Storage decisions |
| [Message Bus Guide](message-bus.md) | Developers | Messaging | Technical | Routing complexity |
| [Creating Modules](creating-modules.md) | Developers | Architecture | Tutorial | Domain modeling |
| [Commands & Events](commands-events.md) | Developers | Messages | Tutorial | Message design |

---

## 🚀 Recommended Reading Paths

### Path 1: Complete Beginner
1. [Installation](../getting-started/installation.md)
2. [Quick Start](../getting-started/quick-start.md)
3. [Core Concepts](../getting-started/concepts.md)
4. [Creating Modules](creating-modules.md)
5. [Commands & Events](commands-events.md)
6. [Examples](../examples/index.md)

### Path 2: Production Launch
1. [Production Deployment Guide](production-deployment.md) - Choose your scale
2. [Production Readiness Guide](production-ready.md) - Complete checklist
3. [Best Practices](best-practices.md) - Code quality review
4. [Event Store Guide](event-store.md) - Storage configuration
5. [Examples: Observability](../examples/metrics.md) - Monitoring setup

### Path 3: Scaling Existing Project
1. [Production Deployment Guide](production-deployment.md) - Review migration paths
2. [Event Store Guide](event-store.md) - Upgrade storage
3. [Message Bus Guide](message-bus.md) - Consider async patterns
4. [Best Practices](best-practices.md) - Refactoring guidance
5. [Examples: Performance](../examples/projections.md) - Optimization techniques

### Path 4: Architecture Deep Dive
1. [Core Concepts](../getting-started/concepts.md)
2. [Architecture](../development/architecture.md)
3. [Best Practices](best-practices.md)
4. [Creating Modules](creating-modules.md)
5. [Event Store Guide](event-store.md)
6. [Message Bus Guide](message-bus.md)

---

## 💡 Tips for Using This Documentation

### For Quick Reference
- Use the **search bar** (top of page) to find specific topics
- Bookmark the **index pages** for each section
- Check **code examples** for copy-paste templates

### For Learning
- Follow the **recommended reading paths** above
- Work through **examples** hands-on
- Reference **API documentation** when stuck

### For Production
- Complete the **production readiness checklist**
- Review **all best practices** relevant to your domain
- Test **deployment procedures** in staging first

---

## 🔗 See Also

- **[Examples](../examples/index.md)** - Working code samples
- **[API Reference](../api/core.md)** - Detailed API documentation
- **[Architecture](../development/architecture.md)** - Design decisions
- **[Contributing](../development/contributing.md)** - Join development

---

## 📮 Need Help?

Can't find what you're looking for?

- 📖 [Search Documentation](https://orchestrix.readthedocs.io)
- 🐛 [Report Issue](https://github.com/stefanposs/orchestrix/issues)
- 💬 [Discussion Forum](https://github.com/stefanposs/orchestrix/discussions)
- 📧 [Contact Support](mailto:stefan@example.com)
