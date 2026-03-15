from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.orm import (
    DeclarativeBase,
    InstrumentedAttribute,
    Load,
    RelationshipProperty,
)

from .ast import ASTNode, LoadOnlyNode, RelationshipLoadNode, safe_getattr
from .code_generator import QueryOptionGenerator
from loguru import logger

from .pydantic_fields import PydanticGraph


class StatementGenerator:
    """Generates SQLAlchemy select statements based on Pydantic models."""

    def __init__(self, graph: PydanticGraph, model: type[DeclarativeBase]):
        self.model = model
        self.graph = graph

    def generate_query(self) -> Sequence[Load]:
        """Generate the SQLAlchemy select statement."""
        ast = self._build_ast()
        generator = QueryOptionGenerator()

        return [generator.visit(node) for node in ast.children]

    def _build_ast(self) -> ASTNode:
        return ASTNode(
            self.model, list(self._build_child_nodes(self.model, self.graph))
        )

    def _build_relationship_nodes(
        self, model: type[DeclarativeBase], graph: PydanticGraph
    ) -> list[ASTNode]:
        """Recursively build relationship nodes."""
        nodes: list[ASTNode] = []

        columns, relationships = self._categorize_columns(
            model, list(graph.relationships.keys())
        )
        if columns:
            nodes.append(LoadOnlyNode(model, [], columns))

        for relationship_name, orm_relationship in relationships:
            sub_graph = graph.relationships[relationship_name]
            relationship_node = RelationshipLoadNode(
                model=model,
                children=list(self._build_child_nodes(orm_relationship, sub_graph)),
                relationship=relationship_name,
            )

            nodes.append(relationship_node)
        return nodes

    def _build_child_nodes(
        self, model: type[DeclarativeBase], graph: PydanticGraph
    ) -> Sequence[ASTNode]:
        columns, _ = self._categorize_columns(model, graph.columns)

        nodes: list[ASTNode] = []
        if columns:
            nodes.append(LoadOnlyNode(model, [], columns))
        nodes.extend(self._build_relationship_nodes(model, graph))
        return nodes

    def _get_orm_relation(
        self, model: type[DeclarativeBase], relationship_name: str
    ) -> type[DeclarativeBase]:
        """Get the related model class for a relationship."""
        try:
            mapper = inspect(model)
            relationship_prop = mapper.relationships[relationship_name]
            return relationship_prop.mapper.class_
        except KeyError:
            raise AttributeError(
                f"Relationship `{relationship_name}` not found in model {model}"
            ) from None

    def _categorize_columns(
        self, model: type[DeclarativeBase], columns: list[str]
    ) -> tuple[list[str], list[tuple[str, type[DeclarativeBase]]]]:
        """
        Categorize columns into relationships and scalars,
        skipping properties and non-sqlalchemy attributes.

        Args:
            model: The SQLAlchemy model to inspect.
            columns: List of column names to categorize.

        Returns:
            A tuple of (scalars, relationships) where:
            - scalars: List of scalar column names
            - relationships: List of (name, related_model) tuples
        """
        relationships: list[tuple[str, type[DeclarativeBase]]] = []
        scalars: list[str] = []

        for column in columns:
            attr = safe_getattr(model, column)

            if isinstance(attr, InstrumentedAttribute):
                if isinstance(attr.property, RelationshipProperty):
                    relationships.append(
                        (column, self._get_orm_relation(model, column))
                    )
                else:
                    scalars.append(column)
            else:
                logger.debug(f"Skipping non-attribute {column} in model {model}")

        return scalars, relationships


def select_from_pydantic(
    model: type[DeclarativeBase], schema: type[BaseModel]
) -> Sequence[Load]:
    graph = PydanticGraph.from_model(schema)
    generator = StatementGenerator(graph, model)
    query = generator.generate_query()

    return query
