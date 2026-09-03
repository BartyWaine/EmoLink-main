import glob
import os

for f in glob.glob('../public/*.php'):
    content = open(f, 'r', encoding='utf-8').read()
    if 'theme.js' not in content:
        content = content.replace('<link rel="stylesheet" href="assets/style.css">', '<script src="assets/theme.js"></script>\n    <link rel="stylesheet" href="assets/style.css">')
        open(f, 'w', encoding='utf-8').write(content)
        print(f"Updated {f}")
