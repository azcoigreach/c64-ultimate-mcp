import json
import os
import tempfile
import unittest

from graphics.converter import convert_bitmap


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestGraphicsBitmap(unittest.TestCase):
    def test_multicolor_bitmap_outputs(self):
        input_path = os.path.join(FIXTURES_DIR, "bitmap_multicolor.bmp")
        with tempfile.TemporaryDirectory() as temp_dir:
            result = convert_bitmap(
                input_path=input_path,
                mode="bitmap_multicolor",
                output_dir=temp_dir,
                emit_asm=True,
                emit_basic=False,
            )

            with open(result["files"]["bitmap"], "rb") as handle:
                self.assertEqual(len(handle.read()), 8000)
            with open(result["files"]["screen"], "rb") as handle:
                self.assertEqual(len(handle.read()), 1000)
            with open(result["files"]["color"], "rb") as handle:
                self.assertEqual(len(handle.read()), 1000)

            with open(result["files"]["manifest"], "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["addresses"]["bitmap"], 0x2000)
            self.assertIn("report_txt", manifest["output_files"])

    def test_hires_bitmap_outputs(self):
        input_path = os.path.join(FIXTURES_DIR, "bitmap_hires.bmp")
        with tempfile.TemporaryDirectory() as temp_dir:
            result = convert_bitmap(
                input_path=input_path,
                mode="bitmap_hires",
                output_dir=temp_dir,
            )

            with open(result["files"]["bitmap"], "rb") as handle:
                self.assertEqual(len(handle.read()), 8000)
            with open(result["files"]["screen"], "rb") as handle:
                self.assertEqual(len(handle.read()), 1000)
            with open(result["files"]["color"], "rb") as handle:
                self.assertEqual(len(handle.read()), 1000)


if __name__ == "__main__":
    unittest.main()
