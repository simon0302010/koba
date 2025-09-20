from PIL import ImageFont, ImageDraw, Image
import numpy as np
import logging
import os
from . import font

FONT_SIZE = 20
font_path = font.get_monospace_font()
font_cache = {}
char_cache = {}


def get_font(char):
    if char not in font_cache.keys():
        if font_path and font.check_support(char, font_path):
            font_cache[char] = ImageFont.truetype(font_path, FONT_SIZE)
        else:
            new_font = font.get_supported_font(char)
            if new_font:
                logging.debug(f"Found font that supports {char}.")
                font_cache[char] = ImageFont.truetype(new_font, FONT_SIZE)
            else:
                return None
    return font_cache[char]

# from UCYT5040/lectrick
def crop_image(image):
    image_array = np.array(image)
    non_white_mask = image_array < 0
    non_white_pixels = np.argwhere(non_white_mask)
    if non_white_pixels.size == 0:
        return image
    top, left = non_white_pixels.min(axis=0)
    bottom, right = non_white_pixels.max(axis=0) + 1  # +1 to include the last pixel
    return image.crop((left, top, right, bottom))

def get_char(char, width, height, save=False):
    char_arr = char_cache.get((char, width, height))
    if char_arr is not None:
        return char_arr
    else:
        font = get_font(char)
        if not font:
            logging.critical("Some chars are not supported by any of your installed fonts. Please specify a custom font with the --font option.")
            raise FileNotFoundError
        bbox = font.getbbox(char)
        
        if not (bbox and bbox[2] > bbox[0] and bbox[3] > bbox[1]):
            return None
        
        char_width, char_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        char_image = Image.new('L', (char_width, char_height), 0)
        draw = ImageDraw.Draw(char_image)
        draw.text((-bbox[0], -bbox[1]), char, font=font, fill=255)
                
        char_image = crop_image(char_image)
        
        char_image = char_image.resize((width, height), Image.Resampling.BILINEAR)
        
        if save:
            os.makedirs("chars", exist_ok=True)
            char_code = ord(char)
            char_image.save(f"chars/{char_code}.png")
        
        char_arr = np.array(char_image)
            
        char_cache[(char, width, height)] = char_arr
        return char_arr

def pre_render_characters(characters, sizes, save_chars, progress_callback=None):
    for size in sizes:
        width, height = size
        for char in characters:
            get_char(char, width, height, save_chars)
            if progress_callback:
                progress_callback()