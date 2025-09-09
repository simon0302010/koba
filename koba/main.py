import os
import sys
import logging

import click
import numpy as np
from PIL import Image, UnidentifiedImageError

from . import __version__
from .core import similarity


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
    "--char-aspect", default=0.5,
    help="Character wdith/height ratio (default: 0.5 for 1:2 aspect)."
)
@click.option(
    "--logging-level",
    default="ERROR",
    help="Set logging level. Options: CRITICAL, ERROR, WARNING, INFO, DEBUG. (default: ERROR)"
)
def main(file, char_aspect, logging_level):
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
    chars_height = round(height / (width / chars_width), 2)
    ppc_w = round(width / chars_width, 2)
    ppc_h = round(ppc_w / char_aspect, 2)
    
    logging.info(f"Image will be {chars_width}x{chars_height} chars.")
    logging.info(f"Every char has to represent {ppc_w}x{ppc_h} pixels.")