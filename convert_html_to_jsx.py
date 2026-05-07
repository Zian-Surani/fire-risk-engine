import re
from bs4 import BeautifulSoup

def html_to_jsx(html_str):
    # Convert classes
    html_str = html_str.replace('class="', 'className="')
    # Close specific tags
    for tag in ['img', 'input', 'hr', 'br', 'source']:
        # Find standard tags without closing and add />
        html_str = re.sub(f'<{tag}(.*?)(?<!/)>', f'<{tag}\\1 />', html_str)
    # Convert inline styles if any exist (naively)
    # We will just strip style="clip-path..." for now and use Tailwind arbitrarily if needed, 
    # but let's try to convert simple styles
    styles = re.findall(r'style="([^"]*)"', html_str)
    for style in styles:
        parts = style.split(';')
        jsx_style = "{" + ", ".join([f"'{k.strip()}': '{v.strip()}'" for part in parts if part.strip() for k, v in [part.split(':', 1)]]) + "}"
        html_str = html_str.replace(f'style="{style}"', f'style={{{jsx_style}}}')
        
    # Convert specific attributes
    html_str = html_str.replace('tabindex=', 'tabIndex=')
    html_str = html_str.replace('viewbox=', 'viewBox=')
    html_str = html_str.replace('stroke-width=', 'strokeWidth=')
    html_str = html_str.replace('stroke-linecap=', 'strokeLinecap=')
    html_str = html_str.replace('stroke-linejoin=', 'strokeLinejoin=')
    html_str = html_str.replace('fill-rule=', 'fillRule=')
    html_str = html_str.replace('clip-rule=', 'clipRule=')
    # material icons span to lucide translation logic could go here, but I'll use standard lucide imports.
    
    return html_str

