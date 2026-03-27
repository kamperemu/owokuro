import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from owokuro.owosocket import OwocrWebsocket, OwocrResult

class TestOwocrWebsocket(unittest.TestCase):
    @patch('owokuro.owosocket.websocket.WebSocket')
    def test_init_success(self, mock_ws_class):
        mock_ws_instance = MagicMock()
        mock_ws_class.return_value = mock_ws_instance

        ws = OwocrWebsocket(1234)
        mock_ws_class.assert_called_once()
        mock_ws_instance.connect.assert_called_once_with("ws://127.0.0.1:1234")

    @patch('owokuro.owosocket.websocket.WebSocket')
    def test_init_connection_refused(self, mock_ws_class):
        mock_ws_instance = MagicMock()
        mock_ws_instance.connect.side_effect = ConnectionRefusedError()
        mock_ws_class.return_value = mock_ws_instance

        with self.assertRaises(ConnectionRefusedError) as context:
            OwocrWebsocket(1234)

        self.assertIn("owocr server is not active on port 1234", str(context.exception))

    @patch('owokuro.owosocket.websocket.WebSocket')
    def test_close(self, mock_ws_class):
        mock_ws_instance = MagicMock()
        mock_ws_class.return_value = mock_ws_instance

        ws = OwocrWebsocket(1234)
        ws.close()
        mock_ws_instance.close.assert_called_once()

    @patch('owokuro.owosocket.websocket.WebSocket')
    @patch('pathlib.Path.read_bytes')
    def test_process_image(self, mock_read_bytes, mock_ws_class):
        mock_ws_instance = MagicMock()
        mock_ws_class.return_value = mock_ws_instance

        # owosocket does recv() twice. First is likely acknowledgment, second is the actual result.
        # We need to mock recv to return those two values.
        expected_json = {"blocks": [], "version": "0.1"}
        mock_ws_instance.recv.side_effect = [
            b"processing", # first recv
            json.dumps(expected_json).encode('utf-8') # second recv
        ]
        mock_read_bytes.return_value = b"fake_image_data"

        ws = OwocrWebsocket(1234)

        test_path = Path("test_image.png")
        result: OwocrResult = ws.process_image(test_path)

        mock_ws_instance.send_binary.assert_called_once_with(b"fake_image_data")
        self.assertEqual(mock_ws_instance.recv.call_count, 2)

        self.assertEqual(result["filename"], "test_image.png")
        self.assertEqual(result["json_data"], expected_json)

if __name__ == '__main__':
    unittest.main()
