import os
import re

directories = ['c:/Users/zians/Downloads/FIRE/frontend/src/app/(dashboard)']

def remove_icons(content):
    # Regex to match the section with Calendar, Bell, and UserCircle buttons.
    # We will match from `<div className="flex items-center gap-4 text-slate-400">`
    # down to the closing `</div>\n</div>\n</header>` and replace it with just closing divs.
    
    pattern = r'<div className="flex items-center gap-4 text-slate-400">.*?(<UserCircle[^>]*>|user_circle).*?</div>\s*</div>\s*</header>'
    
    # Actually it's easier to just match:
    # <div className="flex items-center gap-4 text-slate-400">...</div>
    
    pattern2 = re.compile(
        r'<div className="flex items-center gap-4 text-slate-400">\s*'
        r'<button[^>]*>.*?Calendar.*?</button>\s*'
        r'<button[^>]*>.*?Bell.*?</button>\s*'
        r'<button[^>]*>.*?UserCircle.*?</button>\s*'
        r'</div>',
        re.DOTALL
    )
    
    # Check if there are other variants (since some were converted directly from HTML with spans)
    pattern3 = re.compile(
        r'<div className="flex items-center gap-4 text-slate-400">\s*'
        r'<button[^>]*>.*?calendar_today.*?</button>\s*'
        r'<button[^>]*>.*?notifications.*?</button>\s*'
        r'<button[^>]*>.*?account_circle.*?</button>\s*'
        r'</div>',
        re.DOTALL
    )

    new_content = re.sub(pattern2, '', content)
    new_content = re.sub(pattern3, '', new_content)
    return new_content

for root, _, files in os.walk(directories[0]):
    for file in files:
        if file.endswith('.tsx') and file != 'layout.tsx':
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = remove_icons(content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Removed icons from {file}")
