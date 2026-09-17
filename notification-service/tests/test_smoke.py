"""Smoke test until real tests are added."""
import pytest


@pytest.mark.unit
def test_placeholder():
    """Placeholder so pytest doesn't exit with code 5 (no tests collected)."""
    assert True
