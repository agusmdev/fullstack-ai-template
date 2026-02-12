from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.orm import DeclarativeBase


def safe_getattr(obj: type[DeclarativeBase], attr: str) -> Any:
    """
    Safely get an attribute from a SQLAlchemy model with improved error messages.

    Args:
        obj: The SQLAlchemy model class.
        attr: The attribute name to retrieve.

    Returns:
        The attribute value.

    Raises:
        AttributeError: If the attribute is not found, with a descriptive message.
    """
    try:
        return getattr(obj, attr)
    except AttributeError as e:
        raise AttributeError(
            f"Column or relationship '{attr}' not found in model {obj.__name__}: {e}"
        ) from e


@dataclass
class ASTNode:
    """Base class for all AST nodes in the query optimization tree.

    Attributes:
        model: The SQLAlchemy model this node operates on.
        children: Child AST nodes for nested operations.
    """

    model: type[DeclarativeBase]
    children: list[ASTNode] = field(default_factory=list)

    def visualize(self, indent: int = 0) -> None:
        """Print a visual representation of the AST tree for debugging.

        Args:
            indent: Indentation level for this node.
        """
        indentation = "\t" * indent
        kwargs = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())

        print(f"{indentation}{self.__class__.__name__}({kwargs})")

        for child in self.children:
            child.visualize(indent + 1)


class LoadOnlyNode(ASTNode):
    """Represents a load_only operation on a model with specified columns.

    Attributes:
        model: The SQLAlchemy model to load columns from.
        children: Child AST nodes (typically empty for LoadOnlyNode).
        columns: Iterable of column names to load.
    """

    def __init__(
        self,
        model: type[DeclarativeBase],
        children: list[ASTNode],
        columns: Iterable[str],
    ):
        super().__init__(model, children)
        self.columns = columns

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LoadOnlyNode):
            return False
        return (
            self.model == other.model
            and self.children == other.children
            and list(self.columns) == list(other.columns)
        )


class RelationshipLoadNode(ASTNode):
    """Represents a relationship loading operation with joinedload.

    Attributes:
        model: The SQLAlchemy model containing the relationship.
        children: Child AST nodes for nested relationship loading.
        relationship: The name of the relationship to load.
    """

    def __init__(
        self,
        model: type[DeclarativeBase],
        children: list[ASTNode],
        relationship: str,
    ):
        super().__init__(model, children)
        self.relationship = relationship

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RelationshipLoadNode):
            return False
        return (
            self.model == other.model
            and self.children == other.children
            and self.relationship == other.relationship
        )
