import matplotlib.font_manager as fm
from PIL import ImageFont


PREFERRED = [
    "DejaVuSansMono",
    "LiberationMono",
    "CourierNew",
    "Menlo",
    "JetBrainsMono",
]

def get_fonts(preferred=False):
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

# very slow
def is_monospace(path, test_chars="ilMW"):
    font = ImageFont.truetype(path, 16)
    widths = [font.getsize(c)[0] for c in test_chars]
    return all(w == widths[0] for w in widths)

if __name__ == "__main__":
    print(get_fonts(preferred=True))