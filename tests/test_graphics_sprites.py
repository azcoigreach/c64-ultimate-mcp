import os
import tempfile
import unittest

from graphics.converter import convert_sprites


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestGraphicsSprites(unittest.TestCase):
    def test_hires_sprite_outputs(self):
        input_path = os.path.join(FIXTURES_DIR, "sprite_hires.bmp")
        with tempfile.TemporaryDirectory() as temp_dir:
            result = convert_sprites(
                input_path=input_path,
                sprite_mode="hires",
                output_dir=temp_dir,
            )
            sprite_path = result["files"]["sprites"][0]
            with open(sprite_path, "rb") as handle:
                self.assertEqual(len(handle.read()), 64)

    def test_multicolor_sprite_outputs(self):
        input_path = os.path.join(FIXTURES_DIR, "sprite_multicolor.bmp")
        with tempfile.TemporaryDirectory() as temp_dir:
            result = convert_sprites(
                input_path=input_path,
                sprite_mode="multicolor",
                output_dir=temp_dir,
            )
            sprite_path = result["files"]["sprites"][0]
            with open(sprite_path, "rb") as handle:
                self.assertEqual(len(handle.read()), 64)


if __name__ == "__main__":
    unittest.main()
