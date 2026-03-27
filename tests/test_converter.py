import unittest
from unittest.mock import patch

from owokuro.converter import parse_owocr_file, generate_mokuro_volume

class TestConverter(unittest.TestCase):
    def test_parse_owocr_file_empty(self):
        owocr_data = {
            'image_properties': {'width': 1000, 'height': 2000},
            'paragraphs': []
        }
        result = parse_owocr_file(owocr_data, 'test.jpg')

        self.assertEqual(result['version'], '0.2.4')
        self.assertEqual(result['img_width'], 1000)
        self.assertEqual(result['img_height'], 2000)
        self.assertEqual(result['img_path'], 'test.jpg')
        self.assertEqual(len(result['blocks']), 0)

    def test_parse_owocr_file_vertical_text(self):
        owocr_data = {
            'image_properties': {'width': 100, 'height': 200},
            'paragraphs': [
                {
                    'writing_direction': 'TOP_TO_BOTTOM',
                    'lines': [
                        {
                            'text': 'Hello',
                            'bounding_box': {
                                'center_x': 0.5,
                                'center_y': 0.5,
                                'width': 0.2,
                                'height': 0.1,
                                'rotation_z': 0
                            }
                        }
                    ]
                }
            ]
        }
        result = parse_owocr_file(owocr_data, 'test.png')
        self.assertEqual(len(result['blocks']), 1)
        block = result['blocks'][0]
        self.assertTrue(block['vertical'])
        # Font size for vertical is based on width (0.2 * 100 = 20)
        self.assertEqual(block['font_size'], 20)
        self.assertEqual(block['lines'], ['Hello'])
        self.assertEqual(len(block['lines_coords']), 1)
        self.assertEqual(len(block['lines_coords'][0]), 4)

    def test_parse_owocr_file_horizontal_text_no_rot(self):
        owocr_data = {
            'image_properties': {'width': 100, 'height': 200},
            'paragraphs': [
                {
                    'writing_direction': 'LEFT_TO_RIGHT',
                    'lines': [
                        {
                            'text': 'World',
                            'bounding_box': {
                                'center_x': 0.5,
                                'center_y': 0.5,
                                'width': 0.2,
                                'height': 0.1
                                # missing rotation_z
                            }
                        }
                    ]
                }
            ]
        }
        result = parse_owocr_file(owocr_data, 'test2.png')
        self.assertEqual(len(result['blocks']), 1)
        block = result['blocks'][0]
        self.assertFalse(block['vertical'])
        # Font size for horizontal is based on height (0.1 * 200 = 20)
        self.assertEqual(block['font_size'], 20)
        self.assertEqual(block['lines'], ['World'])

    def test_parse_owocr_file_empty_lines(self):
        owocr_data = {
            'image_properties': {'width': 100, 'height': 200},
            'paragraphs': [
                {
                    'writing_direction': 'LEFT_TO_RIGHT',
                    'lines': []
                }
            ]
        }
        result = parse_owocr_file(owocr_data, 'test3.png')
        self.assertEqual(len(result['blocks']), 0)

    @patch('owokuro.converter.uuid.uuid4', return_value='fake-uuid')
    def test_generate_mokuro_volume(self, mock_uuid):
        volume_json_data = [
            {
                'filename': 'page1.png',
                'json_data': {
                    'image_properties': {'width': 100, 'height': 200},
                    'paragraphs': []
                }
            }
        ]

        result = generate_mokuro_volume('Title', 'title-uuid', 'Vol 1', volume_json_data)

        self.assertEqual(result['version'], '0.2.4')
        self.assertEqual(result['title'], 'Title')
        self.assertEqual(result['title_uuid'], 'title-uuid')
        self.assertEqual(result['volume'], 'Vol 1')
        self.assertEqual(result['volume_uuid'], 'fake-uuid')
        self.assertEqual(len(result['pages']), 1)
        self.assertEqual(result['pages'][0]['img_path'], 'page1.png')

if __name__ == '__main__':
    unittest.main()
