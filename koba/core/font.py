import matplotlib.font_manager as fm
from fontTools.ttLib import TTFont

# cache for font paths and codepoints
_font_paths = None
_font_codepoints = {}

def get_all_font_paths():
    global _font_paths
    if _font_paths is None:
        _font_paths = [f.fname for f in fm.fontManager.ttflist]
    return _font_paths

def get_monospace_font():
    for font in fm.fontManager.ttflist:
        if "dejavusansmono" in font.name.replace(" ", "").lower():
            return font.fname
    return None

def get_supported_font(char):
    codepoint = ord(char)
    for font_path in get_all_font_paths():
        if font_supports_codepoint(font_path, codepoint):
            return font_path
    return False

def font_supports_codepoint(font_path, codepoint):
    if font_path not in _font_codepoints:
        try:
            font = TTFont(font_path)
            cps = set()
            for cmap in font['cmap'].tables:
                if cmap.isUnicode():
                    cps.update(cmap.cmap.keys())
            _font_codepoints[font_path] = cps
        except Exception:
            _font_codepoints[font_path] = set()
    return codepoint in _font_codepoints[font_path]

def check_support(char, font_path):
    return font_supports_codepoint(font_path, ord(char))