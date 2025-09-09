def get_amount(amount):
    chars = []
    i = 32 # first printable ascii
    while len(chars) < amount and i <= 0x10FFFF:
        c = chr(i)
        if c.isprintable() and c.strip():
            chars.append(c)
        i += 1
    return chars

def get_range(start, end):
    chars = []
    for i in range(start, end + 1): # ascii is 32 - 126
        char = chr(i)
        if char.isprintable() and char.strip():
            chars.append(char)
            
    return chars