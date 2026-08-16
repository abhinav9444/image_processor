# E-Commerce Image Processor

A lightweight, configurable Python image-processing pipeline for local e-commerce and grocery product catalogs.

It takes inconsistent source images—different dimensions, formats, quality levels, orientations, and filenames—and turns them into consistent, optimized assets ready for your app.

> Built with Python + Pillow. Duplicate detection is intentionally **not included**.

## Features

- Recursive batch processing
- Standard resolution presets
- Custom width × height resolutions
- Generate multiple resolutions in one run
- `contain`, `cover`, and `stretch` fitting modes
- JPEG / PNG / WebP / AVIF output
- Configurable output quality
- EXIF orientation correction
- Transparency/background handling
- Brightness, contrast, saturation and sharpness adjustment
- Optional noise reduction and sharpening
- Minimum-resolution and basic quality warnings
- Filename normalization
- Source metadata not copied into generated assets
- Dry-run mode
- Processing logs
- JSON processing report
- Storage/compression statistics
- Configurable input/output/report paths
- CLI path overrides
- Windows, PowerShell, Linux and macOS installation scripts
- GitHub Actions CI

## Requirements

- Python 3.10+
- Pillow

## Quick start

Clone the repository and install dependencies.

### Windows

```bat
install.bat
```

or:

```powershell
.\install.ps1
```

### Linux/macOS

```bash
chmod +x install.sh
./install.sh
```

Then:

```bash
python image_processor.py --list-resolutions
python image_processor.py
```

## Input and output paths

You can point the processor at **any folders on your computer**. You do not need to copy images into the repository.

### Option 1 — command-line paths

```bash
python image_processor.py --input-dir "D:/MyStore/product-images" --output-dir "D:/MyStore/processed-images"
```

Windows example:

```powershell
python image_processor.py --input-dir "C:/Users/Abhinav/Pictures/products" --output-dir "D:/Ecommerce/processed"
```

The command-line paths override `config.json`.

### Option 2 — configure paths once

Set the `paths` section in `config.json`:

```json
"paths": {
    "input_dir": "D:/MyStore/product-images",
    "output_dir": "D:/MyStore/processed-images",
    "report_file": "D:/MyStore/processed-images/processing_report.json"
}
```

Then simply run:

```bash
python image_processor.py
```

### Path priority

```text
CLI --input-dir / --output-dir
        ↓
config.json paths
        ↓
./input and ./output
```

The existing positional syntax remains supported:

```bash
python image_processor.py input --output output
```

## Standard resolutions

| Preset | Resolution | Typical use |
|---|---:|---|
| `tiny` | 100×100 | Tiny UI elements |
| `thumbnail` | 150×150 | Search/list thumbnails |
| `small` | 300×300 | Compact cards |
| `card` | 400×400 | Product cards |
| `medium` | 600×600 | Larger cards |
| `detail` | 800×800 | Product detail |
| `large` | 1200×1200 | High-resolution view |

List presets:

```bash
python image_processor.py --list-resolutions
```

Generate configured defaults:

```bash
python image_processor.py
```

One standard resolution:

```bash
python image_processor.py --resolution card
```

Multiple standard resolutions:

```bash
python image_processor.py --resolutions thumbnail card detail
```

Custom resolution:

```bash
python image_processor.py --custom-resolution 512 512
```

Rectangular custom resolution:

```bash
python image_processor.py --custom-resolution 1200 800
```

Combine standard and custom resolutions:

```bash
python image_processor.py --resolutions thumbnail card detail --custom-resolution 512 512
```

## Fit modes

### `contain` — recommended

Keeps the entire product visible and adds the configured background when required.

```bash
python image_processor.py --fit contain
```

### `cover`

Fills the target dimensions and crops when necessary.

```bash
python image_processor.py --fit cover
```

### `stretch`

Forces the image into the target dimensions and may distort it.

```bash
python image_processor.py --fit stretch
```

## Output formats

WebP:

```bash
python image_processor.py --format WEBP --quality 85
```

JPEG:

```bash
python image_processor.py --format JPEG --quality 90
```

PNG:

```bash
python image_processor.py --format PNG
```

AVIF:

```bash
python image_processor.py --format AVIF --quality 80
```

AVIF support depends on the installed Pillow build.

## Configuration

The main configuration file is `config.json`.

Recommended starting configuration for a grocery/e-commerce app:

```json
{
    "paths": {
        "input_dir": "D:/MyStore/product-images",
        "output_dir": "D:/MyStore/processed-images",
        "report_file": "D:/MyStore/processed-images/processing_report.json"
    },
    "output_format": "WEBP",
    "quality": 85,
    "fit_mode": "contain",
    "enabled_resolutions": ["thumbnail", "card", "detail"]
}
```

You can change standard resolutions directly in `config.json`:

```json
"standard_resolutions": {
    "thumbnail": [150, 150],
    "card": [512, 512],
    "detail": [1024, 1024]
}
```

Add persistent custom resolutions:

```json
"custom_resolutions": [
    [512, 512],
    [1200, 800]
]
```

## Image enhancement

The default configuration is intentionally conservative.

```json
"enhancement": {
    "brightness": 1.0,
    "contrast": 1.0,
    "saturation": 1.0,
    "sharpness": 1.0,
    "noise_reduction": 0,
    "sharpen": 0
}
```

Keep the values near `1.0` to avoid unnatural product images.

## Quality checks

The processor warns about source images that may be unsuitable for high-quality app assets:

```json
"quality_check": {
    "minimum_width": 300,
    "minimum_height": 300,
    "minimum_quality_score": 5.0
}
```

These checks warn rather than delete or modify your originals.

## Dry run

Preview processing without creating generated images:

```bash
python image_processor.py --dry-run
```

## Output

For the default configuration:

```text
output/
├── thumbnail/
├── card/
├── detail/
└── image_processor.log
```

The report is written to the configured `paths.report_file` location.

Original input files are never modified.

## Processing report

The JSON report contains:

- processed count
- failed count
- warning count
- output format
- quality
- fit mode
- generated resolutions
- original storage size
- output storage size
- estimated storage reduction
- processing time

## Project structure

```text
image_processor/
├── .github/workflows/ci.yml
├── input/
├── output/
├── tests/
├── config.json
├── image_processor.py
├── requirements.txt
├── install.bat
├── install.ps1
├── install.sh
├── run.bat
├── run.sh
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

## Development

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it and install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Recommended workflow for your e-commerce image repository

Keep original/source assets in a separate location, then point `input_dir` to that directory and `output_dir` to your app's generated asset directory.

A practical setup is:

```text
Original image repository
        ↓
Image Processor
        ↓
┌───────────────┬────────────┬──────────────┐
│ 150×150       │ 400×400    │ 800×800      │
│ thumbnails    │ product    │ detail       │
│               │ cards      │ images       │
└───────────────┴────────────┴──────────────┘
```

For most grocery/product catalogs, `WebP + quality 85 + contain` is a good starting point.

## Duplicate detection

Duplicate and near-duplicate detection is intentionally **not implemented** in this project.

## License

MIT License. See `LICENSE`.

## Roadmap

Potential future additions include automatic background removal, product/object centering, AI-assisted product detection, GUI/web interface, storefront-specific presets and cloud/object-storage integration.
