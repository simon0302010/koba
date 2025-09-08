import os
import sys
import logging
from pathlib import Path

import click
import numpy as np
from PIL import Image, UnidentifiedImageError

from . import __version__


logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.DEBUG
)

terminal_width = os.get_terminal_size().columns

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
    "--char-aspect", default=0.5, show_default=True,
    help="Character width/height ratio (default: 0.5 for 1:2 aspect)."
)
def main(file, char_aspect):
    try:
        img = Image.open(file)
    except UnidentifiedImageError:
        logging.critical(f"Unsupported or unreadable image format for file: {file}.")
        sys.exit(1)
    arr = np.array(img)
    height, width = arr.shape[:2]
    logging.info(f"Image is {width}x{height} pixels.")