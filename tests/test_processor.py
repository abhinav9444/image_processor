import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image

import image_processor


class TestImageProcessor(unittest.TestCase):
    def test_filename_normalization(self):
        self.assertEqual(
            image_processor.normalize_filename("Fresh Tomato (Big).JPG"),
            "fresh_tomato_big",
        )

    def test_resolution_builder(self):
        config = {
            "standard_resolutions": {
                "card": [400, 400],
                "detail": [800, 800],
            },
            "enabled_resolutions": ["card"],
            "custom_resolutions": [],
        }
        resolutions = image_processor.build_resolutions(
            config,
            selected_names=["card"],
            custom=(512, 512),
        )
        self.assertEqual(
            [(r.name, r.width, r.height) for r in resolutions],
            [("card", 400, 400), ("512x512", 512, 512)],
        )

    def test_contain_resize(self):
        image = Image.new("RGB", (1600, 800), "red")
        result = image_processor.resize_contain(
            image,
            (400, 400),
            (255, 255, 255),
        )
        self.assertEqual(result.size, (400, 400))

    def test_process_sample_image(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "input"
            output_dir = root / "output"
            input_dir.mkdir()

            sample = Image.new("RGB", (1000, 700), "green")
            sample.save(input_dir / "Green Apple.JPG")

            config = image_processor.load_config(
                root / "config.json"
            )

            resolutions = [
                image_processor.Resolution("card", 400, 400)
            ]

            stats = image_processor.ProcessingStats()
            stats.start_time = 0

            logger = image_processor.setup_logging(
                output_dir / "test.log"
            )

            image_processor.process_image(
                input_path=input_dir / "Green Apple.JPG",
                output_dir=output_dir,
                resolutions=resolutions,
                output_format="WEBP",
                quality=85,
                fit_mode="contain",
                background=(255, 255, 255),
                enhancement=config["enhancement"],
                quality_config=config["quality_check"],
                dry_run=False,
                logger=logger,
                stats=stats,
            )

            result = output_dir / "card" / "green_apple_card.webp"

            self.assertTrue(result.exists())

            with Image.open(result) as processed:
                self.assertEqual(processed.size, (400, 400))

            self.assertEqual(stats.processed, 1)
            self.assertGreater(stats.output_bytes, 0)


if __name__ == "__main__":
    unittest.main()
