# E-Commerce Image Processor

A lightweight, configurable Python image-processing pipeline for **local e-commerce and grocery product catalogs**.

It takes inconsistent source images—different dimensions, formats, quality levels, orientations, and filenames—and turns them into consistent, optimized assets ready for your app.

> Built with Python + Pillow. Duplicate detection is intentionally **not included**.

## Why use it?

Product images collected from different sources rarely have consistent:

- Resolution
- Aspect ratio
- Format
- Compression
- Orientation
- Naming
- Background/canvas
- Visual quality

This tool provides one repeatable pipeline for preparing those assets before they enter your application.

## Features

### Image normalization
- Resize images to standard app resolutions
- Custom width × height support
- Generate multiple resolutions in one run
- `contain`, `cover`, and `stretch` fitting modes
- Preserve proportions without distortion when using `contain`/`cover`
- EXIF orientation correction
- Transparency handling
- Configurable background color
- Filename normalization

### Image optimization
- WebP output
- JPEG output
- PNG output
- AVIF output when supported by the installed Pillow build
- Configurable output quality
- Metadata stripping by saving generated assets without source metadata
- Optimized PNG/JPEG/WebP encoding
- File-size and compression statistics

### Image enhancement
- Brightness adjustment
- Contrast adjustment
- Saturation adjustment
- Sharpness adjustment
- Optional noise reduction
- Optional post-processing sharpening

### Quality checks
- Minimum source width check
- Minimum source height check
- Basic low-detail/blurriness warning
- Processing warnings in console/logs
- Failed-image logging

### Batch processing
- Recursive folder scanning
- Process hundreds or thousands of images
- Generate separate output directories per resolution
- Dry-run mode
- JSON processing report
- Persistent processing log

### Resolution system
Built-in presets:

| Preset | Resolution | Typical use |
|---|---:|---|
| `tiny` | 100×100 | Tiny UI elements |
| `thumbnail` | 150×150 | Search/list thumbnails |
| `small` | 300×300 | Compact cards |
| `card` | 400×400 | Product cards |
| `medium` | 600×600 | Larger cards |
| `detail` | 800×800 | Product detail |
| `large` | 1200×1200 | High-resolution view |

You can also define your own standard presets in `config.json`.

### Intentionally excluded

**Duplicate detection is not implemented.**

---

## Requirements

- Python **3.10+**
- Pillow

Pillow provides prebuilt wheels for major operating systems, so the normal installation path does not require manually compiling image libraries. See the Pillow installation documentation for platform-specific details.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ecommerce-image-processor.git
cd ecommerce-image-processor
```

### 2. Install automatically

#### Windows

```bat
install.bat
```

Or PowerShell:

```powershell
.\install.ps1
```

#### Linux/macOS

```bash
chmod +x install.sh
./install.sh
```

The installer:

1. Detects Python
2. Creates `.venv`
3. Upgrades pip
4. Installs dependencies from `requirements.txt`

### 3. Put images into `input/`

Example:

```text
input/
├── vegetables/
│   ├── Tomato.JPG
│   ├── potato image.png
│   └── Green Capsicum.jpeg
├── fruits/
│   ├── Apple.jpg
│   └── Banana.png
└── grains/
    └── rice.webp
```

### 4. Process them

```bash
python image_processor.py input --output output
```

On Windows after installation you can also use:

```bat
run.bat input --output output
```

On Linux/macOS:

```bash
./run.sh input --output output
```

---

## Default output

The default configuration generates:

```text
output/
├── thumbnail/
├── card/
├── detail/
└── image_processor.log

processing_report.json
```

For example:

```text
input/vegetables/Tomato.JPG

        ↓

output/
└── card/
    └── tomato_card.webp

output/
└── detail/
    └── tomato_detail.webp

output/
└── thumbnail/
    └── tomato_thumbnail.webp
```

The original files in `input/` are never modified.

---

## Resolution selection

### Use configured default resolutions

```bash
python image_processor.py input --output output
```

Default:

```text
thumbnail → 150×150
card      → 400×400
detail    → 800×800
```

### List available presets

```bash
python image_processor.py --list-resolutions
```

### Generate one standard resolution

```bash
python image_processor.py input --resolution card
```

### Generate multiple standard resolutions

```bash
python image_processor.py input \
  --resolutions thumbnail card detail
```

### Generate a custom resolution

```bash
python image_processor.py input \
  --custom-resolution 512 512
```

### Generate a rectangular custom resolution

```bash
python image_processor.py input \
  --custom-resolution 1200 800
```

### Combine standard + custom resolution

```bash
python image_processor.py input \
  --resolutions thumbnail card detail \
  --custom-resolution 512 512
