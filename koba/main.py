# TODO: video support

import sys
import time
import logging

import click
import itertools
import multiprocessing
import concurrent.futures
import collections
from PIL import Image, ImageSequence, UnidentifiedImageError
from moviepy import VideoFileClip
from tqdm import tqdm
from rich.console import Console
from rich.text import Text

from koba import __version__
from koba.core import core

try:
    multiprocessing.set_start_method("spawn")
except RuntimeError:
    pass

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
    "--char-aspect", default=2.0, show_default=True,
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
    help="Inverts the image for processing (Color will not be inverted when using --color)."
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
    help="Enables color and uses â–ˆ (U+2588) to improve processing speed. Only recommended for animated pictures."
)
def main(file, char_aspect, logging_level, save_blocks, save_chars, engine, font, char_range, stretch_contrast, scale, invert, single_threaded, color, fast_color):
    console = Console()
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
    
    media_type = None
    
    # loading file and reading basic info
    try:
        img = Image.open(file)
        frame_count = getattr(img, 'n_frames', 1)
        if frame_count == 1:
            media_type = "image"
        else:
            media_type = "gif"
        frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
    except UnidentifiedImageError:
        try:
            clip = VideoFileClip(file)
            frame_count = int(clip.fps * clip.duration)
            frames = (Image.fromarray(f) for f in clip.iter_frames())
            if frame_count > 1:
                media_type = "video"
            else:
                media_type = "image"
        except Exception as e:
            logging.critical(f"Unsupported or unreadable image/video format for file: {file}. Error: {e}")
            sys.exit(1)
    else:
        if not frames:
            logging.critical(f"No frames found in image file: {file}.")
            sys.exit(1)
    
    logging.info(f"Image has {frame_count} frame(s).")
    is_animated = frame_count > 1

    executor = None
    block_cache = collections.OrderedDict()
    characters = None

    try:
        if is_animated:
            from koba.core import unify, charsets
            logging.info("Pre-rendering characters...")
            if isinstance(frames, list):
                first_frame = frames[0]
            else:
                first_frame = next(frames)
                frames = itertools.chain([first_frame], frames)
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

            if not single_threaded:
                from koba.core.core import init_worker
                executor = concurrent.futures.ProcessPoolExecutor(initializer=init_worker, initargs=(characters,))

        frame_delays = []
        all_frames = []
        
        # Pass characters for single-threaded animated case
        chars_for_process = characters if (is_animated and single_threaded) else None

        for i, frame in tqdm(enumerate(frames), total=frame_count, desc="Processing frames", disable=not is_animated):
            all_frames.append(core.process(
                frame, char_aspect, scale, engine, color, invert, stretch_contrast,
                save_blocks, start_char, end_char, save_chars, font, 
                single_threaded=single_threaded, 
                show_progress=not is_animated,
                executor=executor,
                block_cache=block_cache,
                characters=chars_for_process
            ))
            delay = 0
            if media_type == "gif":
                delay = frame.info.get("duration", 100) / 1000
            elif media_type == "video":
                delay = 1 / clip.fps
            elif media_type == "image":
                delay = 0.1
            
            if not delay or delay == 0:
                delay = 0.1
            frame_delays.append(delay)

    finally:
        if executor:
            executor.shutdown()

    logging.debug(f"Frame delays: {frame_delays[:3]} ...")

    if media_type == "video":
        input("Press [Enter] to start playback: ")

    prev_lines = 0
    if is_animated:
        while True:
            for frame, delay in zip(all_frames, frame_delays):
                start = time.time()
                lines = frame.count('\n')
                if prev_lines > 0:
                    sys.stdout.write(f"\r\033[{prev_lines}A")
                    sys.stdout.write("\033[J")
                print(frame, end="")
                sys.stdout.flush()
                prev_lines = lines
                elapsed = time.time() - start
                sleep_time = max(0, delay - elapsed)
                time.sleep(sleep_time)
                
            if media_type == "video":
                try:
                    input("\nPress [Enter] to replay, or Ctrl+C to quit: ")
                    sys.stdout.write(f"\r\033[{prev_lines}A")
                    sys.stdout.write("\033[J")
                    sys.stdout.flush()
                except KeyboardInterrupt:
                    print("\nExiting.")
                    break
    else:
        frame = all_frames[0]
        if color:
            console.print(Text.from_ansi(frame))
        else:
            print(frame)