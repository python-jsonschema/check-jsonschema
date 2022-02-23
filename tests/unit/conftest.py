import pytest
import responses


@pytest.fixture(autouse=True)
def mocked_responses():
    responses.start()
    yield
    responses.stop()
    responses.reset()
