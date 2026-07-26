import pytest

from backend.app.security import (
    normalize_role,
    require_permission,
    role_has_permission,
    validate_role,
    PermissionDeniedError,
)


def test_normalize_role():
    assert normalize_role(" Senior_Analyst ") == "senior_analyst"


def test_validate_role_returns_canonical_role():
    assert validate_role("Admin") == "admin"


def test_validate_role_rejects_invalid_role():
    with pytest.raises(ValueError, match="Invalid role"):
        validate_role("intern")


@pytest.mark.parametrize(
    "role, permission",
    [
        ("analyst", "revenue_ranking"),
        ("analyst", "pipeline_comparison"),
        ("analyst", "sector_analysis"),
        ("senior_analyst", "ai_polishing"),
        ("senior_analyst", "document_search"),
        ("admin", "any_future_permission"),
    ],
)
def test_role_has_permission_allowed(role, permission):
    assert role_has_permission(role, permission) is True


@pytest.mark.parametrize(
    "role, permission",
    [
        ("analyst", "ai_polishing"),
        ("analyst", "document_search"),
        ("senior_analyst", "admin_only_action"),
    ],
)
def test_role_has_permission_denied(role, permission):
    assert role_has_permission(role, permission) is False


def test_require_permission_allowed():
    require_permission("senior_analyst", "ai_polishing")


def test_require_permission_denied():
    with pytest.raises(PermissionDeniedError, match="does not have permission"):
        require_permission("analyst", "ai_polishing")
