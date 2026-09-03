import glob
import os

for f in glob.glob('../public/*.php'):
    content = open(f, 'r', encoding='utf-8').read()
    content = content.replace('href="assets/style.css"', 'href="assets/style.css?v=2"')
    content = content.replace('src="assets/theme.js"', 'src="assets/theme.js?v=2"')
    open(f, 'w', encoding='utf-8').write(content)
    print(f"Updated cache buster in {f}")
