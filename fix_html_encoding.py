# Short targeted fix: collapse blank lines + clean CSS comment box-drawing entities
import re

f = open(r"C:\anshika\college\GenCoder challenge\session 3 project\templates\index.html", encoding="ascii", errors="replace")
text = f.read()
f.close()

# 1. Collapse 3+ consecutive blank lines -> 1 blank line
text = re.sub(r'(\r?\n)(\r?\n){2,}', r'\1\2', text)

# 2. Strip box-drawing char entities from CSS comments (&#9472; = unicode box char)
# They appear as: /* &#9472;&#9472;... SECTION ... &#9472;&#9472; */
# Replace the entity runs with plain dashes
text = re.sub(r'(?:&amp;#9472;|&#9472;)+', '-' * 20, text)

# 3. Fix remaining special char entities that show as text
fixes = {
    "&amp;mdash;": "&mdash;",
    "&amp;ndash;": "&ndash;",
    "&amp;rsaquo;": "&rsaquo;",
}
for bad, good in fixes.items():
    text = text.replace(bad, good)

# 4. English only
text = text.replace("Hindi questions work too!", "Try asking follow-up questions!")

f = open(r"C:\anshika\college\GenCoder challenge\session 3 project\templates\index.html", "w", encoding="ascii", newline="\r\n")
f.write(text)
f.close()

# Quick check
idx = text.find("hero-icon-inner")
if idx >= 0:
    print("hero-icon sample:", repr(text[idx:idx+80]))
print("Lines:", text.count("\n"), "Size:", len(text))
