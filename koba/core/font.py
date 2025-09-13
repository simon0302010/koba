# will probably not be used but still kept

import matplotlib.font_manager as fm
from fontTools.ttLib import TTFont


# TODO: More efficient font loading

def get_monospace_font():
    # get dejavu sans mono path
    for font in fm.fontManager.ttflist:
        if "dejavusansmono" in font.name.replace(" ", "").lower():
            return font.fname
    return None
        
def get_supported_font(char):
    for font_path in fm.fontManager.ttflist:
        font = TTFont(font_path.fname)
        for cmap in font['cmap'].tables:
            if cmap.isUnicode():
                if ord(char) in cmap.cmap:
                    return font_path.fname
    return False

def check_support(char, font_path):
    font = TTFont(font_path)
    for cmap in font['cmap'].tables:
        if cmap.isUnicode():
            if ord(char) in cmap.cmap:
                return True
    return False