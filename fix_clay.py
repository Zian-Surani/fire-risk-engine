import os
import re

directories = ['c:/Users/zians/Downloads/FIRE/frontend/src/app/(dashboard)']

bg_patterns = [r'bg-\[#151b22\]/?\d*', r'bg-\[#1f2730\]/?\d*', r'bg-\[#171c21\]/?\d*', r'bg-\[#1b2025\]/?\d*']
border_patterns = [r'border border-white/5', r'border border-outline-variant/10', r'border border-\[#534435\]/15', r'border-t border-white/\[0\.05\]']

def replace_classes(content):
    # For every background pattern, replace it with clay-panel clay-interactive
    for bg in bg_patterns:
        # Match className="..."
        content = re.sub(rf'(className="[^"]*){bg}([^"]*")', r'\1clay-panel clay-interactive\2', content)
        
    for border in border_patterns:
        content = re.sub(border, '', content)
        
    # Let's also enforce rounded-3xl for plush look
    content = re.sub(r'rounded-2xl', 'rounded-3xl', content)
    content = re.sub(r'rounded-\[16px\]', 'rounded-3xl', content)
    content = re.sub(r'rounded-xl', 'rounded-2xl', content)
    return content

for root, _, files in os.walk(directories[0]):
    for file in files:
        if file.endswith('.tsx') and file != 'layout.tsx':
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = replace_classes(content)
            
            # Additional spaces cleanup
            new_content = re.sub(r' +', ' ', new_content)
            new_content = new_content.replace('className=" ', 'className="')
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {file}")
