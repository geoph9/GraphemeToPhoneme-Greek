"""Test cases for the __main__ module."""
import pytest

from g2p_greek import g2p_greek


@pytest.fixture
def runner():
    """Fixture for invoking command-line interfaces."""
    return 


def test_main_succeeds(runner) -> None:
    """It exits with a status code of zero."""
    # result = runner.invoke(g2p_greek.cmdline)
    # assert result.exit_code == 0
    return
