from PIL import ImageFont, ImageDraw, Image
from skimage.metrics import structural_similarity as ssim
import numpy as np
import logging

from . import font


font_path = font.get_monospace_font()
font_cache = {}
char_cache = {}

def get_font(font_path, size):
    key = (font_path, size)
    if key not in font_cache:
        font_cache[key] = ImageFont.truetype(font_path, size)
    return font_cache[key]

# TODO: fill whole canvas with char
def get_char(char, width, height):
    char_arr = char_cache.get(char)
    if char_arr is not None:
        return char_arr
    else:
        # find largest fitting font size
        min_size = 1
        max_size = min(width, height) * 4
        best_size = min_size
        while min_size <= max_size:
            mid = (min_size + max_size) // 2
            font = get_font(font_path, mid)
            bbox = font.getbbox(char)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if w <= width and h <= height:
                best_size = mid
                min_size = mid + 1
            else:
                max_size = mid - 1

        # render at best size
        font = get_font(font_path, best_size)
        img = Image.new("L", (width, height), color=255)
        draw = ImageDraw.Draw(img)
        bbox = font.getbbox(char)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        # center
        x = (width - w) // 2 - bbox[0]
        y = (height - h) // 2 - bbox[1]
        draw.text((x, y), char, font=font, fill=0)
        
        char_arr = np.array(img)
        
        if char_arr.shape != (height, width):
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            char_arr = np.array(img)
            
        char_cache[char] = char_arr
        return char_arr

# TODO: better comparison algorithm
def compare_character(char, block_arr, use_brightness=False):
    height, width = block_arr.shape
    
    char_arr = get_char(char, width, height)
    
    # compare arrays
    if use_brightness:
        score = 255.0
        try:
            avg_char = np.mean(char_arr)
            avg_block = np.mean(block_arr)
            score = abs(avg_char - avg_block)
        except Exception as e:
            logging.error(e)
        finally:
            similarity = 1.0 - (score / 255.0)
    else:
        score = 0.0
        try:
            min_side = min(block_arr.shape)
            win_size = min(7, min_side)
            if win_size % 2 == 0:
                win_size -= 1
            if win_size < 3:
                win_size = 3
            score = ssim(block_arr, char_arr, data_range=255, win_size=win_size)
        except Exception as e:
            logging.error(e)
            score = 0.0
        finally:
            if isinstance(score, tuple):
                score = score[0]
            try:
                similarity = max(0.0, float(score))
            except Exception:
                similarity = 0.0
        
    return similarity
    
# TODO: implement early stopping
def get_character(img_arr, characters):
    max_similarity = 0.0
    best_match = " "
    for character in characters:
        similarity = compare_character(character, img_arr)
        if similarity > max_similarity:
            max_similarity = similarity
            best_match = character
            
    return best_match