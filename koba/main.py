# TODO: video support

import sys
import time
import logging

import click
from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError
from tqdm import tqdm

from koba import __version__
from koba.core import core


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
@click.option(
    "--single-threaded",
    is_flag=True,
    help="Runs the whole program single-threaded."
)
@click.option(
    "--color",
    is_flag=True,
    help="Renders the image in color."
)
@click.option(
    "--fast-color",
    is_flag=True,
    help="Enables color and uses █ (U+2588) to improve processing speed. Only recommended for animated pictures."
)
def main(file, char_aspect, logging_level, save_blocks, save_chars, engine, font, char_range, stretch_contrast, scale, invert, single_threaded, color, fast_color):
    # update logging level
    logging.getLogger().setLevel(getattr(logging, logging_level.upper(), logging.ERROR))
    
    if fast_color:
        color = True
        char_range = "9608-9608"
    
    if font and not font.endswith(".ttf"):
        logging.critical("Please provide a font in TTF format.")
        sys.exit(1)

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
        img = Image.open(file)
    except UnidentifiedImageError:
        logging.critical(f"Unsupported or unreadable image format for file: {file}.")
        sys.exit(1)
    
    frame_count = getattr(img, 'n_frames', 1)
    logging.info(f"Image has {frame_count} frame(s).")
    is_gif = frame_count > 1

    if is_gif:
        from koba.core import unify, charsets
        logging.info("Pre-rendering characters for GIF...")
        first_frame = next(ImageSequence.Iterator(img))
        width, height = first_frame.size
        block_widths, block_heights, _ = core.calculate_block_sizes(width, height, char_aspect, scale)
        unique_shapes = {(w, h) for w in set(block_widths) for h in set(block_heights)}
        
        characters = charsets.get_range(start_char, end_char)
        
        if font:
            unify.font_path = font
        
        if abs(start_char - end_char) >= 400:
            for char in tqdm(characters, total=len(characters), desc="Loading fonts"):
                unify.get_font(char)

        with tqdm(total=len(unique_shapes) * len(characters), desc="Pre-rendering characters", disable=logging_level != "DEBUG") as pbar:
            unify.pre_render_characters(characters, unique_shapes, save_chars, pbar.update)
    
    frame_delays = []
    all_frames = []
    for i, frame in tqdm(enumerate(ImageSequence.Iterator(img)), total=frame_count, desc="Processing frames", disable=not is_gif):
        if color:
            frame = frame.convert("RGB")
        else:
            frame = frame.convert("L")
            if invert:
                frame = ImageOps.invert(frame)
            if stretch_contrast:
                frame = ImageOps.autocontrast(frame)
        all_frames.append(core.process(
            frame, char_aspect, scale, engine, color, invert, stretch_contrast,
            save_blocks, start_char, end_char, save_chars, font, single_threaded, show_progress=not is_gif
        ))
        
        delay = frame.info.get("duration", 100)
        if not delay or delay == 0:
            delay = 100      
        frame_delays.append(delay / 1000.0)

    logging.debug(f"Frame delays: {frame_delays[:3]} ...")

    prev_lines = 0
    if is_gif:
        while True:
            for frame, delay in zip(all_frames, frame_delays):
                lines = frame.count('\n')
                if prev_lines > 0:
                    sys.stdout.write(f"\r\033[{prev_lines}A")
                    sys.stdout.write("\033[J")
                print(frame, end="")
                sys.stdout.flush()
                prev_lines = lines
                time.sleep(delay)
    else:
        print(all_frames[0])
