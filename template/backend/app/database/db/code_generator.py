from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

from sqlalchemy import exc
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import joinedload, load_only

from .ast import safe_getattr

if TYPE_CHECKING:
    from sqlalchemy.orm.strategy_options import Load

    from .ast import ASTNode, LoadOnlyNode, RelationshipLoadNode


class QueryOptimizerError(Exception):
    """Base exception for query optimizer errors.

    Raised when the query optimizer encounters an issue during
    AST traversal or SQLAlchemy option generation.
    """

    pass


class QueryOptionGenerator:
    """Visitor class that generates SQLAlchemy query options from AST nodes.

    This class implements the Visitor pattern to traverse the AST and
    generate SQLAlchemy loading options (joinedload, load_only) based
    on the node types.
    """

    def visit(self, node: ASTNode) -> Load:
        """Dispatch to the appropriate visit_<NodeType> method."""
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> None:
        """Raise QueryOptimizerError when no visit method exists for a node type."""
        raise QueryOptimizerError(f"No visit_{type(node).__name__} method")

    def visit_LoadOnlyNode(self, node: LoadOnlyNode) -> Load:
        """Generate a load_only option; raises QueryOptimizerError for non-column fields."""
        orm_columns = [safe_getattr(node.model, col) for col in node.columns]

        try:
            return load_only(*orm_columns)  # type: ignore[return-value]  # SQLAlchemy's load_only returns Load[Model], not the generic Load[Column]
        except exc.ArgumentError as e:
            self._argument_error(e, node)

    def visit_RelationshipLoadNode(self, node: RelationshipLoadNode) -> Load:
        """Generate a joinedload option, recursively applying options for nested children."""
        relationship = safe_getattr(node.model, node.relationship)

        loader = joinedload(relationship)
        if node.children:
            child_loaders = [self.visit(child) for child in node.children]
            if child_loaders:
                loader = loader.options(*child_loaders)

        return loader  # type: ignore[return-value]  # joinedload() returns JoinedLoad which is narrower than generic Load

    def _argument_error(self, e: exc.ArgumentError, node: LoadOnlyNode) -> NoReturn:
        """Re-raise ArgumentError with a specific column name if a non-column field was passed."""
        for col in node.columns:
            orm_column = safe_getattr(node.model, col)

            try:
                inspect(orm_column)
            except exc.NoInspectionAvailable:
                raise QueryOptimizerError(
                    f"Column '{col}' in model {node.model.__name__} is not a column field"
                ) from e

        raise e
