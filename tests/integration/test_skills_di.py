"""Integration tests for skills route dependency injection."""

import inspect


from apps.api.routes import skills


def test_list_skills_uses_di_signature() -> None:
    """Verify list_skills uses DI for skills services."""
    sig = inspect.signature(skills.list_skills)
    params = list(sig.parameters.keys())
    assert "skills_discovery" in params
    assert "skills_crud" in params
    assert "cache" not in params


def test_create_skill_uses_di_signature() -> None:
    """Verify create_skill uses DI for skills_crud."""
    sig = inspect.signature(skills.create_skill)
    params = list(sig.parameters.keys())
    assert "skills_crud" in params
    assert "cache" not in params


def test_get_skill_uses_di_signature() -> None:
    """Verify get_skill uses DI for skills services."""
    sig = inspect.signature(skills.get_skill)
    params = list(sig.parameters.keys())
    assert "skills_discovery" in params
    assert "skills_crud" in params
    assert "cache" not in params


def test_update_skill_uses_di_signature() -> None:
    """Verify update_skill uses DI for skills_crud."""
    sig = inspect.signature(skills.update_skill)
    params = list(sig.parameters.keys())
    assert "skills_crud" in params
    assert "cache" not in params


def test_delete_skill_uses_di_signature() -> None:
    """Verify delete_skill uses DI for skills_crud."""
    sig = inspect.signature(skills.delete_skill)
    params = list(sig.parameters.keys())
    assert "skills_crud" in params
    assert "cache" not in params


def test_no_helper_functions_exist() -> None:
    """Verify helper functions have been removed."""
    assert not hasattr(skills, "_get_skills_service")
