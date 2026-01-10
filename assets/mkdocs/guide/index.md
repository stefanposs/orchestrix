
# Orchestrix Documentation Overview

Welcome to Orchestrix! Orchestrix is an event-sourcing framework built for modern enterprises, AI-driven development, and rapid code iteration. It provides a robust, future-proof foundation for modeling, managing, and evolving your business processes, commands, and events—ensuring your data, knowledge, and workflows remain consistent, auditable, and under your control.

**Why Orchestrix?**

- In the age of AI, fast prototyping, and ever-changing systems, your business processes are your most valuable digital assets. Orchestrix helps you keep them versioned, governed, and ready to scale.
- Traditional CRUD systems lose history and context. Orchestrix captures every change as a versioned event, making your systems audit-ready and reproducible.
- Designed for readability, scalability, extensibility, and maintainability, Orchestrix empowers teams to innovate quickly—without sacrificing data quality or compliance.

**Key Use Cases:**

- Enterprises with many applications and fragmented business logic
- AI-driven and rapidly evolving software landscapes
- Systems requiring audit trails, compliance, and process governance
- Teams seeking a clear, scalable, and maintainable architecture

---


## 📚 Documentation Overview

### For New Projects

**Start here if you're planning a new Orchestrix deployment:**


1. **[Production Deployment Guide](production-deployment.md)** *(Recommended)*
   - End-to-end deployment for all project sizes
   - Infrastructure guidance for scaling
   - Migration strategies
   - Choose this for a solid, scalable foundation


### For Production Readiness

**Use these when preparing for production launch:**


2. **[Production Readiness Guide](production-ready.md)**
   - Launch checklist
   - Monitoring, observability, and security
   - Environment setup
   - Choose this for a reliable go-live


### For Specific Topics

3. **[Best Practices](best-practices.md)**
   - Domain modeling, error handling, event design, testing
   - Choose this to improve code quality and architecture


4. **[Event Store Guide](event-store.md)**
   - Compare event store implementations
   - Performance and backup strategies
   - Choose this for deep event persistence insights


5. **[Message Bus Guide](message-bus.md)**
   - Message bus patterns, sync/async, error handling, performance
   - Choose this for advanced routing logic


### Additional Resources

6. **[Creating Modules](creating-modules.md)**
   - Module design, registration, dependency injection
   - Choose this for domain-driven architecture


7. **[Commands & Events](commands-events.md)**
   - Message design, validation, CloudEvents compatibility
   - Choose this for robust domain messaging

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
6. [Demos](../demos/index.md)

### Path 2: Production Launch
1. [Production Deployment Guide](production-deployment.md) - Choose your scale
2. [Production Readiness Guide](production-ready.md) - Complete checklist
3. [Best Practices](best-practices.md) - Code quality review
4. [Event Store Guide](event-store.md) - Storage configuration
5. [Demos: Observability](../demos/projection.md) - Monitoring setup

### Path 3: Scaling Existing Project
1. [Production Deployment Guide](production-deployment.md) - Review migration paths
2. [Event Store Guide](event-store.md) - Upgrade storage
3. [Message Bus Guide](message-bus.md) - Consider async patterns
4. [Best Practices](best-practices.md) - Refactoring guidance
5. [Demos: Performance](../demos/projection.md) - Optimization techniques

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

- **[Demos](../demos/index.md)** - Working code samples
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
