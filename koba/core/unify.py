from PIL import Image
from skimage.metrics import structural_similarity as ssim
import numpy as np

from ._unify_shared import get_char, pre_render_characters, crop_image, get_font
from . import _unify_optim

WORKER_CHARACTERS = None

def set_worker_characters(characters):
    """Set the character list for the worker process."""
    global WORKER_CHARACTERS
    WORKER_CHARACTERS = characters

def compare_character(char, block_arr, save_chars, engine):
    if engine == "diff" or engine == "brightness":
        return _unify_optim.compare_character(char, block_arr, save_chars, engine)
    height, width = block_arr.shape
    
    char_arr = get_char(char, width, height, save=save_chars)
    if char_arr is None:
        return 0.0
    
    if char_arr.shape != block_arr.shape:
        char_img = Image.fromarray(char_arr)
        char_img = char_img.resize((width, height), Image.Resampling.BILINEAR)
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
            if isinstance(score, tuple):
                score = score[0]
            similarity = max(0.0, float(score))
        except ValueError:
            # This can happen if the window size is larger than the image
            similarity = 0.0
            
    elif engine == "diff":
        pixel_diff = np.sum(np.abs(block_arr.astype(np.int16) - char_arr.astype(np.int16)))
        max_diff = float(width * height * 255)
        if max_diff == 0:
            return 1.0
        dissimilarity = pixel_diff / max_diff
        similarity = 1.0 - dissimilarity
    elif engine == "mse":
        mse = np.mean((block_arr.astype(np.int32) - char_arr.astype(np.int32)) ** 2)
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
    
def get_character(img_arr, engine, save_chars):
    """
    Finds the best character to represent an image block,
    using the globally defined WORKER_CHARACTERS list.
    """
    max_similarity = float("-inf")
    best_match = " "

    if WORKER_CHARACTERS is None:
        raise ValueError("Worker characters have not been initialized.")

    for character in WORKER_CHARACTERS:
        similarity = compare_character(character, img_arr, save_chars, engine)
        if similarity > max_similarity:
            max_similarity = similarity
            best_match = character
    
    return best_match

def process_blocks_batch(blocks_batch, engine, save_chars):
    """Processes a batch of blocks and returns a result map."""
    results_map = {}
    for block in blocks_batch:
        results_map[block.tobytes()] = get_character(block, engine, save_chars)
    return results_map

