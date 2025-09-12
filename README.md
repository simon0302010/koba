![Hackatime](https://hackatime-badge.hackclub.com/U08HC7N4JJW/koba)
![PyPI - Version](https://img.shields.io/pypi/v/koba)

# koba
A terminal image renderer that can construct images using any set of unicode symbols.

## Installation

```bash
pip install koba
```

## Quick Start

```bash
# Basic usage
koba image.png

# Use different similarity engine
koba image.jpg --engine diff

# Custom character set (box drawing characters)
koba image.png --char-range 9600-9632

# Custom font
koba image.jpg --font /path/to/font.ttf
```

## Features

- 🎨 **Multiple similarity engines** for different visual styles
- 🔤 **Custom character ranges** including Unicode, Braille, and symbols
- 🖋️ **Custom font support** with TTF files
- ⚡ **Multi-threaded processing** for fast rendering
- 🎛️ **Adjustable output quality** with scaling and aspect ratio control

## Usage

```
koba [OPTIONS] FILE
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--version` | Show version and exit | |
| `--char-aspect INTEGER` | Character height-to-width ratio for aspect-correct output | `2` |
| `--logging-level TEXT` | Set verbosity: CRITICAL, ERROR, WARNING, INFO, DEBUG | `ERROR` |
| `--save-blocks` | Save image blocks as PNG files in 'blocks/' directory | |
| `--save-chars` | Save rendered character images in 'chars/' directory | |
| `-e, --engine TEXT` | Similarity metric (see engines below) | `diff` |
| `--font TEXT` | Path to custom TTF font file | |
| `--char-range TEXT` | Unicode range as start-end (e.g., 32-128) | `32-128` |
| `--stretch-contrast` | Stretch image contrast to potentially improve results  | |
| `--scale FLOAT` | Scale factor for image display | `1.0` |

## Similarity Engines

Choose the engine that best fits your artistic vision:

- **`diff`** - Pixel-wise difference, balanced quality/speed (default)
- **`brightness`** - Fast, good for simple images
- **`mse`** - Mean squared error, precise pixel matching
- **`ssim`** - Structural similarity, good for complex images
- **`ncc`** - Normalized cross-correlation, good for textured images
- **`hist`** - Histogram comparison, emphasizes tonal distribution
- **`cosine`** - Cosine similarity, unique artistic effects

## Character Ranges

### Popular Unicode Ranges
- `32-126` - Basic ASCII printable characters
- `32-128` - Extended ASCII (default)
- `9600-9631` - Block drawing characters
- `9632-9727` - Geometric shapes
- `10240-10495` - Braille patterns (high detail)
- `0-1114111` - Full Unicode range (use with appropriate font)

### Example Character Sets
```bash
# Retro terminal look
koba image.png --char-range 32-126

# Geometric patterns
koba image.png --char-range 9632-9727
```

## Examples

### Basic Usage
```bash
koba photo.jpg
```

### Debugging
```bash
koba image.png --logging-level DEBUG --save-blocks --save-chars
```

### Custom Font with Specific Characters
```bash
koba logo.png --font ./fonts/custom.ttf --char-range 65-90 --engine mse
```

## Technical Details

- Automatically adjusts output to terminal width
- Maintains aspect ratio with configurable character aspect
- Uses multiprocessing for parallel block processing
- Supports all PIL-compatible image formats
- Minimum block size: 8×8 pixels for SSIM, 4×4 for other engines

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.