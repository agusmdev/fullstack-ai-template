from pytest import mark
from sqlalchemy import select

from app.database.db.ast import ASTNode, LoadOnlyNode, RelationshipLoadNode
from app.database.db.pydantic_fields import PydanticGraph
from app.database.db.statement_generator import StatementGenerator

from .schemas import (
    AliasedModel,
    AliasedSchema,
    BasicModel,
    BasicSchema,
    DeeplyNestedModel,
    DeeplyNestedSchema,
    JSONModel,
    JSONSchema,
    NestedModel,
    NestedSchema,
)


@mark.parametrize(
    "schema, model, expected",
    [
        (
            BasicSchema,
            BasicModel,
            ASTNode(
                BasicModel, [LoadOnlyNode(BasicModel, [], ["id", "title", "date"])]
            ),
        ),
        (
            AliasedSchema,
            AliasedModel,
            ASTNode(AliasedModel, [LoadOnlyNode(AliasedModel, [], ["title"])]),
        ),
        (
            NestedSchema,
            NestedModel,
            ASTNode(
                NestedModel,
                [
                    LoadOnlyNode(NestedModel, [], ["uuid"]),
                    RelationshipLoadNode(
                        NestedModel,
                        children=[
                            LoadOnlyNode(BasicModel, [], ["id", "title", "date"])
                        ],
                        relationship="basic",
                    ),
                    RelationshipLoadNode(
                        NestedModel,
                        children=[LoadOnlyNode(AliasedModel, [], ["title"])],
                        relationship="aliased",
                    ),
                ],
            ),
        ),
        (
            DeeplyNestedSchema,
            DeeplyNestedModel,
            ASTNode(
                DeeplyNestedModel,
                [
                    LoadOnlyNode(DeeplyNestedModel, [], ["nesting_level"]),
                    RelationshipLoadNode(
                        DeeplyNestedModel,
                        children=[
                            LoadOnlyNode(NestedModel, [], ["uuid"]),
                            RelationshipLoadNode(
                                NestedModel,
                                children=[
                                    LoadOnlyNode(
                                        BasicModel, [], ["id", "title", "date"]
                                    )
                                ],
                                relationship="basic",
                            ),
                            RelationshipLoadNode(
                                NestedModel,
                                children=[LoadOnlyNode(AliasedModel, [], ["title"])],
                                relationship="aliased",
                            ),
                        ],
                        relationship="nested",
                    ),
                    RelationshipLoadNode(
                        DeeplyNestedModel,
                        children=[LoadOnlyNode(AliasedModel, [], ["title"])],
                        relationship="alias",
                    ),
                ],
            ),
        ),
        (
            JSONSchema,
            JSONModel,
            ASTNode(
                JSONModel,
                [
                    LoadOnlyNode(JSONModel, [], ["id"]),
                    LoadOnlyNode(
                        JSONModel,
                        [],
                        [
                            "data_json_explicit",
                            "data_json_implicit",
                            "data_jsonb_explicit",
                            "data_jsonb_implicit",
                        ],
                    ),
                ],
            ),
        ),
    ],
)
def test_statement_generator_ast(schema, model, expected):
    graph = PydanticGraph.from_model(schema)
    generator = StatementGenerator(graph, model)

    assert generator._build_ast() == expected


def flatten_sql(sql: str) -> str:
    # Remove multiple whitespaces, newlines, and leading/trailing whitespaces
    return " ".join(sql.split())


@mark.parametrize(
    "schema, model, expected",
    [
        (
            BasicSchema,
            BasicModel,
            "SELECT basic.id, basic.title, basic.date FROM basic",
        ),
        (AliasedSchema, AliasedModel, "SELECT aliased.id, aliased.title FROM aliased"),
        (
            NestedSchema,
            NestedModel,
            """SELECT
                nested.uuid,
                nested.basic_id,
                nested.aliased_id,
                basic_1.id,
                basic_1.title,
                basic_1.date,
                aliased_1.id AS id_1,
                aliased_1.title AS title_1
            FROM
                nested
                LEFT OUTER JOIN basic AS basic_1 ON basic_1.id = nested.basic_id
                LEFT OUTER JOIN aliased AS aliased_1 ON aliased_1.id = nested.aliased_id""",
        ),
        (
            DeeplyNestedSchema,
            DeeplyNestedModel,
            """SELECT
                deeply_nested.nesting_level,
                deeply_nested.nested_id,
                deeply_nested.aliased_id,
                basic_1.id,
                basic_1.title,
                basic_1.date,
                aliased_1.id AS id_1,
                aliased_1.title AS title_1,
                nested_1.uuid,
                aliased_2.id AS id_2,
                aliased_2.title AS title_2
            FROM
                deeply_nested
                LEFT OUTER JOIN nested AS nested_1 ON nested_1.uuid = deeply_nested.nested_id
                LEFT OUTER JOIN basic AS basic_1 ON basic_1.id = nested_1.basic_id
                LEFT OUTER JOIN aliased AS aliased_1 ON aliased_1.id = nested_1.aliased_id
                LEFT OUTER JOIN aliased AS aliased_2 ON aliased_2.id = deeply_nested.aliased_id""",
        ),
        (
            JSONSchema,
            JSONModel,
            "SELECT jsonb.id, jsonb.data_json_explicit, jsonb.data_json_implicit, jsonb.data_jsonb_explicit, jsonb.data_jsonb_implicit FROM jsonb",
        ),
    ],
)
def test_statement_generator_sql(schema, model, expected):
    graph = PydanticGraph.from_model(schema)
    generator = StatementGenerator(graph, model)

    assert flatten_sql(
        str(select(model).options(*generator.generate_load_options()))
    ) == flatten_sql(expected)
