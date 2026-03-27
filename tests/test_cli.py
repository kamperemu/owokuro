import sys
import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from owokuro.run import run, _process_directory, _process_file

class TestCLI(unittest.TestCase):
    @patch('owokuro.run.OwocrWebsocket')
    @patch('owokuro.run._get_volume_name', return_value='dummy')
    @patch('owokuro.run.generate_mokuro_volume', return_value={})
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_force_argument(self, mock_open, mock_generate, mock_get_name, mock_socket):
        # Test short argument
        with patch('sys.argv', ['owokuro', 'dummy_volume', '-f']):
            try:
                run()
            except SystemExit as e:
                self.fail(f"argparse failed to recognize -f flag, exited with {e}")

        # Test long argument
        with patch('sys.argv', ['owokuro', 'dummy_volume', '--force']):
            try:
                run()
            except SystemExit as e:
                self.fail(f"argparse failed to recognize --force flag, exited with {e}")

    @patch('owokuro.run._process_directory', return_value=[])
    @patch('owokuro.run._process_file', return_value=[])
    @patch('owokuro.run.OwocrWebsocket')
    @patch('owokuro.run._get_volume_name', return_value='dummy')
    @patch('owokuro.run.generate_mokuro_volume', return_value={})
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=True)
    def test_skip_existing(
        self, mock_is_dir, mock_exists, mock_open, mock_generate, mock_get_name,
        mock_socket, mock_process_file, mock_process_directory
    ):
        with patch('sys.argv', ['owokuro', 'dummy_volume']):
            run()
            mock_process_directory.assert_not_called()
            mock_process_file.assert_not_called()
            mock_generate.assert_not_called()
            mock_open.assert_not_called()

    @patch('owokuro.run._process_directory', return_value=[{'filename': 'dummy'}])
    @patch('owokuro.run._process_file', return_value=[{'filename': 'dummy'}])
    @patch('owokuro.run.OwocrWebsocket')
    @patch('owokuro.run._get_volume_name', return_value='dummy')
    @patch('owokuro.run.generate_mokuro_volume', return_value={})
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=True)
    def test_force_overwrite(
        self, mock_is_dir, mock_exists, mock_open, mock_generate, mock_get_name,
        mock_socket, mock_process_file, mock_process_directory
    ):
        with patch('sys.argv', ['owokuro', 'dummy_volume', '--force']):
            run()
            mock_process_directory.assert_called_once()
            mock_generate.assert_called_once()
            mock_open.assert_called_once()

    @patch('owokuro.run._process_directory', return_value=[{'filename': 'dummy'}])
    @patch('owokuro.run.generate_mokuro_volume', return_value={})
    @patch('owokuro.run.OwocrWebsocket')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('pathlib.Path.exists', return_value=False)
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.iterdir')
    def test_parent_dir_natural_sorting(
        self, mock_iterdir, mock_is_dir, mock_exists, mock_open,
        mock_socket, mock_generate, mock_process_directory
    ):
        p1 = Path('dummy_dir/vol10')
        p2 = Path('dummy_dir/vol2')
        p3 = Path('dummy_dir/vol1')
        mock_iterdir.return_value = [p1, p2, p3]

        with patch('sys.argv', ['owokuro', '--parent_dir', 'dummy_dir']):
            run()
            calls = mock_process_directory.call_args_list
            self.assertEqual(len(calls), 3)
            self.assertEqual(calls[0][0][1].name, 'vol1')
            self.assertEqual(calls[1][0][1].name, 'vol2')
            self.assertEqual(calls[2][0][1].name, 'vol10')

    @patch('owokuro.run._process_directory', return_value=[])
    @patch('owokuro.run._process_file', return_value=[])
    @patch('owokuro.run.generate_mokuro_volume', return_value={})
    @patch('owokuro.run.OwocrWebsocket')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('pathlib.Path.iterdir')
    def test_parent_dir_skips(
        self, mock_iterdir, mock_open,
        mock_socket, mock_generate, mock_process_file, mock_process_directory
    ):
        # p1: normal dir
        p1 = MagicMock(spec=Path)
        p1.name = 'vol1'
        p1.is_dir.return_value = True

        # p2: duplicate dir
        p2 = MagicMock(spec=Path)
        p2.name = 'vol1'
        p2.is_dir.return_value = True

        # p3: unsupported file
        p3 = MagicMock(spec=Path)
        p3.name = 'vol2.txt'
        p3.is_dir.return_value = False
        p3.is_file.return_value = True
        p3.suffix = '.txt'
        p3.stem = 'vol2'

        # Set up comparisons for natsort to work via MagicMock
        p1.__lt__.return_value = False
        p2.__lt__.return_value = False
        p3.__lt__.return_value = False

        # Setup the output file to not exist so it doesn't skip
        mock_out_path = MagicMock()
        mock_out_path.exists.return_value = False
        mock_out_path.name = 'vol1.mokuro'
        p1.parent.__truediv__.return_value = mock_out_path

        # Instead of iterdir, mock os_sorted directly to avoid mock comparison issues
        with patch('owokuro.run.os_sorted', return_value=[p1, p2, p3]):
            with patch('sys.argv', ['owokuro', '--parent_dir', 'dummy_dir']):
                run()

        # Only p1 should be processed. p2 is duplicate, p3 is unsupported
        self.assertEqual(mock_process_directory.call_count, 1)

    @patch('owokuro.run.generate_mokuro_volume', return_value={})
    @patch('owokuro.run.OwocrWebsocket')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_unsupported_volume_skip(
        self, mock_open, mock_socket, mock_generate
    ):
        p = MagicMock(spec=Path)
        p.is_dir.return_value = False
        p.is_file.return_value = True
        p.suffix = '.txt'
        p.name = 'unsupported.txt'
        p.stem = 'unsupported'

        mock_out_path = MagicMock()
        mock_out_path.exists.return_value = False
        p.parent.__truediv__.return_value = mock_out_path

        with patch('owokuro.run.argparse.ArgumentParser.parse_args') as mock_args:
            args = MagicMock()
            args.volume = p
            args.parent_dir = None
            args.force = False
            mock_args.return_value = args

            run()

            mock_open.assert_not_called()

    @patch('owokuro.run._process_file', return_value=[])
    @patch('owokuro.run.generate_mokuro_volume', return_value={})
    @patch('owokuro.run.OwocrWebsocket')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_archive_volume(
        self, mock_open, mock_socket, mock_generate, mock_process_file
    ):
        p = MagicMock(spec=Path)
        p.is_dir.return_value = False
        p.is_file.return_value = True
        p.suffix = '.cbz'
        p.name = 'vol1.cbz'
        p.stem = 'vol1'

        mock_out_path = MagicMock()
        mock_out_path.exists.return_value = False
        p.parent.__truediv__.return_value = mock_out_path

        with patch('owokuro.run.argparse.ArgumentParser.parse_args') as mock_args:
            args = MagicMock()
            args.volume = p
            args.parent_dir = None
            args.force = False
            mock_args.return_value = args

            run()

            mock_process_file.assert_called_once()

    @patch('owokuro.run._process_directory', return_value=[])
    @patch('owokuro.run.generate_mokuro_volume')
    @patch('owokuro.run.OwocrWebsocket')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('owokuro.run.log.warning')
    def test_empty_volume_skip(
        self, mock_warning, mock_open, mock_socket, mock_generate, mock_process_directory
    ):
        p = MagicMock(spec=Path)
        p.is_dir.return_value = True
        p.name = 'empty_vol'
        p.stem = 'empty_vol'

        mock_out_path = MagicMock()
        mock_out_path.exists.return_value = False
        p.parent.__truediv__.return_value = mock_out_path

        with patch('owokuro.run.argparse.ArgumentParser.parse_args') as mock_args:
            args = MagicMock()
            args.volume = p
            args.parent_dir = None
            args.force = False
            mock_args.return_value = args

            run()

            mock_process_directory.assert_called_once()
            mock_generate.assert_not_called()
            mock_open.assert_not_called()
            mock_warning.assert_called_once_with("Skipping empty volume: empty_vol. No valid images found.")

    def test_process_directory(self):
        owo_socket = MagicMock()
        owo_socket.process_image.return_value = 'res'

        volume_path = MagicMock(spec=Path)

        # Valid image
        p1 = MagicMock(spec=Path)
        p1.is_file.return_value = True
        p1.suffix = '.jpg'
        p1.__lt__.return_value = False

        # Invalid file
        p2 = MagicMock(spec=Path)
        p2.is_file.return_value = True
        p2.suffix = '.txt'
        p2.__lt__.return_value = False

        volume_path.iterdir.return_value = [p1, p2]

        with patch('builtins.sorted', return_value=[p1, p2]):
            results = _process_directory(owo_socket, volume_path)

        self.assertEqual(results, ['res'])
        owo_socket.process_image.assert_called_once_with(p1)

    @patch('owokuro.run.tempfile.TemporaryDirectory')
    @patch('owokuro.run.zipfile.ZipFile')
    @patch('owokuro.run._process_directory', return_value=['res'])
    def test_process_file(self, mock_process_dir, mock_zipfile, mock_tempdir):
        owo_socket = MagicMock()
        volume_path = Path("test.cbz")

        mock_temp = MagicMock()
        mock_temp.__enter__.return_value = "fake_temp_dir"
        mock_tempdir.return_value = mock_temp

        mock_zip = MagicMock()
        mock_zip_instance = MagicMock()
        mock_zip.__enter__.return_value = mock_zip_instance
        mock_zipfile.return_value = mock_zip

        mock_entry = MagicMock()
        mock_zip_instance.infolist.return_value = [mock_entry]

        results = _process_file(owo_socket, volume_path)

        self.assertEqual(results, ['res'])
        mock_zip_instance.extract.assert_called_once_with(mock_entry, Path("fake_temp_dir"))
        mock_process_dir.assert_called_once_with(owo_socket, Path("fake_temp_dir"))

if __name__ == '__main__':
    unittest.main()
