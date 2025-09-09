import random
from PIL import Image, ImageDraw, ImageFont

def get_best_font_size(char, font_path, canvas_width, canvas_height, min_size=1, max_size=200):
    best_size = min_size
    while min_size <= max_size:
        mid = (min_size + max_size) // 2
        font = ImageFont.truetype(font_path, mid)
        bbox = font.getbbox(char)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w <= canvas_width and h <= canvas_height:
            best_size = mid
            min_size = mid + 1
        else:
            max_size = mid - 1
    return best_size

# Example parameters
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
canvas_width, canvas_height = 32, 32

# Get 100 random printable ASCII characters
characters = [chr(i) for i in range(32, 127)]
sample_size = min(100, len(characters))
random_chars = random.sample(characters, sample_size)

for char in characters:
    best_size = get_best_font_size(char, font_path, canvas_width, canvas_height)
    print(f"'{char}': {best_size}")