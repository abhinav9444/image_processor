#!/usr/bin/env python3
"""
E-Commerce Image Processor
===========================

Batch image preprocessing utility for e-commerce product catalogs.

Features:
- Recursive batch processing
- Standard resolution presets
- Custom resolutions
- Multiple resolutions in one run
- Cover / contain / stretch fitting
- JPEG / PNG / WebP / AVIF output
- Configurable quality
- EXIF orientation correction
- Transparency/background handling
- Brightness / contrast / saturation / sharpness adjustment
- Optional noise reduction and sharpening
- Minimum resolution and quality warnings
- Filename normalization
- Metadata stripping
- Dry-run mode
- Logging
- JSON processing report
- Storage/compression statistics

Intentionally excluded:
- Duplicate detection
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError


SUPPORTED_INPUT_FORMATS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".avif"
}
SUPPORTED_OUTPUT_FORMATS = {"JPEG", "PNG", "WEBP", "AVIF"}

DEFAULT_STANDARD_RESOLUTIONS = {
    "tiny": (100, 100),
    "thumbnail": (150, 150),
    "small": (300, 300),
    "card": (400, 400),
    "medium": (600, 600),
    "detail": (800, 800),
    "large": (1200, 1200),
}


@dataclass(frozen=True)
class Resolution:
    name: str
    width: int
    height: int


@dataclass
class ProcessingStats:
    processed: int = 0
    failed: int = 0
    warnings: int = 0
    original_bytes: int = 0
    output_bytes: int = 0
    start_time: float = 0.0

    @property
    def saved_bytes(self) -> int:
        return max(0, self.original_bytes - self.output_bytes)

    @property
    def compression_percentage(self) -> float:
        if self.original_bytes == 0:
            return 0.0
        return self.saved_bytes / self.original_bytes * 100

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time


def setup_logging(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("image_processor")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


def create_default_config(path: Path) -> None:
    config = {
        "output_format": "WEBP",
        "quality": 85,
        "fit_mode": "contain",
        "background": {"r": 255, "g": 255, "b": 255},
        "standard_resolutions": {
            name: list(size) for name, size in DEFAULT_STANDARD_RESOLUTIONS.items()
        },
        "enabled_resolutions": ["thumbnail", "card", "detail"],
        "custom_resolutions": [],
        "enhancement": {
            "brightness": 1.0,
            "contrast": 1.0,
            "saturation": 1.0,
            "sharpness": 1.0,
            "noise_reduction": 0,
            "sharpen": 0,
        },
        "quality_check": {
            "minimum_width": 300,
            "minimum_height": 300,
            "minimum_quality_score": 5.0,
        },
    }
    path.write_text(json.dumps(config, indent=4) + "\n", encoding="utf-8")


def load_config(path: Path) -> dict:
    if not path.exists():
        create_default_config(path)
        print(f"Created default config: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_config(config: dict) -> None:
    output_format = config.get("output_format", "WEBP").upper()
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}")

    quality = int(config.get("quality", 85))
    if not 1 <= quality <= 100:
        raise ValueError("quality must be between 1 and 100")

    fit_mode = config.get("fit_mode", "contain")
    if fit_mode not in {"cover", "contain", "stretch"}:
        raise ValueError("fit_mode must be cover, contain, or stretch")

    background = config.get("background", {})
    for key in ("r", "g", "b"):
        value = int(background.get(key, 255))
        if not 0 <= value <= 255:
            raise ValueError(f"background.{key} must be between 0 and 255")


def build_resolutions(
    config: dict,
    selected_names: list[str] | None = None,
    custom: tuple[int, int] | None = None,
) -> list[Resolution]:
    standard = config.get("standard_resolutions", {})
    names = selected_names or config.get(
        "enabled_resolutions", ["thumbnail", "card", "detail"]
    )

    resolutions: list[Resolution] = []

    for name in names:
        if name not in standard:
            available = ", ".join(standard.keys())
            raise ValueError(f"Unknown resolution '{name}'. Available: {available}")
        width, height = map(int, standard[name])
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid resolution for '{name}'")
        resolutions.append(Resolution(name, width, height))

    if custom:
        width, height = custom
        if width <= 0 or height <= 0:
            raise ValueError("Custom width and height must be positive")
        resolutions.append(Resolution(f"{width}x{height}", width, height))

    for item in config.get("custom_resolutions", []):
        if len(item) != 2:
            continue
        width, height = map(int, item)
        if width > 0 and height > 0:
            resolutions.append(Resolution(f"{width}x{height}", width, height))

    return resolutions


def print_resolutions(config: dict) -> None:
    print("\nAvailable standard resolutions")
    print("==============================")
    for name, size in config.get("standard_resolutions", {}).items():
        print(f"{name:<12} {size[0]} x {size[1]}")
    print()


def normalize_filename(filename: str) -> str:
    stem = Path(filename).stem.lower().replace("&", "and")
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    stem = re.sub(r"_+", "_", stem)
    return stem.strip("_") or "image"


def correct_orientation(image: Image.Image) -> Image.Image:
    return ImageOps.exif_transpose(image)


def normalize_image_mode(
    image: Image.Image, background: tuple[int, int, int]
) -> Image.Image:
    if image.mode == "RGBA":
        canvas = Image.new("RGBA", image.size, background + (255,))
        canvas.alpha_composite(image)
        return canvas.convert("RGB")
    if image.mode in {"LA", "P", "CMYK", "LAB", "HSV", "L"}:
        return image.convert("RGB")
    if image.mode == "RGB":
        return image
    return image.convert("RGB")


def enhance_image(
    image: Image.Image,
    brightness: float,
    contrast: float,
    saturation: float,
    sharpness: float,
) -> Image.Image:
    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)
    if contrast != 1.0:
        image = ImageEnhance.Contrast(image).enhance(contrast)
    if saturation != 1.0:
        image = ImageEnhance.Color(image).enhance(saturation)
    if sharpness != 1.0:
        image = ImageEnhance.Sharpness(image).enhance(sharpness)
    return image


def reduce_noise(image: Image.Image, strength: int) -> Image.Image:
    if strength <= 0:
        return image
    strength = max(1, min(strength, 5))
    return image.filter(ImageFilter.MedianFilter(size=strength * 2 + 1))


def sharpen_image(image: Image.Image, amount: int) -> Image.Image:
    if amount <= 0:
        return image
    amount = max(1, min(amount, 5))
    for _ in range(amount):
        image = image.filter(
            ImageFilter.UnsharpMask(radius=1.0, percent=100, threshold=3)
        )
    return image


def resize_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(
        image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
    )


def resize_contain(
    image: Image.Image,
    size: tuple[int, int],
    background: tuple[int, int, int],
) -> Image.Image:
    canvas = Image.new("RGB", size, background)
    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    x = (size[0] - copy.width) // 2
    y = (size[1] - copy.height) // 2
    canvas.paste(copy, (x, y))
    return canvas


def resize_stretch(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return image.resize(size, Image.Resampling.LANCZOS)


def resize_image(
    image: Image.Image,
    resolution: Resolution,
    fit_mode: str,
    background: tuple[int, int, int],
) -> Image.Image:
    size = (resolution.width, resolution.height)
    if fit_mode == "cover":
        return resize_cover(image, size)
    if fit_mode == "contain":
        return resize_contain(image, size, background)
    if fit_mode == "stretch":
        return resize_stretch(image, size)
    raise ValueError(f"Invalid fit mode: {fit_mode}")


def estimate_quality(image: Image.Image) -> float:
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    histogram = edges.histogram()
    total = gray.width * gray.height
    if total == 0:
        return 0.0
    return sum(i * count for i, count in enumerate(histogram)) / total


def validate_image(
    image: Image.Image,
    minimum_width: int,
    minimum_height: int,
    minimum_quality: float,
) -> list[str]:
    warnings = []
    if image.width < minimum_width:
        warnings.append(
            f"Source width {image.width}px is below {minimum_width}px"
        )
    if image.height < minimum_height:
        warnings.append(
            f"Source height {image.height}px is below {minimum_height}px"
        )

    quality = estimate_quality(image)
    if quality < minimum_quality:
        warnings.append(
            f"Potentially low-quality/blurry image (score={quality:.2f})"
        )
    return warnings


def save_image(
    image: Image.Image,
    path: Path,
    output_format: str,
    quality: int,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "JPEG":
        image = image.convert("RGB")
        image.save(
            path, format="JPEG", quality=quality, optimize=True, progressive=True
        )
    elif output_format == "WEBP":
        image.save(path, format="WEBP", quality=quality, method=6)
    elif output_format == "PNG":
        image.save(path, format="PNG", optimize=True, compress_level=9)
    elif output_format == "AVIF":
        image.save(path, format="AVIF", quality=quality)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

    # Saving without EXIF/XMP arguments intentionally strips source metadata.
    return path.stat().st_size


def find_images(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_FORMATS
    )


def process_image(
    input_path: Path,
    output_dir: Path,
    resolutions: list[Resolution],
    output_format: str,
    quality: int,
    fit_mode: str,
    background: tuple[int, int, int],
    enhancement: dict,
    quality_config: dict,
    dry_run: bool,
    logger: logging.Logger,
    stats: ProcessingStats,
) -> None:
    try:
        stats.original_bytes += input_path.stat().st_size

        with Image.open(input_path) as source:
            logger.info("Processing: %s", input_path)

            image = correct_orientation(source)

            warnings = validate_image(
                image,
                int(quality_config.get("minimum_width", 300)),
                int(quality_config.get("minimum_height", 300)),
                float(quality_config.get("minimum_quality_score", 5.0)),
            )
            for warning in warnings:
                stats.warnings += 1
                logger.warning("%s | %s", input_path.name, warning)

            image = normalize_image_mode(image, background)

            image = enhance_image(
                image,
                float(enhancement.get("brightness", 1.0)),
                float(enhancement.get("contrast", 1.0)),
                float(enhancement.get("saturation", 1.0)),
                float(enhancement.get("sharpness", 1.0)),
            )
            image = reduce_noise(
                image, int(enhancement.get("noise_reduction", 0))
            )
            image = sharpen_image(
                image, int(enhancement.get("sharpen", 0))
            )

            base_name = normalize_filename(input_path.name)
            extension = "jpg" if output_format == "JPEG" else output_format.lower()

            for resolution in resolutions:
                processed = resize_image(
                    image, resolution, fit_mode, background
                )
                output_path = (
                    output_dir
                    / resolution.name
                    / f"{base_name}_{resolution.name}.{extension}"
                )

                if dry_run:
                    logger.info("[DRY RUN] Would create: %s", output_path)
                    continue

                output_size = save_image(
                    processed, output_path, output_format, quality
                )
                stats.output_bytes += output_size
                logger.info(
                    "Created %s | %dx%d | %.2f KB",
                    output_path,
                    resolution.width,
                    resolution.height,
                    output_size / 1024,
                )

            stats.processed += 1

    except (UnidentifiedImageError, OSError, ValueError) as error:
        stats.failed += 1
        logger.error("Failed: %s | %s", input_path, error)


def generate_report(
    path: Path,
    stats: ProcessingStats,
    resolutions: list[Resolution],
    output_format: str,
    quality: int,
    fit_mode: str,
) -> None:
    report = {
        "processing": {
            "processed": stats.processed,
            "failed": stats.failed,
            "warnings": stats.warnings,
        },
        "configuration": {
            "format": output_format,
            "quality": quality,
            "fit_mode": fit_mode,
            "resolutions": [
                {"name": r.name, "width": r.width, "height": r.height}
                for r in resolutions
            ],
        },
        "storage": {
            "original_mb": round(stats.original_bytes / 1024 / 1024, 2),
            "output_mb": round(stats.output_bytes / 1024 / 1024, 2),
            "saved_mb": round(stats.saved_bytes / 1024 / 1024, 2),
            "compression_percentage": round(stats.compression_percentage, 2),
        },
        "performance": {
            "elapsed_seconds": round(stats.elapsed_seconds, 2)
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=4) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch image processor for e-commerce product assets."
    )
    parser.add_argument("input", nargs="?", type=Path, help="Input image directory")
    parser.add_argument("-o", "--output", type=Path, default=Path("output"))
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--resolution", help="One standard resolution")
    parser.add_argument("--resolutions", nargs="+", help="Multiple standard resolutions")
    parser.add_argument(
        "--custom-resolution",
        nargs=2,
        type=int,
        metavar=("WIDTH", "HEIGHT"),
        help="Custom resolution",
    )
    parser.add_argument("--list-resolutions", action="store_true")
    parser.add_argument(
        "--format",
        choices=sorted(SUPPORTED_OUTPUT_FORMATS),
        help="Override configured output format",
    )
    parser.add_argument("--quality", type=int, help="Override configured quality (1-100)")
    parser.add_argument(
        "--fit",
        choices=["cover", "contain", "stretch"],
        help="Override configured fit mode",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--report", type=Path, default=Path("processing_report.json")
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(args.config)

    if args.list_resolutions:
        print_resolutions(config)
        return 0

    if args.input is None:
        parser.error("Input directory is required unless --list-resolutions is used.")

    if not args.input.exists() or not args.input.is_dir():
        parser.error(f"Input directory does not exist or is not a directory: {args.input}")

    try:
        validate_config(config)
        output_format = (args.format or config.get("output_format", "WEBP")).upper()
        quality = args.quality if args.quality is not None else int(config.get("quality", 85))
        if not 1 <= quality <= 100:
            raise ValueError("quality must be between 1 and 100")
        fit_mode = args.fit or config.get("fit_mode", "contain")

        if args.resolutions:
            selected_names = args.resolutions
        elif args.resolution:
            selected_names = [args.resolution]
        else:
            selected_names = None

        resolutions = build_resolutions(
            config,
            selected_names=selected_names,
            custom=tuple(args.custom_resolution) if args.custom_resolution else None,
        )
        if not resolutions:
            raise ValueError("No resolutions selected.")

    except ValueError as error:
        parser.error(str(error))

    background_config = config.get(
        "background", {"r": 255, "g": 255, "b": 255}
    )
    background = (
        int(background_config["r"]),
        int(background_config["g"]),
        int(background_config["b"]),
    )

    args.output.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(args.output / "image_processor.log")

    images = find_images(args.input)
    if not images:
        logger.warning("No supported images found.")
        return 0

    logger.info("Found %d image(s).", len(images))
    logger.info("Format=%s | Quality=%d | Fit=%s", output_format, quality, fit_mode)
    logger.info(
        "Resolutions=%s",
        ", ".join(f"{r.name}={r.width}x{r.height}" for r in resolutions),
    )

    stats = ProcessingStats(start_time=time.time())
    enhancement = config.get("enhancement", {})
    quality_config = config.get("quality_check", {})

    for image_path in images:
        process_image(
            input_path=image_path,
            output_dir=args.output,
            resolutions=resolutions,
            output_format=output_format,
            quality=quality,
            fit_mode=fit_mode,
            background=background,
            enhancement=enhancement,
            quality_config=quality_config,
            dry_run=args.dry_run,
            logger=logger,
            stats=stats,
        )

    generate_report(
        args.report, stats, resolutions, output_format, quality, fit_mode
    )

    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info("Processed : %d", stats.processed)
    logger.info("Failed    : %d", stats.failed)
    logger.info("Warnings  : %d", stats.warnings)
    logger.info("Original  : %.2f MB", stats.original_bytes / 1024 / 1024)
    logger.info("Output    : %.2f MB", stats.output_bytes / 1024 / 1024)
    logger.info("Saved     : %.2f MB", stats.saved_bytes / 1024 / 1024)
    logger.info("Reduction : %.2f%%", stats.compression_percentage)
    logger.info("Time      : %.2f seconds", stats.elapsed_seconds)
    logger.info("Report    : %s", args.report)
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
