import numpy as np
cimport numpy as np
cimport cython

from PIL import Image
from koba.core.unify import get_char
from koba.core._unify_shared import get_char

@cython.boundscheck(False)
@cython.wraparound(False)
def compare_character(
    object char, 
    np.ndarray[np.uint8_t, ndim=2] block_arr, 
    object save_chars, 
    object engine
):
    cdef int height = block_arr.shape[0]
    cdef int width = block_arr.shape[1]
    cdef double similarity = 0.0
    cdef long pixel_diff
    cdef double max_diff
    cdef int x, y
    cdef double sum_char, sum_block, avg_char, avg_block, score

    char_arr_obj = get_char(char, width, height, save=save_chars)
    if char_arr_obj is None:
        return 0.0

    cdef np.ndarray[np.uint8_t, ndim=2] char_arr = char_arr_obj
    
    if engine == "diff":
        pixel_diff = 0
        for y in range(height):
            for x in range(width):
                pixel_diff += abs(block_arr[y, x] - char_arr[y, x])
        
        max_diff = <double>(width * height * 255)
        if max_diff == 0:
            return 1.0
        
        similarity = 1.0 - (pixel_diff / max_diff)

    elif engine == "brightness":
        sum_char = 0.0
        sum_block = 0.0
        for y in range(height):
            for x in range(width):
                sum_char += char_arr[y, x]
                sum_block += block_arr[y, x]
        avg_char = sum_char / (width * height)
        avg_block = sum_block / (width * height)
        score = abs(avg_char - avg_block)
        similarity = 1.0 - (score / 255.0)
        
    return similarity