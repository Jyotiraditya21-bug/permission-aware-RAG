import pytest
from src.api import app

def test_pipeline_integration():
    assert app is not None
