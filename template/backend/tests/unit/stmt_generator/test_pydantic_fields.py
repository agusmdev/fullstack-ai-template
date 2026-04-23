
from pydantic import BaseModel, Field
from pytest import mark

from app.database.db import PydanticGraph

from .schemas import (
    AliasedSchema,
    BasicSchema,
    DeeplyNestedSchema,
    NestedSchema,
)


class IgnoredFieldSchema(BasicSchema):
    ignored_field: str = Field(_select_strategy="lazy")
    title: str = Field(_select_strategy="lazy")


class OptionalFieldSchema(BaseModel):
    optional: list[str] | None
    basic: list[BasicSchema] | None
    future_reference: "BasicSchema"


@mark.parametrize(
    "model, expected_columns, expected_relationships",
    [
        (BasicSchema, ["id", "title", "date"], {}),
        (AliasedSchema, ["title"], {}),
        (
            NestedSchema,
            ["uuid"],
            {
                "basic": PydanticGraph(["id", "title", "date"], {}),
                "aliased": PydanticGraph(["title"], {}),
            },
        ),
        (
            DeeplyNestedSchema,
            ["nesting_level"],
            {
                "nested": PydanticGraph(
                    ["uuid"],
                    {
                        "basic": PydanticGraph(["id", "title", "date"], {}),
                        "aliased": PydanticGraph(["title"], {}),
                    },
                ),
                "alias": PydanticGraph(["title"], {}),
            },
        ),
        (
            IgnoredFieldSchema,
            ["id", "date"],
            {},
        ),
        (
            OptionalFieldSchema,
            [
                "optional",
            ],
            {
                "basic": PydanticGraph(
                    ["id", "title", "date"],
                    {},
                ),
                "future_reference": PydanticGraph(
                    ["id", "title", "date"],
                    {},
                ),
            },
        ),
    ],
)
def test_graph_from_model(model, expected_columns, expected_relationships):
    graph = PydanticGraph.from_model(model)
    assert graph.columns == expected_columns
    assert graph.relationships == expected_relationships
