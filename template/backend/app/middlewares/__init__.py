"""General-purpose HTTP middlewares.

Placement rule: cross-cutting, domain-agnostic HTTP middlewares live here
(e.g., RequestContextMiddleware, which populates request-scoped identity).
Domain-coupled middlewares stay with their feature package — for example,
WideEventMiddleware lives in app/core/logging/middleware.py because it is
wired to the logging subsystem's WideEventContext and emits wide-event logs.
"""