def process_file(in_filename, out_filename, page_name):
    with open(in_filename, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')
        
    header = soup.find('header')
    main = soup.find('main')
    
    if not main:
        print(f"Skipping {in_filename}, no main tag")
        return
        
    # Replace header classes to not be fixed, since layout.tsx handles it.
    if header:
        header_classes = header.get('class', [])
        # Remove 'fixed' and absolute positioning
        header_classes = [c for c in header_classes if c not in ['fixed', 'top-0', 'right-0', 'w-full', 'ml-20', 'md:ml-64', 'max-w-[calc(100%-5rem)]', 'md:max-w-[calc(100%-16rem)]', 'z-40']]
        header['class'] = header_classes + ['w-full', 'mb-8'] # add some bottom margin

    # Get inner main content 
    # The main content is usually inside a <div class="flex flex-col xl:flex-row gap-8">
    main_inner = "".join(str(child) for child in main.children if child.name)
    
    header_str = str(header) if header else ""
    
    # We combine them
    combined = f"{header_str}\n{main_inner}"
    jsx_content = html_to_jsx(combined)
    
    # Material symbol icons mapping
    # Just a rough conversion, replacing <span class="material-symbols-outlined" data-icon="search">search</span> with <Search /> etc.
    lucide_imports = set()
    
    def replacer(match):
        icon_name = match.group(1)
        # simplistic mapping, we will fallback manually if needed
        # map lowercase_underscore to PascalCase
        mapping = {
            'dashboard': 'LayoutDashboard',
            'security': 'Shield',
            'settings_input_component': 'Settings2',
            'psychology': 'Brain',
            'search': 'Search',
            'calendar_today': 'Calendar',
            'notifications': 'Bell',
            'account_circle': 'UserCircle',
            'cable': 'Cable', 
            'router': 'Router',
            'cell_tower': 'TowerControl',
            'battery_charging_full': 'BatteryCharging',
            'warning': 'AlertTriangle',
            'arrow_downward': 'ArrowDown',
            'arrow_upward': 'ArrowUp',
            'bolt': 'Zap',
            'water_drop': 'Droplets',
            'sensors': 'Cpu',
            'broadcast_on_home': 'RadioTower',
            'play_arrow': 'Play',
            'fast_forward': 'FastForward',
            'stop': 'Square',
            'analytics': 'LineChart',
            'tune': 'SlidersHorizontal',
            'memory': 'Microchip',
            'device_thermostat': 'Thermometer',
            'check_circle': 'CheckCircle2'
        }
        pascal = mapping.get(icon_name)
        if pascal:
            lucide_imports.add(pascal)
            return f"<{pascal} size={{20}} className=\"{match.group(2)}\" />"
        else:
            pascal_guess = "".join(word.capitalize() for word in icon_name.split('_'))
            lucide_imports.add(pascal_guess)
            return f"<{pascal_guess} size={{20}} className=\"{match.group(2)}\" />"
    
    # regex for <span class="material-symbols-outlined.*?" data-icon="(.*?)">.*?</span>
    jsx_content = re.sub(r'<span[^>]*class="material-symbols-outlined([^"]*)"[^>]*data-icon="([^"]*)"[^>]*>.*?</span>', lambda m: replacer(m) if m.re else replacer(re.match(r'.*data-icon="([^"]*)".*', m.group(0))), jsx_content)
    # sometimes class is just material-symbols-outlined without extra
    jsx_content = re.sub(r'<span[^>]*className="material-symbols-outlined(.*?)"[^>]*data-icon="([^"]*)"[^>]*>.*?</span>', lambda m: replacer(m), jsx_content)
    
    # Also if the icon text is inside the span without data-icon
    def raw_replacer(match):
        class_names = match.group(1).replace('material-symbols-outlined', '').strip()
        icon_name = match.group(2).strip()
        mapping = {
            'dashboard': 'LayoutDashboard',
            'security': 'Shield',
            'settings_input_component': 'Settings2',
            'psychology': 'Brain',
            'search': 'Search',
            'calendar_today': 'Calendar',
            'notifications': 'Bell',
            'account_circle': 'UserCircle',
            'cable': 'Cable', 
            'router': 'Router',
            'cell_tower': 'RadioTower', # Wait, mapped Server or TowerControl
            'battery_charging_full': 'BatteryCharging',
            'warning': 'AlertTriangle',
            'arrow_downward': 'ArrowDown',
            'arrow_upward': 'ArrowUp',
            'bolt': 'Zap',
            'water_drop': 'Droplets',
            'sensors': 'Cpu',
            'broadcast_on_home': 'RadioTower',
            'play_arrow': 'Play',
            'fast_forward': 'FastForward',
            'stop': 'Square',
            'analytics': 'LineChart',
            'tune': 'SlidersHorizontal',
            'memory': 'Cpu',
            'device_thermostat': 'Thermometer',
            'check_circle': 'CheckCircle2'
        }
        pascal = mapping.get(icon_name)
        if pascal:
            lucide_imports.add(pascal)
            return f"<{pascal} size={{20}} className=\"{class_names}\" />"
        else:
            pascal_guess = "".join(word.capitalize() for word in icon_name.split('_'))
            lucide_imports.add(pascal_guess)
            return f"<{pascal_guess} size={{20}} className=\"{class_names}\" />"

    jsx_content = re.sub(r'<span[^>]*className="material-symbols-outlined([^"]*)"[^>]*>([^<]+)</span>', raw_replacer, jsx_content)


    # Clean up empty classNames
    jsx_content = jsx_content.replace('className="" ', '')

    # Fix unescaped < and > if any outside tags, although bs4 handles most.
    # Fix the `<!-- -->` comments which React hates
    jsx_content = re.sub(r'<!--(.*?)-->', r'{/* \1 */}', jsx_content)

    lucide_import_str = f"import {{ {', '.join(lucide_imports)} }} from 'lucide-react';\n" if lucide_imports else ""

    react_component = f"""\"use client\";
import React from 'react';
{lucide_import_str}

export default function {page_name}() {{
  return (
    <div className="flex flex-col gap-8 pb-12 w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
        {jsx_content}
    </div>
  );
}}
"""
    with open(out_filename, 'w', encoding='utf-8') as f:
        f.write(react_component)
    print(f"Generated {out_filename} with imports: {lucide_imports}")

process_file('command_center_pacman.html', r'frontend\src\app\(dashboard)\command-center\page.tsx', 'CommandCenter')
process_file('operations_pacman.html', r'frontend\src\app\(dashboard)\operations\page.tsx', 'Operations')
process_file('simulation_pacman.html', r'frontend\src\app\(dashboard)\simulation-ai\page.tsx', 'SimulationAI')
