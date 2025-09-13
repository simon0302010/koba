from PIL import ImageFont, ImageDraw, Image
from skimage.metrics import structural_similarity as ssim
import numpy as np
import logging
import sys
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
        
        char_image = char_image.resize((width, height), Image.Resampling.LANCZOS)
        
        if save:
            os.makedirs("chars", exist_ok=True)
            char_code = ord(char)
            char_image.save(f"chars/{char_code}.png")
        
        char_arr = np.array(char_image)
            
        char_cache[(char, width, height)] = char_arr
        return char_arr

def compare_character(char, block_arr, save_chars, engine):
    height, width = block_arr.shape
    
    char_arr = get_char(char, width, height, save=save_chars)
    if char_arr is None:
        return 0.0
    
    if char_arr.shape != block_arr.shape:
        char_img = Image.fromarray(char_arr)
        char_img = char_img.resize((width, height), Image.Resampling.LANCZOS)
        char_arr = np.array(char_img)
    
    # compare arrays
    if engine == "brightness":
        avg_char = np.mean(char_arr)
        avg_block = np.mean(block_arr)
        score = abs(avg_char - avg_block)
        similarity = 1.0 - (score / 255.0)
    elif engine == "ssim":
        min_side = min(block_arr.shape)
        win_size = min(7, min_side)
        if win_size % 2 == 0:
            win_size -= 1
        if win_size < 3:
            win_size = 3
        
        try:
            score = ssim(block_arr, char_arr, data_range=255, win_size=win_size)
            similarity = max(0.0, float(score))
        except ValueError:
            # This can happen if the window size is larger than the image
            similarity = 0.0
            
    elif engine == "diff":
        pixel_diff = np.sum(np.abs(block_arr.astype(np.float64) - char_arr.astype(np.float64)))
        max_diff = float(width * height * 255)
        if max_diff == 0:
            return 1.0
        dissimilarity = pixel_diff / max_diff
        similarity = 1.0 - dissimilarity
    elif engine == "mse":
        mse = np.mean((block_arr.astype(np.float64) - char_arr.astype(np.float64)) ** 2)
        max_mse = 255.0 ** 2
        similarity = 1.0 - (mse / max_mse) if max_mse > 0 else 1.0
    elif engine == "ncc":
        a = block_arr.astype(np.float64)
        b = char_arr.astype(np.float64)
        
        std_a = a.std()
        std_b = b.std()

        if std_a == 0 and std_b == 0:
            similarity = 1.0 if a.mean() == b.mean() else 0.0
        elif std_a == 0 or std_b == 0:
            similarity = 0.0
        else:
            a = (a - a.mean()) / std_a
            b = (b - b.mean()) / std_b
            ncc = np.mean(a * b)
            similarity = (ncc + 1) / 2
    elif engine == "hist":
        hist_a, _ = np.histogram(block_arr, bins=256, range=(0,255), density=True)
        hist_b, _ = np.histogram(char_arr, bins=256, range=(0,255), density=True)
        similarity = np.minimum(hist_a, hist_b).sum()
    elif engine == "cosine":
        a = block_arr.flatten().astype(np.float64)
        b = char_arr.flatten().astype(np.float64)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 and norm_b == 0: # Both are black
            similarity = 1.0
        elif norm_a == 0 or norm_b == 0: # One is black
            similarity = 0.0
        else:
            cos_sim = np.dot(a, b) / (norm_a * norm_b)
            similarity = (cos_sim + 1) / 2
    else:
        raise ValueError(f"Invalid engine specified: {engine}")
        
    return similarity
    
def get_character(img_arr, characters, engine, save_chars):
    max_similarity = float("-inf")
    best_match = " "
    for character in characters:
        similarity = compare_character(character, img_arr, engine, save_chars)
        if similarity > max_similarity:
            max_similarity = similarity
            best_match = character
    
    return best_match