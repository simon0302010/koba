import numpy as np
from PIL import Image

def build_img(char_arrays, block_widths, block_heights):
    out_height = sum(block_heights)
    out_width = sum(block_widths)
    out_img = np.zeros((out_height, out_width), dtype=np.uint8)

    idx = 0
    y = 0
    for bh in block_heights:
        x = 0
        for bw in block_widths:
            char_arr = char_arrays[idx]
            # resize
            if char_arr.shape != (bh, bw):
                char_arr = np.array(Image.fromarray(char_arr).resize((bw, bh), Image.LANCZOS))
            out_img[y:y+bh, x:x+bw] = char_arr
            x += bw
            idx += 1
        y += bh

    return out_img