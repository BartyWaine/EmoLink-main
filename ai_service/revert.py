import glob
import os

# 1. Remove script from all PHP files
for f in glob.glob('../public/*.php'):
    content = open(f, 'r', encoding='utf-8').read()
    content = content.replace('<script src="assets/theme.js"></script>\n    ', '')
    content = content.replace('<script src="assets/theme.js?v=2"></script>\n    ', '')
    content = content.replace('?v=2', '') # remove cache busters just in case
    open(f, 'w', encoding='utf-8').write(content)
    print(f"Reverted PHP file {f}")

# 2. Remove theme UI from dashboard.php
dash_path = '../public/dashboard.php'
dash_content = open(dash_path, 'r', encoding='utf-8').read()
ui_start = '<div style="display: flex; gap: 1rem; align-items: center;">'
ui_end = '</div>\n        </div>'
if ui_start in dash_content:
    # Need to replace the whole block back to the simple logout button
    import re
    dash_content = re.sub(
        r'<div style="display: flex; gap: 1rem; align-items: center;">.*?<a href="logout.php" class="btn btn-outline" style="width: auto; padding: 0.5rem 1rem;">Log Out</a>\s*</div>',
        '<a href="logout.php" class="btn btn-outline" style="width: auto;">Log Out</a>',
        dash_content,
        flags=re.DOTALL
    )
    open(dash_path, 'w', encoding='utf-8').write(dash_content)
    print("Reverted UI in dashboard.php")

# 3. Clean up CSS
css_path = '../public/assets/style.css'
css_content = open(css_path, 'r', encoding='utf-8').read()
# Just remove the [data-theme="dark"] block
import re
css_content = re.sub(r'\[data-theme="dark"\]\s*{[^}]*}', '', css_content)
open(css_path, 'w', encoding='utf-8').write(css_content)
print("Reverted style.css")
