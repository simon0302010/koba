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

from koba import __version__
from koba.core import charsets, unify

def process_block(args):
    block, characters, engine, save_chars = args
    return unify.get_character(block, characters, save_chars, engine)

def calculate_block_sizes(width, height, char_aspect, scale):
    terminal_width = os.get_terminal_size().columns
    chars_width = terminal_width
    
    min_block_width = 10 / char_aspect
    min_block_height = 10

    scale = min(scale, 1.0)
    
    max_chars_width_by_block_width = int(width // min_block_width)
    max_chars_width_by_block_height = int(height // min_block_height * char_aspect)

    max_chars_width = min(max_chars_width_by_block_width, max_chars_width_by_block_height)

    chars_width = min(int(terminal_width * scale), terminal_width, max_chars_width)

    chars_width = max(chars_width, 1)

    chars_height = math.ceil((height * chars_width / width) / char_aspect)
    
    block_widths = [width // chars_width] * chars_width
    for i in range(width % chars_width):
        block_widths[i] += 1

    block_heights = [height // chars_height] * chars_height
    for i in range(height % chars_height):
        block_heights[i] += 1
        
    return block_widths, block_heights, chars_width

def process(img, char_aspect, scale, engine, color, invert, stretch_contrast, save_blocks, start_char, end_char, save_chars, font, single_threaded, show_progress=False):
    img_arr = np.array(img)
    height, width = img_arr.shape[:2]
    logging.debug(f"Image is {width}x{height} pixels.")
    
    block_widths, block_heights, chars_width = calculate_block_sizes(width, height, char_aspect, scale)

    logging.debug(f"Image will be {chars_width}x{len(block_heights)} chars.")
    logging.debug(f"Block widths: {block_widths[:5]}... (total {len(block_widths)})")
    logging.debug(f"Block heights: {block_heights[:5]}... (total {len(block_heights)})")

    if min(block_heights + block_widths) <= 7 and str(engine).lower() == "ssim":
        logging.critical("Image blocks are too small for SSIM. Please use another engine.")
        sys.exit(1)

    # splitting into blocks with variable sizes
    block_colors = []
    blocks = []
    y = 0
    for bh in block_heights:
        x = 0
        for bw in block_widths:
            block = img_arr[y:y+bh, x:x+bw]
            if block.ndim == 3: # check if block is rgb
                if color:
                    block_color = block.mean(axis=(0, 1)).astype(int)
                    block_colors.append(block_color)
                    
                    block = Image.fromarray(block).convert("L")
                    if invert:
                        block = ImageOps.invert(block)
                    if stretch_contrast:
                        block = ImageOps.autocontrast(block)
                    block = np.array(block)
                else:
                    logging.warning("Block has color but --color wasn't used.")
                    block = Image.fromarray(block).convert("L")
                    block = np.array(block)
                
            blocks.append(block)
            x += bw
        y += bh
        
    if color:
        if len(block_colors) != len(blocks):
            logging.critical("Block colors don't match the blocks. Falling back to grayscale.")
            color = False
        else:
            logging.debug(f"Block colors: {block_colors[:3]} ...")
    
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
    unique_blocks = {block.tobytes(): block for block in blocks}
    unique_block_args = [(block, characters, engine.lower(), save_chars) for block in unique_blocks.values()]

    if font:
        unify.font_path = font

    block_results = {}
    if not single_threaded:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_block = {
                executor.submit(unify.get_character, *arg): arg[0] for arg in unique_block_args
            }
            try:
                for future in tqdm(
                    concurrent.futures.as_completed(future_to_block),
                    total=len(future_to_block),
                    desc="Processing unique blocks",
                    disable=not show_progress
                ):
                    block = future_to_block[future]
                    block_results[block.tobytes()] = future.result()
            except ValueError as e:
                logging.critical(str(e))
                sys.exit(1)
    else:
        for args in tqdm(
            unique_block_args,
            desc="Processing unique blocks (single-threaded)",
            disable=not show_progress
        ):
            block, characters, engine, save_chars = args
            result = unify.get_character(block, characters, save_chars, engine)
            block_results[block.tobytes()] = result

    results = [block_results[block.tobytes()] for block in blocks]

    print_chars = ""
    all_chars = "".join(results)
    lines = [all_chars[i:i+chars_width] for i in range(0, len(all_chars), chars_width)]
    flat_chars = "".join(lines)
    logging.debug(f"Char count: {len(flat_chars)}")
    logging.debug(f"Colored blocks: {len(block_colors)}")

    color_idx = 0
    for c in '\n'.join(lines):
        if c == '\n':
            print_chars += '\n'
        elif color_idx < len(block_colors):
            r, g, b = block_colors[color_idx]
            print_chars += f"\033[38;2;{r};{g};{b}m{c}\033[0m"
            color_idx += 1
        else:
            print_chars += c
            
    return print_chars