```

---

## Fit modes

### `contain` — recommended

Keeps the entire product visible and adds the configured background when required.

```bash
python image_processor.py input --fit contain
```

Recommended for grocery/product catalogs.

### `cover`

Fills the target dimensions completely and crops the image if necessary.

```bash
python image_processor.py input --fit cover
```

Useful when your UI requires every card to be completely filled.

### `stretch`

Forces the image into the target dimensions.

```bash
python image_processor.py input --fit stretch
```

Generally not recommended for product photography because it can distort objects.

---

## Output formats

### WebP — recommended default

```bash
python image_processor.py input --format WEBP --quality 85
```

### JPEG

```bash
python image_processor.py input --format JPEG --quality 90
```

### PNG

```bash
python image_processor.py input --format PNG
```

### AVIF

```bash
python image_processor.py input --format AVIF --quality 80
```

AVIF support depends on the Pillow build and environment.

---

## Configuration

Most users should configure the project through `config.json`.

Example:

```json
{
    "output_format": "WEBP",
    "quality": 85,
    "fit_mode": "contain",

    "background": {
        "r": 255,
        "g": 255,
        "b": 255
    },

    "enabled_resolutions": [
        "thumbnail",
        "card",
        "detail"
    ]
}
```

### Change standard resolutions

For example:

```json
"standard_resolutions": {
    "thumbnail": [150, 150],
    "card": [512, 512],
    "detail": [1024, 1024]
}
```

Then:

```bash
python image_processor.py input
```

will automatically use the new values.

### Add custom resolutions to config

```json
"custom_resolutions": [
    [512, 512],
    [1200, 800]
]
```

These are generated in addition to the enabled standard resolutions.

---

## Image enhancement

The default configuration deliberately performs no aggressive enhancement.

### Brightness

```json
"brightness": 1.05
```

### Contrast

```json
"contrast": 1.05
```

### Saturation

```json
"saturation": 1.05
```

### Sharpness

```json
"sharpness": 1.10
```

Keep these values close to `1.0` to avoid unnatural product images.

### Noise reduction

```json
"noise_reduction": 1
```

Valid range:

```text
0–5
```

### Additional sharpening

```json
"sharpen": 1
```

Valid range:

```text
0–5
```

---

## Quality checks

The processor can warn about source images that are too small or potentially low quality.

Example:

```json
"quality_check": {
    "minimum_width": 300,
    "minimum_height": 300,
    "minimum_quality_score": 5.0
}
```

These checks **warn rather than silently delete or reject your originals**.

---

## Dry run

Preview what would happen without creating processed images:

```bash
python image_processor.py input \
  --output output \
  --dry-run
```

This is recommended before processing a large repository.

---

## Processing report

After a run, the tool creates:

```text
processing_report.json
```

Example:

```json
{
    "processing": {
        "processed": 250,
        "failed": 2,
        "warnings": 11
    },
    "storage": {
        "original_mb": 842.5,
        "output_mb": 116.3,
        "saved_mb": 726.2,
        "compression_percentage": 86.2
    }
}
```

This lets you measure how much storage/bandwidth optimization the pipeline achieved.

---

## Logs

Processing logs are written to:

```text
output/image_processor.log
```

The log includes:

- Processed files
- Generated assets
- Resolution
- Output size
- Warnings
- Errors

---

## Recommended grocery-app configuration

For a typical local grocery/e-commerce application, a good starting point is:

```json
{
    "output_format": "WEBP",
    "quality": 85,
    "fit_mode": "contain",
    "enabled_resolutions": [
        "thumbnail",
        "card",
        "detail"
    ]
}
```

This gives:

```text
150×150  → list/search
400×400  → product cards
800×800  → product detail
```

Keep the original images outside the generated output tree so you can regenerate assets later if your app's requirements change.

---

## Architecture

```text
                    SOURCE IMAGE
                         │
                         ▼
                ┌─────────────────┐
                │ EXIF correction │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │ Quality checks  │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │ Mode / Alpha    │
                │ normalization   │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │ Enhancement     │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │ Resize / Fit    │
                └────────┬────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
        Thumbnail      Card         Detail
        150×150       400×400       800×800
            │            │            │
            └────────────┼────────────┘
                         ▼
                ┌─────────────────┐
                │ Format + Quality│
                │ optimization    │
                └────────┬────────┘
                         ▼
                    APP-READY
                      ASSETS
```

---

## Project structure

```text
ecommerce-image-processor/
├── .github/
│   └── workflows/
│       └── ci.yml
├── input/
│   └── .gitkeep
├── output/
│   └── .gitkeep
├── tests/
│   └── test_processor.py
├── config.json
├── image_processor.py
├── install.bat
├── install.ps1
├── install.sh
├── requirements.txt
├── run.bat
├── run.sh
├── .gitignore
├── CHANGELOG.md
├── LICENSE
└── README.md
```

---

## Development

Create the environment:

```bash
python -m venv .venv
```

Activate it:

### Windows

```bat
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Install:

```bash
python -m pip install -r requirements.txt
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

---

## Security and privacy

The processor runs locally and does not require an external image-processing API.

Generated images are written to the configured local output directory.

Source metadata is not copied into generated assets.

Do not commit private product images, credentials, API keys, or other sensitive files.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Roadmap

Potential future additions:

- Automatic background removal
- Product/object centering
- AI-assisted product detection
- CLI progress bar
- GUI/web interface
- Preset profiles for different storefronts
- Image quality scoring with a dedicated model
- Cloud/object-storage integration

Duplicate detection is intentionally outside the current scope.

---

## Contributing

Pull requests are welcome.

For larger changes, open an issue first to discuss the proposed approach.

---

## Author

Built as a reusable image-preprocessing utility for e-commerce applications.
