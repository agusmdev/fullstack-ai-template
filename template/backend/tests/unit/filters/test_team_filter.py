"""Tests for TeamFilter."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.teams.filters import TeamFilter
from app.modules.teams.models import Team


class TestTeamFilterConstants:
    def test_model_is_team(self):
        assert TeamFilter.Constants.model is Team

    def test_search_model_fields(self):
        assert TeamFilter.Constants.search_model_fields == ["name", "key"]


class TestTeamFilterFields:
    def test_search_field_exists(self):
        assert "search" in TeamFilter.model_fields

    def test_search_field_optional(self):
        assert TeamFilter().search is None

    def test_search_field_can_be_set(self):
        assert TeamFilter(search="eng").search == "eng"


class TestTeamFilterInheritance:
    def test_inherits_from_filter(self):
        assert issubclass(TeamFilter, Filter)

    def test_has_filter_method(self):
        f = TeamFilter()
        assert hasattr(f, "filter")
        assert callable(f.filter)
