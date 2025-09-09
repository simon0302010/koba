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

def get_fonts(preferred=False, monospace=False):
    fonts = []
    seen_names = set()
    font_list = fm.fontManager.ttflist

    for font in font_list:
        if font.name in seen_names:
            continue
        if preferred:
            if any(name.lower() in font.name.lower() for name in PREFERRED):
                fonts.append(font)
                seen_names.add(font.name)
        else:
            fonts.append(font)
            seen_names.add(font.name)

    return [font.fname for font in fonts]

def get_best_candidate(font_paths):
    style_rank = {
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
    
    # only monospace fonts that aren't italic
    candidates = [
        p for p in font_paths
        if "mono" in p.lower() and "italic" not in p.lower() and "propo" not in p.lower()
    ]
    
    # rank fonts
    def score(path):
        for style, rank in style_rank.items():
            if style.lower() in path.lower():
                return rank
        return 99

    best = min(candidates, key=score, default=None)
    return best

# very slow
def is_monospace(path, test_chars="ilMW"):
    font = ImageFont.truetype(path, 16)
    widths = [font.getsize(c)[0] for c in test_chars]
    return all(w == widths[0] for w in widths)

if __name__ == "__main__":
    font_paths = get_fonts(preferred=True)
    print(get_best_candidate(font_paths))