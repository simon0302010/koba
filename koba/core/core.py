import os
import sys
import math
import logging
import concurrent.futures

import numpy as np
from tqdm import tqdm
from PIL import Image, ImageOps

from koba.core import charsets, unify

def init_worker(characters_for_worker):
    """Initializer for each worker process."""
    unify.set_worker_characters(characters_for_worker)

def chunk_list(data, n):
    """Splits a list into n roughly equal chunks."""
    if n <= 0:
        return [data]
    k, m = divmod(len(data), n)
    return [data[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n)]

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

def process(
    img, char_aspect, scale, engine, color, invert, stretch_contrast, 
    save_blocks, start_char, end_char, save_chars, font, 
    single_threaded, show_progress=False, 
    executor=None, block_cache=None, characters=None
):
    if color:
        img_color = img.convert("RGB")
        img_arr_color = np.array(img_color)
    
    img = img.convert("L")
    if invert:
        img = ImageOps.invert(img)
    if stretch_contrast:
        img = ImageOps.autocontrast(img)
    
    img_arr = np.array(img)
    height, width = img_arr.shape[:2]
    logging.debug(f"Image is {width}x{height} pixels.")
    
    block_widths, block_heights, chars_width = calculate_block_sizes(width, height, char_aspect, scale)

    logging.debug(f"Image will be {chars_width}x{len(block_heights)} chars.")

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
            blocks.append(block)
            x += bw
        y += bh
    
    if color:
        y = 0
        for bh in block_heights:
            x = 0
            for bw in block_widths:
                block = img_arr_color[y:y+bh, x:x+bw]
                block_color = block.mean(axis=(0, 1)).astype(int)            
                block_colors.append(block_color)
                x += bw
            y += bh
    
    if save_blocks:
        os.makedirs("blocks", exist_ok=True)
        for idx, block in enumerate(blocks):
            Image.fromarray(block).save(os.path.join("blocks", f"{idx:04d}.png"))
    
    print_chars = ""
    
    if start_char == end_char:
        all_chars = chr(start_char) * len(blocks)
    else:
        frame_results_map = {}
        unique_blocks_map = {block.tobytes(): block for block in blocks}

        if block_cache is not None:
            blocks_to_process = []
            for key, block in unique_blocks_map.items():
                if key in block_cache:
                    frame_results_map[key] = block_cache[key]
                    block_cache.move_to_end(key)
                else:
                    blocks_to_process.append(block)
        else:
            blocks_to_process = list(unique_blocks_map.values())
        
        if blocks_to_process:
            new_results = {}
            if not single_threaded and executor:
                n_workers = executor._max_workers
                if not n_workers or n_workers <= 0: n_workers = 1
                block_chunks = chunk_list(blocks_to_process, n_workers)
                chunk_args = [(chunk, engine.lower(), save_chars) for chunk in block_chunks if chunk]
                futures = [executor.submit(unify.process_blocks_batch, *arg) for arg in chunk_args]
                for future in concurrent.futures.as_completed(futures):
                    new_results.update(future.result())
            else:
                if characters is None:
                    characters = charsets.get_range(start_char, end_char)
                init_worker(characters)
                for block in tqdm(blocks_to_process, desc="Processing unique blocks", disable=not show_progress):
                    new_results[block.tobytes()] = unify.get_character(block, engine.lower(), save_chars)

            if block_cache is not None:
                block_cache.update(new_results)
                while len(block_cache) > 1000000:
                    block_cache.popitem(last=False)
            frame_results_map.update(new_results)

        results = [frame_results_map.get(block.tobytes()) for block in blocks]
        all_chars = "".join(filter(None, results))
    
    lines = [all_chars[i:i+chars_width] for i in range(0, len(all_chars), chars_width)]

    if not color:
        return "\n".join(lines)

    # Apply colors
    print_chars = ""
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