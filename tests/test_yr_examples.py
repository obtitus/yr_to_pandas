"""Runs doctests for easier integration with tox."""
import doctest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import yr_to_pandas
from yr_to_pandas import yr_examples


def test_yr_examples_doctest():
    """Run doctests for yr_examples."""
    doctest.testmod(yr_examples, raise_on_error=True, verbose=True)


def test_yr_client_doctest():
    """Run doctests for yr_client."""
    doctest.testmod(yr_to_pandas.yr_client, raise_on_error=True, verbose=True)
