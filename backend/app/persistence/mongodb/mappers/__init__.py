"""Mappers sub-package.

Each mapper module provides two pure functions:

``to_document(domain_model) -> Document``
    Convert a domain model to its Mongo document representation.

``to_domain(document) -> DomainModel``
    Convert a raw Mongo document to the corresponding domain model.

Mappers contain zero business logic — they are mechanical translations
between the persistence schema and the domain layer.
"""
