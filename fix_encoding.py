import os

path = r"c:\anshika\college\GenCoder challenge\session 3 project\templates\index.html"

with open(path, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

# Each tuple: (garbled_string, clean_replacement)
fixes = [
    # Theme toggles
    ("\u00e2\u02c6\u0080\u00e2\u201e\u00a2\u00c2\u00b0 Light Mode", "Light Mode"),
    ("\u00c3\u00b0\u00c5\u00b8\u0152\u00c2\u2122 Dark Mode", "Dark Mode"),
    ("\u00c3\u00b0\u00c5\u00b8\u0152\u00c2\u2122", "Night"),
    # Voice/mic
    ("\u00c3\u00b0\u00c5\u00b8\u017d\u00a4", "Mic"),
    # Trash/clear
    ("\u00c3\u00b0\u00c5\u00b8\u2014\u2018\u00ef\u00bf\u00bd", "X"),
    # Ellipsis
    ("\u00e2\u20ac\u00a6", "..."),
    # Middle dot
    ("\u00c3\u0082\u00c2\u00b7", "-"),
    # Em dash
    ("\u00e2\u20ac\u201d", "-"),
    # Quiz icon
    ("\u00c3\u00b0\u00c5\u00b8\u201c Quiz Mode", "Quiz Mode"),
    ("\u00c3\u00b0\u00c5\u00b8\u201c Quiz Me!", "Quiz Me!"),
    ("\u00e2\u009a\u00a1", ""),
    ("\u00e2\u00b3 Generating quiz", "Generating quiz"),
    ("\u00c3\u00b0\u00c5\u00b8\u2019\u00a1", "Hint:"),
    # Sidebar labels
    ("\u00c3\u00b0\u00c5\u00b8\u201c\u00ca\u0160 TOKEN SAVINGS", "TOKEN SAVINGS"),
    ("\u00c3\u00b0\u00c5\u00b8\u201c\u2013 CHAPTER COVERAGE", "CHAPTER COVERAGE"),
    ("\u00c3\u00b0\u00c5\u00b8\u201c Quiz Me!", "Quiz Me!"),
    # Avatars
    ("\u00c3\u00b0\u00c5\u00b8\u00a4\u2013\u00e2\u20ac\u2039\u00c3\u00b0\u00c5\u00b8\u017d\u201c", "U"),
    ("\u00c3\u00b0\u00c5\u00b8\u00a4\u2013", "U"),
    ("\u00c3\u00b0\u00c5\u00b8\u00a4", "AI"),
    # Copy
    ("\u00e2\u009c\u201d Copied", "Copied!"),
    ("\u00c3\u00b0\u00c5\u00b8\u201c\u2039 Copy", "Copy"),
    ("\u00c3\u00b0\u00c5\u00b8\u201c\u2039", ""),
    # Source label
    ("\u00c3\u00b0\u00c5\u00b8\u201c\u2013 Sources", "Sources"),
    # Warning
    ("\u00e2\u009a\u00a0\u00ef\u00bf\u00bd", "Warning:"),
    # Dropdown arrow
    ("\u00e2\u2013\u00bc", "v"),
    # Book emoji in hero
    ("\u00c3\u00b0\u00c5\u00b8\u201c\u00da\u00b0", ""),
    # Chapter range
    ("1\u00e2\u20ac", "1-"),
    # Send separator
    ("send \u00c3\u0082\u00c2\u00b7", "send |"),
]

for old, new in fixes:
    if old in text:
        text = text.replace(old, new)
        print(f"Replaced: {repr(old[:30])} -> {repr(new)}")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Done.")
