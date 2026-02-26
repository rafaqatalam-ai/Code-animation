import streamlit as st
import re
import time

# Page config
st.set_page_config(
    page_title="C++ Constructor Visualizer",
    page_icon="🔧",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        background-color: #0a0a14;
    }
    .main-title {
        color: #ffff64;
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .panel {
        background-color: #191928;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        border: 2px solid #6496ff;
        color: white;
    }
    .code-panel {
        background-color: #1e1e2e;
        border-radius: 10px;
        padding: 15px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        color: #a0a0ff;
        border: 2px solid #78ff78;
    }
    .console-panel {
        background-color: #14141e;
        border-radius: 10px;
        padding: 15px;
        font-family: 'Courier New', monospace;
        color: #00ff00;
        border: 2px solid #00ff00;
        height: 150px;
        overflow-y: auto;
    }
    .object-panel {
        background-color: #ffb432;
        border-radius: 10px;
        padding: 15px;
        margin: 10px;
        color: black;
        border: 2px solid #ffff64;
        transition: all 0.3s ease;
    }
    .object-panel.current {
        transform: scale(1.05);
        border: 4px solid #ffff64;
        box-shadow: 0 0 20px #ffff64;
    }
    .object-panel.created {
        border: 4px solid #64ff64;
    }
    .member-init {
        margin: 5px 0;
        padding: 3px;
        border-radius: 3px;
    }
    .member-init.completed {
        background-color: #2a5a2a;
        color: #a0ffa0;
    }
    .step-box {
        background-color: #3c3c50;
        border-radius: 10px;
        padding: 15px;
        border: 2px solid #ffff64;
        color: white;
    }
    .progress-bar {
        height: 20px;
        background-color: #46465a;
        border-radius: 10px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background-color: #ffff64;
        transition: width 0.3s ease;
    }
    .control-button {
        background-color: #32324a;
        color: white;
        border: 2px solid #c896ff;
        border-radius: 5px;
        padding: 10px 20px;
        margin: 5px;
        cursor: pointer;
        font-size: 16px;
    }
    .control-button:hover {
        background-color: #4a4a6a;
    }
    .hl-line {
        background-color: #ffff64;
        color: black;
        padding: 2px 5px;
        border-radius: 3px;
    }
    .arrow-indicator {
        color: #c896ff;
        font-size: 20px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = -1
if 'current_obj' not in st.session_state:
    st.session_state.current_obj = 0
if 'auto_play' not in st.session_state:
    st.session_state.auto_play = False
if 'paused' not in st.session_state:
    st.session_state.paused = False
if 'console' not in st.session_state:
    st.session_state.console = []
if 'created' not in st.session_state:
    st.session_state.created = []
if 'initialized' not in st.session_state:
    st.session_state.initialized = []
if 'code' not in st.session_state:
    st.session_state.code = ""
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None

# ───────────────────────────────────────────────
#                  PARSER
# ───────────────────────────────────────────────

class CPPCodeParser:
    def __init__(self):
        self.class_name = ""
        self.members = []
        self.member_types = {}
        self.ctor_params = []
        self.ctor_param_types = {}
        self.objects = []
        self.code_lines = []
        self.main_lines = []
        self.error = None
        self.member_to_param_map = {}
        self.has_valid_constructor = False
        self.constructor_body = ""

    def parse(self, code):
        try:
            # Store raw code lines
            self.code_lines = code.split('\n')
            
            # Remove comments
            code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            
            # Find class
            class_match = re.search(r'class\s+(\w+)\s*{', code)
            if not class_match:
                self.error = "No class found"
                return False
                
            self.class_name = class_match.group(1)
            
            # Find class body
            class_start = class_match.end()
            brace_count = 1
            class_end = class_start
            
            for i, char in enumerate(code[class_start:], class_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = i
                        break
            
            class_body = code[class_start:class_end]
            
            # Parse members
            var_pattern = r'(\w+(?:\s*[\*&])?)\s+(\w+)\s*[=;]'
            for match in re.finditer(var_pattern, class_body):
                typ, name = match.group(1).strip(), match.group(2).strip()
                if name not in self.members and '(' not in typ:
                    self.members.append(name)
                    self.member_types[name] = typ
            
            # Find constructor
            ctor_pattern = rf'{self.class_name}\s*\(([^)]*)\)'
            ctor_match = re.search(ctor_pattern, code)
            
            if ctor_match:
                params_str = ctor_match.group(1).strip()
                
                # Parse parameters
                if params_str and params_str != 'void':
                    for param in params_str.split(','):
                        if param.strip():
                            parts = param.strip().split()
                            if len(parts) >= 2:
                                name = parts[-1].replace('*', '').replace('&', '').strip()
                                typ = ' '.join(parts[:-1]).strip()
                                self.ctor_params.append(name)
                                self.ctor_param_types[name] = typ
            
            # Map members to parameters
            for i, mem in enumerate(self.members):
                if i < len(self.ctor_params):
                    self.member_to_param_map[mem] = self.ctor_params[i]
            
            # Find objects
            obj_pattern = rf'{self.class_name}\s+(\w+)\s*\(([^)]*)\)\s*;'
            for match in re.finditer(obj_pattern, code):
                name, args_str = match.group(1), match.group(2)
                args = [a.strip().strip('"\'') for a in args_str.split(',') if a.strip()]
                self.objects.append({
                    'name': name,
                    'args': args
                })
            
            # Find main
            main_match = re.search(r'main\s*\([^)]*\)\s*{', code)
            if main_match:
                start = main_match.end()
                brace_count = 1
                end = start
                for i, char in enumerate(code[start:], start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i
                            break
                self.main_lines = code[start:end].split('\n')
            
            return len(self.objects) > 0

        except Exception as e:
            self.error = str(e)
            return False

# ───────────────────────────────────────────────
#                VISUALIZER FUNCTIONS
# ───────────────────────────────────────────────

def parse_code(code):
    parser = CPPCodeParser()
    if parser.parse(code):
        return parser
    return None

def build_steps(parser, obj_idx):
    if not parser or obj_idx >= len(parser.objects):
        return []
    
    obj = parser.objects[obj_idx]
    steps = []
    
    steps.append(f"1. Call {obj['name']} constructor")
    steps.append("2. Enter constructor")
    
    if obj['args']:
        steps.append(f"3. Pass arguments: {', '.join(str(a) for a in obj['args'])}")
    
    for i, mem in enumerate(parser.members):
        val = obj['args'][i] if i < len(obj['args']) else "?"
        steps.append(f"4.{i+1} Initialize {mem} = {val}")
    
    steps.append(f"5. Constructor complete - {obj['name']} created")
    
    return steps

def next_step():
    if st.session_state.step < len(st.session_state.steps) - 1:
        st.session_state.step += 1
        st.session_state.t = 0
    elif st.session_state.current_obj < len(st.session_state.parsed_data.objects) - 1:
        st.session_state.current_obj += 1
        st.session_state.step = 0
        st.session_state.console = []
        st.session_state.steps = build_steps(
            st.session_state.parsed_data, 
            st.session_state.current_obj
        )
    else:
        st.session_state.step = len(st.session_state.steps)

def restart():
    st.session_state.current_obj = 0
    st.session_state.step = -1
    st.session_state.auto_play = False
    st.session_state.paused = False
    st.session_state.console = []
    if st.session_state.parsed_data:
        st.session_state.steps = build_steps(st.session_state.parsed_data, 0)
        st.session_state.created = [False] * len(st.session_state.parsed_data.objects)
        st.session_state.initialized = [
            {m: False for m in st.session_state.parsed_data.members} 
            for _ in range(len(st.session_state.parsed_data.objects))
        ]

# ───────────────────────────────────────────────
#                UI COMPONENTS
# ───────────────────────────────────────────────

def render_class_panel(parser):
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f"### Class {parser.class_name}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**private:**")
        for mem in parser.members[:7]:
            typ = parser.member_types.get(mem, "?")
            st.markdown(f"<span style='color: #ff7878;'>{typ} {mem};</span>", 
                       unsafe_allow_html=True)
    
    with col2:
        st.markdown("**public:**")
        params = ", ".join(parser.ctor_params)
        st.markdown(f"<span style='color: #78ff78;'>{parser.class_name}({params})</span>", 
                   unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_code_panel(parser, hl_line=None):
    st.markdown('<div class="code-panel">', unsafe_allow_html=True)
    st.markdown("### C++ Code")
    
    start_line = max(0, hl_line - 5) if hl_line else 0
    for i in range(start_line, min(start_line + 15, len(parser.code_lines))):
        line = parser.code_lines[i]
        if i == hl_line:
            st.markdown(f"<div class='hl-line'>{line}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div>{line}</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_console_panel():
    st.markdown('<div class="console-panel">', unsafe_allow_html=True)
    st.markdown("### Console Output")
    for line in st.session_state.console[-7:]:
        st.markdown(f"> {line}")
    st.markdown('</div>', unsafe_allow_html=True)

def render_main_panel(parser, hl_line=None, in_ctor=False):
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### main() function")
    
    # Arrow indicator
    if in_ctor:
        st.markdown("<div class='arrow-indicator'>→ in constructor</div>", 
                   unsafe_allow_html=True)
    else:
        st.markdown("<div class='arrow-indicator'>← in main</div>", 
                   unsafe_allow_html=True)
    
    lines_to_show = parser.main_lines if parser.main_lines else ["(No main function)"]
    for i, line in enumerate(lines_to_show[:10]):
        if i == hl_line:
            st.markdown(f"<div class='hl-line'>{line}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div>{line}</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_object_panel(parser, idx, is_current):
    obj = parser.objects[idx]
    
    panel_class = "object-panel"
    if is_current:
        panel_class += " current"
    if st.session_state.created[idx]:
        panel_class += " created"
    
    st.markdown(f'<div class="{panel_class}">', unsafe_allow_html=True)
    st.markdown(f"### Object: {obj['name']}")
    
    if st.session_state.created[idx]:
        st.markdown("**✓ CREATED**")
    
    for mem in parser.members[:6]:
        init = st.session_state.initialized[idx].get(mem, False)
        val = "?"
        
        if mem in parser.ctor_params:
            param_idx = parser.ctor_params.index(mem)
            if param_idx < len(obj['args']):
                val = obj['args'][param_idx]
        
        if init:
            st.markdown(f"<div class='member-init completed'>✓ {mem}: {val}</div>", 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='member-init'>○ {mem}: —</div>", 
                       unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_step_info():
    st.markdown('<div class="step-box">', unsafe_allow_html=True)
    if st.session_state.step >= 0 and st.session_state.step < len(st.session_state.steps):
        st.markdown(f"### Step {st.session_state.step + 1}/{len(st.session_state.steps)}")
        st.markdown(f"**{st.session_state.steps[st.session_state.step]}**")
        if st.session_state.parsed_data:
            obj = st.session_state.parsed_data.objects[st.session_state.current_obj]
            st.markdown(f"Object: {obj['name']}")
    else:
        st.markdown("### Press SPACE to start")
    st.markdown('</div>', unsafe_allow_html=True)

def render_progress():
    if st.session_state.step >= 0 and st.session_state.steps:
        progress = (st.session_state.step + 0.5) / len(st.session_state.steps)
        st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress*100}%;"></div>
        </div>
        <div style="text-align: right;">{int(progress*100)}%</div>
        """, unsafe_allow_html=True)

# ───────────────────────────────────────────────
#                     MAIN
# ───────────────────────────────────────────────

def main():
    st.markdown('<h1 class="main-title">C++ Constructor Visualizer</h1>', 
                unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader("Choose a C++ file", type=['cpp', 'h', 'hpp', 'cxx'])
    
    if uploaded_file is not None:
        code = uploaded_file.getvalue().decode("utf-8")
        st.session_state.code = code
        
        # Parse code
        parser = parse_code(code)
        if parser:
            st.session_state.parsed_data = parser
            if not st.session_state.steps:
                st.session_state.steps = build_steps(parser, 0)
                st.session_state.created = [False] * len(parser.objects)
                st.session_state.initialized = [
                    {m: False for m in parser.members} 
                    for _ in range(len(parser.objects))
                ]
        else:
            st.error("Failed to parse code")
            return
    
    if st.session_state.parsed_data:
        parser = st.session_state.parsed_data
        
        # Controls
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("⏭️ Next", key="next"):
                next_step()
        with col2:
            if st.button("🔄 Restart", key="restart"):
                restart()
        with col3:
            auto_text = "⏸️ Pause" if st.session_state.auto_play else "▶️ Auto"
            if st.button(auto_text, key="auto"):
                st.session_state.auto_play = not st.session_state.auto_play
        with col4:
            pause_text = "▶️ Resume" if st.session_state.paused else "⏸️ Pause"
            if st.button(pause_text, key="pause"):
                st.session_state.paused = not st.session_state.paused
        with col5:
            if st.button("📁 New File", key="new"):
                st.session_state.parsed_data = None
                st.rerun()
        
        # Progress
        render_progress()
        
        # Main layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            render_class_panel(parser)
            render_console_panel()
        
        with col2:
            hl_code = st.session_state.step if 0 <= st.session_state.step < len(st.session_state.steps) else None
            render_code_panel(parser, hl_code)
        
        # Objects
        st.markdown("### Objects")
        obj_cols = st.columns(2)
        for i in range(min(2, len(parser.objects))):
            with obj_cols[i]:
                render_object_panel(parser, i, i == st.session_state.current_obj)
        
        # Step info
        render_step_info()
        
        # Help text
        st.markdown("""
        <div style="background-color: #28283c; padding: 10px; border-radius: 5px; margin-top: 20px;">
            <span style="color: #ffff64;">Keyboard Shortcuts:</span> 
            SPACE = Next | R = Restart | A = Auto-play | P = Pause
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-play
        if st.session_state.auto_play and not st.session_state.paused:
            if st.session_state.step < len(st.session_state.steps) - 1:
                time.sleep(1)
                next_step()
                st.rerun()

if __name__ == "__main__":
    main()
