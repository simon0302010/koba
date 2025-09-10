from PIL import ImageFont, ImageDraw, Image
from skimage.metrics import structural_similarity as ssim
import numpy as np
import logging
import os

from . import font


SAVE_CHARS = True
FONT_SIZE = 48

font_path = font.get_monospace_font()
font_cache = {}
char_cache = {}

def get_font(font_path, size):
    key = (font_path, size)
    if key not in font_cache:
        font_cache[key] = ImageFont.truetype(font_path, size)
    return font_cache[key]

# from UCYT5040/lectrick
def crop_image(image):
    image_array = np.array(image)
    non_white_mask = image_array < 255
    non_white_pixels = np.argwhere(non_white_mask)
    if non_white_pixels.size == 0:
        return image
    top, left = non_white_pixels.min(axis=0)
    bottom, right = non_white_pixels.max(axis=0) + 1  # +1 to include the last pixel
    return image.crop((left, top, right, bottom))

def get_char(char, width, height, save=False):
    char_arr = char_cache.get(char)
    if char_arr is not None:
        return char_arr
    else:
        font = get_font(font_path, FONT_SIZE)
        bbox = font.getbbox(char)
        
        if not (bbox and bbox[2] > bbox[0] and bbox[3] > bbox[1]):
            return None
        
        char_width, char_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        char_image = Image.new('L', (char_width, char_height), 255)
        draw = ImageDraw.Draw(char_image)
        draw.text((-bbox[0], -bbox[1]), char, font=font, fill=0)
                
        char_image = crop_image(char_image)
        
        char_image = char_image.resize((width, height), Image.Resampling.LANCZOS)
        
        if save:
            os.makedirs("blocks", exist_ok=True)
            char_code = ord(char)
            char_image.save(f"blocks/char_{char_code}.png")
        
        char_arr = np.array(char_image)
            
        char_cache[char] = char_arr
        return char_arr

# TODO: better comparison algorithm
def compare_character(char, block_arr, use_brightness=False):
    height, width = block_arr.shape
    
    char_arr = get_char(char, width, height, save=SAVE_CHARS)
    if char_arr is None:
        return 0.0
    
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
        similarity = compare_character(character, img_arr, use_brightness=True)
        if similarity > max_similarity:
            max_similarity = similarity
            best_match = character
            
    return best_match