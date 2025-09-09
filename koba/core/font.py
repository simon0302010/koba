# will probably not be used but still kept

import matplotlib.font_manager as fm
from PIL import ImageFont


PREFERRED = [
    "DejaVuSansMono",
    "LiberationMono",
    "CourierNew",
    "Menlo",
    "JetBrainsMono",
    "Consolas",
    "Cascadia"
]

STYLE_RANK = {
    "Regular": 0,
    "Book": 1,
    "Normal": 2,
    "Medium": 3,
    "SemiBold": 4,
    "Bold": 5,
    "ExtraBold": 6,
    "Light": 7,
    "ExtraLight": 8,
    "Thin": 9,
}

def get_fonts(preferred=False):
    fonts = []
    seen_names = set()
    font_list = fm.fontManager.ttflist

    for font in font_list:
        if font.name in seen_names:
            continue
        if preferred:
            if any(name.lower() in font.name.lower() for name in PREFERRED) or any(name.lower() in font.fname.lower() for name in PREFERRED):
                fonts.append(font)
                seen_names.add(font.name)
        else:
            fonts.append(font)
            seen_names.add(font.name)

    return [font.fname for font in fonts]

def get_best_candidate(font_paths):    
    # only monospace fonts that aren't italic
    candidates = [
        p for p in font_paths
        if "mono" in p.lower() and "italic" not in p.lower() and "propo" not in p.lower()
    ]
    
    # rank fonts
    def score(path):
        for style, rank in STYLE_RANK.items():
            if style.lower() in path.lower():
                return rank
        return 99

    best = min(candidates, key=score, default=None)
    return best

# very slow, will prob not use
def is_monospace(path, test_chars="ilMW"):
    font = ImageFont.truetype(path, 16)
    widths = [font.getsize(c)[0] for c in test_chars]
    return all(w == widths[0] for w in widths)

def get_monospace_font():
    # get dejavu sans mono path
    for font in fm.fontManager.ttflist:
        if "dejavusansmono" in font.name.replace(" ", "").lower():
            return font.fname

# results are weird
def get_font_aspect(font_path):
    font = ImageFont.truetype(font_path, 16)
    width, height = font.getsize("0")
    return height / width