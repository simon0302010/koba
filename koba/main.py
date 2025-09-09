import os
import sys
import math
import logging

import click
import numpy as np
from PIL import Image, UnidentifiedImageError

from . import __version__
from .core import charsets


logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.ERROR
)

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
    "--char-aspect", default=1.6, show_default=True,
    help="Set character height/width ratio."
)
@click.option(
    "--logging-level",
    default="ERROR",
    show_default=True,
    help="Set logging level. Options: CRITICAL, ERROR, WARNING, INFO, DEBUG."
)
@click.option("--save-blocks", is_flag=True)
def main(file, char_aspect, logging_level, save_blocks):
    # update logging level
    logging.getLogger().setLevel(getattr(logging, logging_level.upper(), logging.ERROR))
    
    # loading file and reading basic info
    try:
        img = Image.open(file)
    except UnidentifiedImageError:
        logging.critical(f"Unsupported or unreadable image format for file: {file}.")
        sys.exit(1)
    img_arr = np.array(img)
    height, width = img_arr.shape[:2]
    logging.info(f"Image is {width}x{height} pixels.")
    
    # calculating important metrics
    chars_width = os.get_terminal_size().columns
    chars_height = math.ceil((height * chars_width / width) / char_aspect)
    ppc_w = math.ceil(width / chars_width)
    ppc_h = math.ceil(height / chars_height)
    
    logging.info(f"Image will be {chars_width}x{chars_height} chars.")
    logging.info(f"Every char has to represent {ppc_w}x{ppc_h} pixels.")
    logging.info(f"Max chars: {chars_width*chars_height}")
    
    # splitting into blocks
    blocks = []
    for y in range(0, height, ppc_h):
        for x in range(0, width, ppc_w):
            block = img_arr[y:y+ppc_h, x:x+ppc_w]
            blocks.append(block)
            
    logging.info(f"{len(blocks)} blocks created.")
    
    if save_blocks:
        logging.info("Saving image blocks...")
        blocks_dir = "blocks"
        os.makedirs(blocks_dir, exist_ok=True)
        for idx, block in enumerate(blocks):
            img_block = Image.fromarray(block)
            img_block.save(os.path.join(blocks_dir, f"block_{idx:04d}.png"))