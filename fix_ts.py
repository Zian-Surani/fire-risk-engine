import re
import os

# Fix operations/page.tsx
file_ops = r'frontend\src\app\(dashboard)\operations\page.tsx'
with open(file_ops, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix imports in operations
text = re.sub(r'import \{.*?\} from \'lucide-react\';', 
    '''import { Search, Calendar, Bell, UserCircle, Layers, Crosshair, Zap, Navigation, ChevronRight, Activity, Battery, TriangleAlert, ArrowRight, Car, Fuel, RefreshCw } from 'lucide-react';''', text)

text = text.replace('<MyLocation', '<Crosshair')
text = text.replace('<ArrowForward', '<ArrowRight')
text = text.replace('<AlertTriangle', '<TriangleAlert')
text = text.replace('<Traffic', '<Car')
text = text.replace('<EvStation', '<Fuel')
text = text.replace('<AutoMode', '<RefreshCw')

with open(file_ops, 'w', encoding='utf-8') as f:
    f.write(text)


# Fix simulation-ai/page.tsx
file_sim = r'frontend\src\app\(dashboard)\simulation-ai\page.tsx'
with open(file_sim, 'r', encoding='utf-8') as f:
    sim_text = f.read()

sim_text = re.sub(r'import \{.*?\} from \'lucide-react\';', 
    '''import { Search, Calendar, Bell, UserCircle, Play, FastForward, Square, LineChart, SlidersHorizontal, Cpu, Thermometer, CheckCircle2, Sparkles, Target } from 'lucide-react';''', sim_text)

sim_text = sim_text.replace('<Grain', '<Sparkles')
sim_text = sim_text.replace('<Radar', '<Target')
sim_text = re.sub(r'strokeWidth="([^"]+)"', lambda m: f'strokeWidth={{{m.group(1)}}}', sim_text)
# there's a type string to number issue. Usually strokeWidth="1", we converted to strokeWidth={1}

with open(file_sim, 'w', encoding='utf-8') as f:
    f.write(sim_text)

