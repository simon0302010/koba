import os
import sys
import math
import time
import logging
import concurrent.futures

import click
import numpy as np
from PIL import Image, UnidentifiedImageError

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
    help="Set character height/width ratio."
)
@click.option(
    "--logging-level",
    default="ERROR",
    show_default=True,
    help="Set logging level. Options: CRITICAL, ERROR, WARNING, INFO, DEBUG."
)
@click.option("--save-blocks", is_flag=True, help="Saves images of blocks to blocks/")
@click.option("--save-chars", is_flag=True, help="Saves images of chars in the specified range to chars/")
@click.option("--engine", "-e", default="brightness", help="Which engine to use for similarity checking (brightness, ssim, diff, mse)", show_default=True)
@click.option("--font", help="Overwrites default font path.", default=None)
@click.option("--char-range", help="Sets the range of unicode symbols to use (start-end)", default="32-128", show_default=True)
def main(file, char_aspect, logging_level, save_blocks, save_chars, engine, font, char_range):
    # update logging level
    logging.getLogger().setLevel(getattr(logging, logging_level.upper(), logging.ERROR))
    
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
        img = Image.open(file).convert("L")
    except UnidentifiedImageError:
        logging.critical(f"Unsupported or unreadable image format for file: {file}.")
        sys.exit(1)
    img_arr = np.array(img)
    height, width = img_arr.shape[:2]
    logging.debug(f"Image is {width}x{height} pixels.")
    
    # calculating important metrics
    chars_width = os.get_terminal_size().columns
    chars_height = math.ceil((height * chars_width / width) / char_aspect)
    # ppc_w = math.ceil(width / chars_width)
    # ppc_h = math.ceil(height / chars_height)
    
    # distribute extra pixels
    block_widths = [width // chars_width] * chars_width
    for i in range(width % chars_width):
        block_widths[i] += 1

    block_heights = [height // chars_height] * chars_height
    for i in range(height % chars_height):
        block_heights[i] += 1

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

    results = [""] * len(blocks)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_idx = {
            executor.submit(process_block, arg): idx
            for idx, arg in enumerate(block_args)
        }
        for i, future in enumerate(concurrent.futures.as_completed(future_to_idx), 1):
            idx = future_to_idx[future]
            results[idx] = future.result()
            print(f"Processed {i}/{len(future_to_idx)} blocks", end="\r", flush=True)

    logging.info(f"Took {round(time.time() - start_time, 2)}s")

    all_chars = "".join(results)
    print()
    print(all_chars)
