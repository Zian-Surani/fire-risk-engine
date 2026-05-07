import re

def fix_imports_and_tags(filepath, page_type):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if page_type == 'command':
        content = re.sub(r'import \{.*?\} from \'lucide-react\';', 
            "import { Search, Calendar, Bell, UserCircle, AlertTriangle, ArrowDown, ArrowUp, Zap, Droplets, Cpu, RadioTower } from 'lucide-react';", content)
        content = content.replace('< text-xl size={20} className="calendar_today" />', '<Calendar size={20} className="text-slate-400" />')
        content = content.replace('< text-xl size={20} className="notifications" />', '<Bell size={20} className="text-slate-400" />')
        content = content.replace('< text-xl size={20} className="account_circle" />', '<UserCircle size={20} className="text-slate-400" />')
        content = content.replace('< text-sm mr-1 size={20} className="arrow_downward" />', '<ArrowDown size={14} className="text-secondary mr-1" />')
        content = content.replace('< text-sm mr-1 size={20} className="arrow_upward" />', '<ArrowUp size={14} className="text-tertiary mr-1" />')
        content = content.replace('< text-xl size={20} className="bolt" />', '<Zap size={20} className="text-primary" />')
        content = content.replace('< size={20} className="water_drop" />', '<Droplets size={20} />')
        content = content.replace('< size={20} className="sensors" />', '<Cpu size={20} />')
        content = content.replace('< size={20} className="broadcast_on_home" />', '<RadioTower size={20} />')
        content = content.replace('< text-xl size={20} className="warning" />', '<AlertTriangle size={20} className="text-tertiary" />')

    elif page_type == 'operations':
        content = re.sub(r'import \{.*?\} from \'lucide-react\';', 
            "import { Search, Calendar, Bell, UserCircle, Layers, MapPin, Zap, Navigation, ChevronRight, Activity, Battery, TriangleAlert } from 'lucide-react';", content)
        # We need to broadly fix tags for ops, let's use regex
        content = re.sub(r'<\s*text-[^\s]+ size=\{[^\}]+\} className=\"(.*?)\" />', r'<span className="material-symbols-outlined">\1</span>', content)
        content = re.sub(r'<\s*size=\{[^\}]+\} className=\"(.*?)\" />', r'<span className="material-symbols-outlined">\1</span>', content)

    elif page_type == 'simulation':
        content = re.sub(r'import \{.*?\} from \'lucide-react\';', 
            "import { Search, Calendar, Bell, UserCircle, Play, FastForward, Square, LineChart, SlidersHorizontal, Cpu, Thermometer, CheckCircle2 } from 'lucide-react';", content)
        content = re.sub(r'<\s*text-[^\s]+ size=\{[^\}]+\} className=\"(.*?)\" />', r'<span className="material-symbols-outlined">\1</span>', content)
        content = re.sub(r'<\s*text-[^\s]+ text-[^\s]+ size=\{[^\}]+\} className=\"(.*?)\" />', r'<span className="material-symbols-outlined">\1</span>', content)
        content = re.sub(r'<\s*size=\{[^\}]+\} className=\"(.*?)\" />', r'<span className="material-symbols-outlined">\1</span>', content)

    # Make sure 'clip-path' is 'clipPath'
    content = content.replace("'clip-path'", "clipPath")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

fix_imports_and_tags(r'frontend\src\app\(dashboard)\command-center\page.tsx', 'command')
fix_imports_and_tags(r'frontend\src\app\(dashboard)\operations\page.tsx', 'operations')
fix_imports_and_tags(r'frontend\src\app\(dashboard)\simulation-ai\page.tsx', 'simulation')
