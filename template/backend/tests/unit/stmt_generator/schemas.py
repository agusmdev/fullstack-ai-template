from pydantic import BaseModel, Field
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()


class BasicSchema(BaseModel):
    id: str
    title: int
    date: str


class AliasedSchema(BaseModel):
    name: str = Field(alias="title")


class NestedSchema(BaseModel):
    uuid: str

    basic: BasicSchema
    aliased: AliasedSchema


class DeeplyNestedSchema(BaseModel):
    nesting_level: int

    nested: NestedSchema
    alias: AliasedSchema


class BasicModel(Base):
    __tablename__ = "basic"
    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[int]
    date: Mapped[str]

    ignored_field: Mapped[str] = mapped_column()


class AliasedModel(Base):
    __tablename__ = "aliased"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()

    unmapped_field: Mapped[str] = mapped_column()


class NestedModel(Base):
    __tablename__ = "nested"
    uuid: Mapped[str] = mapped_column(primary_key=True)

    basic_id: Mapped[str] = mapped_column(ForeignKey("basic.id"))
    basic: Mapped[BasicModel] = relationship("BasicModel")

    aliased_id: Mapped[str] = mapped_column(ForeignKey("aliased.id"))
    aliased: Mapped[AliasedModel] = relationship("AliasedModel")

    not_used_field: Mapped[str] = mapped_column()


class DeeplyNestedModel(Base):
    __tablename__ = "deeply_nested"
    nesting_level: Mapped[int] = mapped_column(primary_key=True)
    unloaded_field: Mapped[str] = mapped_column()

    nested_id: Mapped[str] = mapped_column(ForeignKey("nested.uuid"))
    nested: Mapped[NestedModel] = relationship("NestedModel")

    aliased_id: Mapped[str] = mapped_column(ForeignKey("aliased.id"))
    alias: Mapped[AliasedModel] = relationship("AliasedModel")


class InnerJSONSchema(BaseModel):
    field_a: int
    field_b: str


class JSONSchema(BaseModel):
    """
    Schema for a model JSON fields.
    """

    id: int
    data_json_explicit: InnerJSONSchema
    data_json_implicit: InnerJSONSchema

    data_jsonb_explicit: InnerJSONSchema
    data_jsonb_implicit: InnerJSONSchema

    should_skip: bool
    should_skip_complex_model: InnerJSONSchema


class JSONModel(Base):
    __tablename__ = "jsonb"
    id: Mapped[int] = mapped_column(primary_key=True)
    data_json_explicit: Mapped[dict] = mapped_column(type_=JSON)
    data_json_implicit: Mapped[dict] = mapped_column(JSON)

    data_jsonb_explicit: Mapped[dict] = mapped_column(type_=JSONB)
    data_jsonb_implicit: Mapped[dict] = mapped_column(JSONB)

    @property
    def should_skip(self):
        return True

    @property
    def should_skip_complex_model(self):
        return {"a": 1, "b": 2}
