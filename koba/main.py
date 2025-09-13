import os
import sys
import math
import time
import logging
import concurrent.futures

import click
import numpy as np
from tqdm import tqdm
from PIL import Image, ImageOps, UnidentifiedImageError

from . import __version__
from .core import charsets, unify


logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.ERROR
)

def process_block(args):
    block, characters, engine, save_chars = args
    return unify.get_character(block, characters, save_chars, engine)

@click.command("koba")
@click.version_option(__version__)
@click.argument(
    "file",
    type=click.Path(
        exists=True,
        file_okay=True,
        readable=True,
    )
)
@click.option(
    "--char-aspect", default=2, show_default=True,
    help="Character height-to-width ratio (for aspect-correct output)."
)
@click.option(
    "--logging-level",
    default="ERROR",
    show_default=True,
    help="Set the logging verbosity. Options: CRITICAL, ERROR, WARNING, INFO, DEBUG."
)
@click.option(
    "--save-blocks", is_flag=True,
    help="Save each image block as a PNG file in the 'blocks/' directory."
)
@click.option(
    "--save-chars", is_flag=True,
    help="Save rendered character images in the 'chars/' directory."
)
@click.option(
    "--engine", "-e", default="diff", show_default=True,
    help="Similarity metric to use: brightness, ssim, diff, mse, ncc, hist, or cosine."
)
@click.option(
    "--font", default=None,
    help="Path to a custom TTF font file (overrides the default font)."
)
@click.option(
    "--char-range", default="32-126", show_default=True,
    help="Unicode range of characters to use, as start-end (e.g., 32-126)."
)
@click.option(
    "--stretch-contrast",
    is_flag=True,
    help="Stretch image contrast to use the full brightness range."
)
@click.option(
    "--scale",
    default=1.0,
    help="Sets the scale at which to render the image. Will be overwritten if image needs to be scaled down to allow proper processing."
)
@click.option(
    "--invert",
    is_flag=True,
    help="Inverts the image before processing."
)
def main(file, char_aspect, logging_level, save_blocks, save_chars, engine, font, char_range, stretch_contrast, scale, invert):
    # update logging level
    logging.getLogger().setLevel(getattr(logging, logging_level.upper(), logging.ERROR))
    
    if font and not font.endswith(".ttf"):
        logging.critical("Please provide a font in TTF format.")
        sys.exit(1)

    start_time = time.time()

    split_range = char_range.split("-")
    start_char = split_range[0]
    end_char = split_range[1]
    if start_char.isnumeric() and end_char.isnumeric():
        start_char = int(start_char)
        end_char = int(end_char)
    else:
        logging.critical("Wrong format for char-range.")
        sys.exit(1)
    
    # loading file and reading basic info
    try:
        # convert to grayscale and apply constrast stretching
        img = Image.open(file).convert("L")
        if invert:
            img = ImageOps.invert(img)
        if stretch_contrast:
            img = ImageOps.autocontrast(img)
    except UnidentifiedImageError:
        logging.critical(f"Unsupported or unreadable image format for file: {file}.")
        sys.exit(1)
    img_arr = np.array(img)
    height, width = img_arr.shape[:2]
    logging.debug(f"Image is {width}x{height} pixels.")
    
    # calculating important metrics
    terminal_width = os.get_terminal_size().columns
    chars_width = terminal_width
    
    # calculate required sizes
    min_block_width = 10 / char_aspect
    min_block_height = 10

    scale = min(scale, 1.0)
    
    max_chars_width_by_block_width = int(width // min_block_width)
    max_chars_width_by_block_height = int(height // min_block_height * char_aspect)

    max_chars_width = min(max_chars_width_by_block_width, max_chars_width_by_block_height)

    chars_width = min(int(terminal_width * scale), terminal_width, max_chars_width)

    chars_width = max(chars_width, 1)

    chars_height = math.ceil((height * chars_width / width) / char_aspect)
    
    # recalculate block sizes
    block_widths = [width // chars_width] * chars_width
    for i in range(width % chars_width):
        block_widths[i] += 1

    block_heights = [height // chars_height] * chars_height
    for i in range(height % chars_height):
        block_heights[i] += 1

    logging.debug(f"Terminal is {terminal_width} chars wide.")
    logging.debug(f"Image will be {chars_width}x{chars_height} chars.")
    logging.debug(f"Block widths: {block_widths[:5]}... (total {len(block_widths)})")
    logging.debug(f"Block heights: {block_heights[:5]}... (total {len(block_heights)})")

    if min(block_heights + block_widths) <= 7 and str(engine).lower() == "ssim":
        logging.critical("Image blocks are too small for SSIM. Please use another engine.")
        sys.exit(1)

    # splitting into blocks with variable sizes
    blocks = []
    y = 0
    for bh in block_heights:
        x = 0
        for bw in block_widths:
            block = img_arr[y:y+bh, x:x+bw]
            blocks.append(block)
            x += bw
        y += bh

    logging.debug(f"{len(blocks)} blocks created.")
    
    if save_blocks:
        logging.info("Saving image blocks...")
        blocks_dir = "blocks"
        os.makedirs(blocks_dir, exist_ok=True)
        for idx, block in enumerate(blocks):
            img_block = Image.fromarray(block)
            img_block.save(os.path.join(blocks_dir, f"{idx:04d}.png"))
    
    characters = charsets.get_range(start_char, end_char)
    all_chars = ""

    # prepare arguments
    block_args = [(block, characters, engine.lower(), save_chars) for block in blocks]

    if font:
        unify.font_path = font

    if abs(start_char - end_char) >= 400:
        for char in tqdm(characters, total=len(characters), desc="Loading fonts"):
            unify.get_font(char)

    results = [""] * len(blocks)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_idx = {
            executor.submit(process_block, arg): idx
            for idx, arg in enumerate(block_args)
        }
        try:
            for future in tqdm(concurrent.futures.as_completed(future_to_idx), total=len(future_to_idx), desc="Processing blocks"):
                idx = future_to_idx[future]
                results[idx] = future.result()
        except ValueError as e:
            logging.critical(str(e))
            sys.exit(1)

    logging.info(f"Took {round(time.time() - start_time, 2)}s")

    all_chars = "".join(results)
    all_chars = '\n'.join(all_chars[i:i+chars_width] for i in range(0, len(all_chars), chars_width))
    print()
    print(all_chars)
