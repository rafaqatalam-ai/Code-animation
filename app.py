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
        max-height: 400px;
        overflow-y: auto;
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
        margin: 10px 0;
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
        width: 100%;
    }
    .control-button:hover {
        background-color: #4a4a6a;
    }
    .hl-line {
        background-color: #ffff64;
        color: black;
        padding: 2px 5px;
        border-radius: 3px;
        font-weight: bold;
    }
    .arrow-indicator {
        color: #c896ff;
        font-size: 20px;
        margin: 10px 0;
        padding: 5px;
        background-color: #2a2a3a;
        border-radius: 5px;
        text-align: center;
    }
    .error-box {
        background-color: #ff4d4d20;
        border: 2px solid #ff4d4d;
        border-radius: 10px;
        padding: 20px;
        color: #ff4d4d;
        text-align: center;
        margin: 20px;
    }
    .success-box {
        background-color: #00ff0020;
        border: 2px solid #00ff00;
        border-radius: 10px;
        padding: 10px;
        color: #00ff00;
        text-align: center;
    }
    .debug-box {
        background-color: #2a2a3a;
        border: 1px solid #6496ff;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        color: #a0a0ff;
        font-family: monospace;
        font-size: 12px;
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
if 'steps' not in st.session_state:
    st.session_state.steps = []
if 'parse_error' not in st.session_state:
    st.session_state.parse_error = None
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = []

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
        self.all_classes = []
        self.debug_info = []

    def parse(self, code):
        try:
            self.debug_info = ["Starting parse..."]
            
            # Store raw code lines
            self.code_lines = [line.rstrip() for line in code.split('\n') if line.strip()]
            self.debug_info.append(f"Found {len(self.code_lines)} non-empty lines")
            
            if not self.code_lines:
                self.error = "Empty file"
                return False
            
            # Remove comments but keep line structure
            clean_code = self._remove_comments(code)
            
            # Find all classes
            self._find_classes(clean_code)
            
            if not self.all_classes:
                self.error = "No classes found in the code. Make sure your code contains a 'class' definition."
                self.debug_info.append("ERROR: No classes found")
                return False
            
            # Use the first class found
            class_info = self.all_classes[0]
            self.class_name = class_info['name']
            self.members = class_info['members']
            self.member_types = class_info['member_types']
            self.ctor_params = class_info['params']
            self.ctor_param_types = class_info['param_types']
            self.constructor_body = class_info['ctor_body']
            
            self.debug_info.append(f"Found class: {self.class_name}")
            self.debug_info.append(f"Members: {self.members}")
            self.debug_info.append(f"Constructor params: {self.ctor_params}")
            
            # Map members to parameters
            self._map_members_to_params()
            
            # Find objects
            self._find_objects(clean_code)
            
            self.debug_info.append(f"Found objects: {[obj['name'] for obj in self.objects]}")
            
            if not self.objects:
                self.error = "No objects found. Make sure your code creates objects of the class."
                return False
            
            # Find main function (optional)
            self._find_main(clean_code)
            
            return True

        except Exception as e:
            self.error = f"Parse error: {str(e)}"
            self.debug_info.append(f"EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _remove_comments(self, code):
        """Remove comments from code"""
        # Remove single line comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

    def _find_classes(self, code):
        """Find all classes in the code"""
        # Pattern to match class definition
        class_pattern = r'class\s+(\w+)\s*{'
        
        for match in re.finditer(class_pattern, code):
            class_name = match.group(1)
            start_pos = match.end()
            
            # Find matching closing brace
            brace_count = 1
            pos = start_pos
            while pos < len(code) and brace_count > 0:
                if code[pos] == '{':
                    brace_count += 1
                elif code[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            class_body = code[start_pos:pos-1]
            
            # Parse class members
            members = []
            member_types = {}
            
            # Look for member variables (common patterns)
            patterns = [
                r'(\w+(?:\s*[\*&])?)\s+(\w+)\s*;',  # type name;
                r'(\w+(?:\s*[\*&])?)\s+(\w+)\s*=', # type name = value;
                r'(\w+)\s+(\w+)\s*\[\d*\]\s*;',     # array type name[size];
            ]
            
            for pattern in patterns:
                for var_match in re.finditer(pattern, class_body):
                    if len(var_match.groups()) >= 2:
                        typ, name = var_match.group(1).strip(), var_match.group(2).strip()
                        # Filter out methods and keywords
                        if (name not in members and 
                            '(' not in typ and 
                            ')' not in name and
                            name != class_name and
                            not name.startswith('_')):
                            members.append(name)
                            member_types[name] = typ
                            self.debug_info.append(f"Found member: {typ} {name}")
            
            # Find constructor
            ctor_params = []
            ctor_param_types = {}
            ctor_body = ""
            
            # Look for constructor definition
            ctor_pattern = rf'{class_name}\s*\(([^)]*)\)'
            for ctor_match in re.finditer(ctor_pattern, code):
                params_str = ctor_match.group(1).strip()
                
                # Check if this is likely a constructor (followed by { or :)
                next_chars = code[ctor_match.end():ctor_match.end()+20]
                if '{' in next_chars or ':' in next_chars:
                    
                    # Find constructor body
                    ctor_start = ctor_match.end()
                    brace_count = 1
                    ctor_end = ctor_start
                    
                    # Find opening brace
                    while ctor_start < len(code) and code[ctor_start] != '{':
                        ctor_start += 1
                    
                    if ctor_start < len(code):
                        ctor_start += 1
                        for i, ch in enumerate(code[ctor_start:], ctor_start):
                            if ch == '{':
                                brace_count += 1
                            elif ch == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    ctor_end = i
                                    break
                        
                        ctor_body = code[ctor_start:ctor_end]
                    
                    # Parse parameters
                    if params_str and params_str != 'void':
                        # Handle default values
                        params_str = re.sub(r'=\s*[^,)]+', '', params_str)
                        
                        # Split parameters
                        for param in self._split_parameters(params_str):
                            if param.strip():
                                # Handle pointers and references
                                parts = param.strip().split()
                                if len(parts) >= 2:
                                    name = parts[-1].replace('*', '').replace('&', '').strip()
                                    typ = ' '.join(parts[:-1]).strip()
                                    ctor_params.append(name)
                                    ctor_param_types[name] = typ
                                    self.debug_info.append(f"Found parameter: {typ} {name}")
                    
                    break  # Use first constructor found
            
            self.all_classes.append({
                'name': class_name,
                'members': members,
                'member_types': member_types,
                'params': ctor_params,
                'param_types': ctor_param_types,
                'ctor_body': ctor_body
            })

    def _split_parameters(self, params_str):
        """Split parameter string respecting templates"""
        params = []
        bracket_level = 0
        current = ''
        
        for char in params_str + ',':
            if char == ',' and bracket_level == 0:
                if current.strip():
                    params.append(current.strip())
                current = ''
            else:
                if char == '<':
                    bracket_level += 1
                elif char == '>':
                    bracket_level -= 1
                current += char
        
        return params

    def _map_members_to_params(self):
        """Map member variables to constructor parameters"""
        # First try exact matches
        for mem in self.members:
            for param in self.ctor_params:
                if mem == param:
                    self.member_to_param_map[mem] = param
                    break
        
        # If no exact matches, try by position
        if not self.member_to_param_map:
            for i, mem in enumerate(self.members):
                if i < len(self.ctor_params):
                    self.member_to_param_map[mem] = self.ctor_params[i]

    def _find_objects(self, code):
        """Find object declarations"""
        
        # Multiple patterns for object creation
        patterns = [
            # ClassName objName(args);
            (rf'{self.class_name}\s+(\w+)\s*\(([^)]*)\)\s*;', True),
            # ClassName objName; (default constructor)
            (rf'{self.class_name}\s+(\w+)\s*;', False),
            # ClassName objName = ClassName(args);
            (rf'{self.class_name}\s+(\w+)\s*=\s*{self.class_name}\s*\(([^)]*)\)\s*;', True),
            # ClassName* objName = new ClassName(args);
            (rf'{self.class_name}\s*\*\s*(\w+)\s*=\s*new\s+{self.class_name}\s*\(([^)]*)\)\s*;', True),
            # ClassName objName = {args};
            (rf'{self.class_name}\s+(\w+)\s*=\s*{{([^}}]*)}}\s*;', True),
            # ClassName objName{args};
            (rf'{self.class_name}\s+(\w+)\s*{{([^}}]*)}}\s*;', True),
        ]
        
        for pattern, has_args in patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                if has_args and len(match.groups()) >= 2:
                    name, args_str = match.group(1), match.group(2)
                    args = self._parse_arguments(args_str)
                elif not has_args and len(match.groups()) >= 1:
                    name = match.group(1)
                    args = []
                else:
                    continue
                
                # Check if object already exists
                if not any(obj['name'] == name for obj in self.objects):
                    self.objects.append({
                        'name': name,
                        'args': args
                    })
                    self.debug_info.append(f"Found object: {name} with args {args}")

    def _parse_arguments(self, args_str):
        """Parse argument string into list"""
        args = []
        if not args_str.strip():
            return args
        
        bracket_level = 0
        current = ''
        
        for char in args_str + ',':
            if char == ',' and bracket_level == 0:
                if current.strip():
                    arg = current.strip()
                    # Remove quotes
                    if arg.startswith(('"', "'")) and arg.endswith(('"', "'")):
                        arg = arg[1:-1]
                    # Try to convert to number if possible
                    try:
                        if '.' in arg:
                            arg = float(arg)
                        else:
                            arg = int(arg)
                    except:
                        pass
                    args.append(arg)
                current = ''
            else:
                if char in '([{':
                    bracket_level += 1
                elif char in ')]}':
                    bracket_level -= 1
                current += char
        
        return args

    def _find_main(self, code):
        """Find main function"""
        main_patterns = [
            r'int\s+main\s*\([^)]*\)\s*{',
            r'main\s*\(\s*\)\s*{',
            r'void\s+main\s*\([^)]*\)\s*{'
        ]
        
        for pattern in main_patterns:
            main_match = re.search(pattern, code)
            if main_match:
                start = main_match.end()
                brace_count = 1
                end = start
                
                # Find opening brace
                while start < len(code) and code[start] != '{':
                    start += 1
                
                if start < len(code):
                    start += 1
                    for i, ch in enumerate(code[start:], start):
                        if ch == '{':
                            brace_count += 1
                        elif ch == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i
                                break
                    
                    main_body = code[start:end]
                    self.main_lines = [line.strip() for line in main_body.split('\n') if line.strip()]
                    self.debug_info.append(f"Found main function with {len(self.main_lines)} lines")
                    break

# ───────────────────────────────────────────────
#                VISUALIZER FUNCTIONS
# ───────────────────────────────────────────────

def parse_code(code):
    """Parse the C++ code"""
    parser = CPPCodeParser()
    if parser.parse(code):
        st.session_state.debug_info = parser.debug_info
        return parser
    else:
        st.session_state.parse_error = parser.error
        st.session_state.debug_info = parser.debug_info
        return None

def build_steps(parser, obj_idx):
    """Build visualization steps for an object"""
    if not parser or obj_idx >= len(parser.objects):
        return []
    
    obj = parser.objects[obj_idx]
    steps = []
    
    steps.append(f"1. Call {obj['name']} constructor")
    steps.append("2. Enter constructor")
    
    if obj['args']:
        if parser.ctor_params:
            param_strs = []
            for i, param in enumerate(parser.ctor_params):
                if i < len(obj['args']):
                    param_strs.append(f"{param} = {obj['args'][i]}")
            steps.append(f"3. Pass arguments: {', '.join(param_strs)}")
        else:
            steps.append(f"3. Pass arguments: {', '.join(str(a) for a in obj['args'])}")
    
    for i, mem in enumerate(parser.members):
        val = "?"
        if i < len(obj['args']):
            val = obj['args'][i]
        elif mem in parser.member_to_param_map:
            param = parser.member_to_param_map[mem]
            if param in parser.ctor_params:
                param_idx = parser.ctor_params.index(param)
                if param_idx < len(obj['args']):
                    val = obj['args'][param_idx]
        
        steps.append(f"4.{i+1} Initialize {mem} = {val}")
    
    steps.append(f"5. Constructor complete - {obj['name']} created")
    
    return steps

def next_step():
    """Move to next step"""
    if st.session_state.step < len(st.session_state.steps) - 1:
        st.session_state.step += 1
        # Add to console
        step_text = st.session_state.steps[st.session_state.step]
        if step_text not in st.session_state.console:
            st.session_state.console.append(step_text)
            if len(st.session_state.console) > 7:
                st.session_state.console.pop(0)
        
        # Update member initialization
        if st.session_state.parsed_data:
            step_num = st.session_state.step
            # Steps 3+ are member initializations (step 0: call, 1: enter, 2: args, then members)
            if step_num >= 3 and step_num - 3 < len(st.session_state.parsed_data.members):
                mem_idx = step_num - 3
                if mem_idx < len(st.session_state.parsed_data.members):
                    mem = st.session_state.parsed_data.members[mem_idx]
                    st.session_state.initialized[st.session_state.current_obj][mem] = True
            
            # Last step marks object as created
            if step_num == len(st.session_state.steps) - 1:
                st.session_state.created[st.session_state.current_obj] = True
                
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
        st.session_state.console.append("✓ Visualization complete!")

def restart():
    """Restart visualization"""
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
    """Render class information panel"""
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f"### 📦 Class {parser.class_name}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔒 private:**")
        if parser.members:
            for mem in parser.members[:7]:
                typ = parser.member_types.get(mem, "?")
                st.markdown(f"<span style='color: #ff7878;'>{typ} {mem};</span>", 
                           unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #888;'>(No member variables found)</span>", 
                       unsafe_allow_html=True)
    
    with col2:
        st.markdown("**🔓 public:**")
        if parser.ctor_params:
            params = ", ".join(parser.ctor_params)
            st.markdown(f"<span style='color: #78ff78;'>{parser.class_name}({params})</span>", 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color: #78ff78;'>{parser.class_name}()</span>", 
                       unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_code_panel(parser, hl_line=None):
    """Render code panel with optional highlighting"""
    st.markdown('<div class="code-panel">', unsafe_allow_html=True)
    st.markdown("### 📝 C++ Code")
    
    if parser.code_lines:
        start_line = max(0, hl_line - 5) if hl_line is not None and hl_line >= 0 else 0
        end_line = min(start_line + 15, len(parser.code_lines))
        
        for i in range(start_line, end_line):
            line = parser.code_lines[i]
            if i == hl_line:
                st.markdown(f"<div class='hl-line'>{line}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color: #a0a0ff;'>{line}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color: #888;'>No code to display</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_console_panel():
    """Render console output panel"""
    st.markdown('<div class="console-panel">', unsafe_allow_html=True)
    st.markdown("### 📟 Console Output")
    if st.session_state.console:
        for line in st.session_state.console[-7:]:
            st.markdown(f"<div>> {line}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color: #666;'>> Waiting for steps...</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_main_panel(parser, hl_line=None, in_ctor=False):
    """Render main function panel"""
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### 🎯 Program Flow")
    
    # Arrow indicator
    if in_ctor:
        st.markdown("<div class='arrow-indicator'>➡️ Currently in constructor</div>", 
                   unsafe_allow_html=True)
    else:
        st.markdown("<div class='arrow-indicator'>⬅️ Currently in main/global scope</div>", 
                   unsafe_allow_html=True)
    
    if parser.main_lines:
        for i, line in enumerate(parser.main_lines[:8]):
            if i == hl_line:
                st.markdown(f"<div class='hl-line'>{line}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div>{line}</div>", unsafe_allow_html=True)
    else:
        # Show object declarations
        st.markdown("**Global Objects:**")
        for obj in parser.objects:
            args_str = ", ".join(str(a) for a in obj['args'])
            st.markdown(f"<div>{parser.class_name} {obj['name']}({args_str});</div>", 
                       unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_object_panel(parser, idx, is_current):
    """Render object visualization panel"""
    obj = parser.objects[idx]
    
    panel_class = "object-panel"
    if is_current:
        panel_class += " current"
    if st.session_state.created[idx]:
        panel_class += " created"
    
    st.markdown(f'<div class="{panel_class}">', unsafe_allow_html=True)
    st.markdown(f"### 🎯 Object: {obj['name']}")
    
    if st.session_state.created[idx]:
        st.markdown("**✅ CREATED**")
    
    if parser.members:
        for mem in parser.members[:6]:
            init = st.session_state.initialized[idx].get(mem, False)
            val = "?"
            
            # Find value
            if mem in parser.member_to_param_map:
                param = parser.member_to_param_map[mem]
                if param in parser.ctor_params:
                    param_idx = parser.ctor_params.index(param)
                    if param_idx < len(obj['args']):
                        val = obj['args'][param_idx]
            elif mem in parser.ctor_params:
                param_idx = parser.ctor_params.index(mem)
                if param_idx < len(obj['args']):
                    val = obj['args'][param_idx]
            
            if init:
                st.markdown(f"<div class='member-init completed'>✓ {mem}: {val}</div>", 
                           unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='member-init'>○ {mem}: —</div>", 
                           unsafe_allow_html=True)
    else:
        st.markdown("<div style='color: #666;'>(No member variables)</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_step_info():
    """Render step information"""
    st.markdown('<div class="step-box">', unsafe_allow_html=True)
    if (st.session_state.step >= 0 and 
        st.session_state.step < len(st.session_state.steps)):
        st.markdown(f"### ⚡ Step {st.session_state.step + 1}/{len(st.session_state.steps)}")
        st.markdown(f"**{st.session_state.steps[st.session_state.step]}**")
        if st.session_state.parsed_data:
            obj = st.session_state.parsed_data.objects[st.session_state.current_obj]
            st.markdown(f"📌 Object: {obj['name']}")
    else:
        st.markdown("### ▶️ Press SPACE or click Next to start")
    st.markdown('</div>', unsafe_allow_html=True)

def render_progress():
    """Render progress bar"""
    if st.session_state.step >= 0 and st.session_state.steps:
        progress = (st.session_state.step + 1) / len(st.session_state.steps)
        st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress*100}%;"></div>
        </div>
        <div style="text-align: right; color: #ffff64;">{int(progress*100)}% Complete</div>
        """, unsafe_allow_html=True)

def render_debug_info():
    """Render debug information"""
    if st.session_state.debug_info and st.session_state.parse_error:
        with st.expander("🔍 Debug Information"):
            st.markdown('<div class="debug-box">', unsafe_allow_html=True)
            for line in st.session_state.debug_info:
                st.markdown(f"<div>{line}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ───────────────────────────────────────────────
#                     MAIN
# ───────────────────────────────────────────────

def main():
    st.markdown('<h1 class="main-title">🔧 C++ Constructor Visualizer</h1>', 
                unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "📂 Choose a C++ file", 
        type=['cpp', 'h', 'hpp', 'cxx', 'cc'],
        help="Upload any C++ file containing a class and object declarations"
    )
    
    # Example code button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("📋 Load Example", use_container_width=True):
            example_code = """#include <iostream>
#include <string>
using namespace std;

class Person {
private:
    string name;
    int age;
    double height;
    string city;
public:
    Person(string n, int a, double h, string c) {
        name = n;
        age = a;
        height = h;
        city = c;
    }
    
    void display() {
        cout << name << " is " << age << " years old, " 
             << height << "m tall, from " << city << endl;
    }
};

int main() {
    Person p1("Alice", 25, 1.75, "New York");
    p1.display();
    
    Person p2("Bob", 30, 1.85, "London");
    p2.display();
    
    return 0;
}"""
            st.session_state.code = example_code
            parser = parse_code(example_code)
            if parser:
                st.session_state.parsed_data = parser
                st.session_state.steps = build_steps(parser, 0)
                st.session_state.created = [False] * len(parser.objects)
                st.session_state.initialized = [
                    {m: False for m in parser.members} 
                    for _ in range(len(parser.objects))
                ]
                st.session_state.parse_error = None
                st.rerun()
    
    if uploaded_file is not None:
        code = uploaded_file.getvalue().decode("utf-8")
        st.session_state.code = code
        
        with st.spinner("Parsing C++ code..."):
            parser = parse_code(code)
            if parser:
                st.session_state.parsed_data = parser
                st.session_state.steps = build_steps(parser, 0)
                st.session_state.created = [False] * len(parser.objects)
                st.session_state.initialized = [
                    {m: False for m in parser.members} 
                    for _ in range(len(parser.objects))
                ]
                st.session_state.parse_error = None
                st.success(f"✅ Successfully parsed! Found class '{parser.class_name}' with {len(parser.objects)} objects.")
            else:
                st.session_state.parse_error = st.session_state.parse_error or "Failed to parse code"
    
    # Show error if any
    if st.session_state.parse_error:
        st.markdown(f"""
        <div class="error-box">
            ❌ Error: {st.session_state.parse_error}<br>
            Please check your C++ syntax and try again.
        </div>
        """, unsafe_allow_html=True)
        
        # Show debug info
        render_debug_info()
    
    if st.session_state.parsed_data:
        parser = st.session_state.parsed_data
        
        # Controls
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("⏭️ Next", key="next", use_container_width=True):
                next_step()
                st.rerun()
        with col2:
            if st.button("🔄 Restart", key="restart", use_container_width=True):
                restart()
                st.rerun()
        with col3:
            auto_text = "⏸️ Pause" if st.session_state.auto_play else "▶️ Auto"
            if st.button(auto_text, key="auto", use_container_width=True):
                st.session_state.auto_play = not st.session_state.auto_play
                st.rerun()
        with col4:
            pause_text = "▶️ Resume" if st.session_state.paused else "⏸️ Pause"
            if st.button(pause_text, key="pause", use_container_width=True):
                st.session_state.paused = not st.session_state.paused
                st.rerun()
        with col5:
            if st.button("📁 New File", key="new", use_container_width=True):
                st.session_state.parsed_data = None
                st.session_state.code = ""
                st.session_state.steps = []
                st.session_state.parse_error = None
                st.session_state.debug_info = []
                st.rerun()
        
        # Progress
        render_progress()
        
        # Main layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            render_class_panel(parser)
            render_console_panel()
        
        with col2:
            hl_line = None
            in_ctor = False
            
            if 0 <= st.session_state.step < len(st.session_state.steps):
                step_text = st.session_state.steps[st.session_state.step]
                if "enter" in step_text.lower():
                    in_ctor = True
                    # Find constructor line
                    for i, line in enumerate(parser.code_lines):
                        if parser.class_name in line and '(' in line and ')' in line:
                            if 'class' not in line.lower():
                                hl_line = i
                                break
                elif "call" in step_text.lower():
                    # Find object declaration line
                    obj = parser.objects[st.session_state.current_obj]
                    for i, line in enumerate(parser.code_lines):
                        if obj['name'] in line and parser.class_name in line:
                            hl_line = i
                            break
            
            render_code_panel(parser, hl_line)
            render_main_panel(parser, hl_line, in_ctor)
        
        # Objects
        st.markdown("### 📦 Objects")
        obj_cols = st.columns(2)
        for i in range(min(2, len(parser.objects))):
            with obj_cols[i]:
                render_object_panel(parser, i, i == st.session_state.current_obj)
        
        # Step info
        render_step_info()
        
        # Help text
        st.markdown("""
        <div style="background-color: #28283c; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <span style="color: #ffff64; font-weight: bold;">⌨️ Keyboard Shortcuts:</span><br>
            • <kbd>Space</kbd> - Next step<br>
            • <kbd>R</kbd> - Restart<br>
            • <kbd>A</kbd> - Toggle auto-play<br>
            • <kbd>P</kbd> - Pause/Resume
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-play
        if st.session_state.auto_play and not st.session_state.paused:
            if st.session_state.step < len(st.session_state.steps) - 1:
                time.sleep(1.5)
                next_step()
                st.rerun()

if __name__ == "__main__":
    main()
