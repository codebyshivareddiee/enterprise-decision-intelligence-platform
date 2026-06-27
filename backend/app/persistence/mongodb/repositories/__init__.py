"""Repositories sub-package.

Each repository encapsulates all Motor calls for a single aggregate.
Repositories return domain models — never raw Mongo documents.

Repositories expose only generic CRUD operations:
    create(), get_by_id(), list(), update(), delete()

No business logic lives here.
"""
