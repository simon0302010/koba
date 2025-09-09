from numpy import array as np_array
from PIL import ImageFont, ImageDraw, Image
from skimage.metrics import structural_similarity as ssim
import logging

from . import font, charsets


font_path = font.get_monospace_font()

def compare_character(char, block_arr):
    height, width = block_arr.shape

    # find largest fitting font size
    min_size = 1
    max_size = min(width, height) * 4
    best_size = min_size
    while min_size <= max_size:
        mid = (min_size + max_size) // 2
        font = ImageFont.truetype(font_path, mid)
        bbox = font.getbbox(char)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w <= width and h <= height:
            best_size = mid
            min_size = mid + 1
        else:
            max_size = mid - 1

    # render at best size
    font = ImageFont.truetype(font_path, best_size)
    img = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(img)
    bbox = font.getbbox(char)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # center
    x = (width - w) // 2 - bbox[0]
    y = (height - h) // 2 - bbox[1]
    draw.text((x, y), char, font=font, fill=0)
    
    char_arr = np_array(img)
    
    if char_arr.shape != block_arr.shape:
        img = img.resize((block_arr.shape[1], block_arr.shape[0]), Image.Resampling.LANCZOS)
        char_arr = np_array(img)
        
    img.show()
    
    try:
        score = ssim(block_arr, char_arr, data_range=255)
    except Exception as e:
        logging.critical(e)
        score = 0.0
        
    similarity = max(0.0, score)
    return similarity