
import pytest
from app.core.config import settings

@pytest.fixture
def mock_settings():
    return settings
