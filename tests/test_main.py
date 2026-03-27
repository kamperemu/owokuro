import unittest
from unittest.mock import patch

from owokuro import __main__

class TestMain(unittest.TestCase):
    @patch('owokuro.run.run')
    def test_main(self, mock_run):
        __main__.main()
        mock_run.assert_called_once()
