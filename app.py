import pygame
import math
import sys
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# Initialize Pygame
pygame.init()

# Get display info
display_info = pygame.display.Info()
available_width = display_info.current_w
available_height = display_info.current_h

# Set larger default window size
DEFAULT_WIDTH = 1800
DEFAULT_HEIGHT = 1000

WINDOW_WIDTH = min(DEFAULT_WIDTH, available_width - 50)
WINDOW_HEIGHT = min(DEFAULT_HEIGHT, available_height - 50)

SCALE_X = WINDOW_WIDTH / DEFAULT_WIDTH
SCALE_Y = WINDOW_HEIGHT / DEFAULT_HEIGHT
SCALE = min(SCALE_X, SCALE_Y, 1.0)

print(f"Screen resolution: {available_width}x{available_height}")
print(f"Window size: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
print(f"Scale factor: {SCALE}")

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("C++ Constructor Visualizer")
clock = pygame.time.Clock()

# Font sizes
base_font_size  = max(28, int(32 * SCALE))
small_font_size = max(22, int(26 * SCALE))
title_font_size = max(36, int(48 * SCALE))
tiny_font_size  = max(18, int(22 * SCALE))

font   = pygame.font.Font(None, base_font_size)
small  = pygame.font.Font(None, small_font_size)
title  = pygame.font.Font(None, title_font_size)
tiny   = pygame.font.Font(None, tiny_font_size)

# Colors
DARK_BG     = (10, 10, 20)
PANEL_BG    = (25, 25, 40)
CLASS_COLOR = (100, 150, 255)
PRIVATE_COLOR = (255, 120, 120)
PUBLIC_COLOR  = (120, 255, 120)
OBJ_COLORS    = [(255,180,50), (255,120,200), (100,255,100), (200,150,255), (80,220,220)]
HIGHLIGHT   = (255, 255, 100)
CONTROL     = (200, 150, 255)
TEXT        = (255, 255, 255)
CONSOLE_BG  = (20, 20, 30)
CONSOLE_TEXT= (0, 255, 0)
STEP_BG     = (60, 60, 80)
OK_GREEN    = (100, 255, 100)
ERROR_COLOR = (255, 100, 100)

# Layout (scaled)
def s(x, y, w, h):
    return pygame.Rect(int(x*SCALE), int(y*SCALE), int(w*SCALE), int(h*SCALE))

CLASS_BOX   = s(20, 20, 420, 420)
CODE_BOX    = s(460, 20, 480, 420)
CONSOLE_BOX = s(20, 460, 920, 160)
MAIN_BOX    = s(20, 640, 920, 260)
OBJECT_BOX1 = s(960, 20, 420, 280)
OBJECT_BOX2 = s(960, 320, 420, 280)
OUTPUT_BOX  = s(960, 620, 420, 140)
STEP_BOX    = s(960, 780, 420, 100)
HELP_BOX    = s(20, 920, 1360, 50)
PROGRESS    = s(20, 880, 1360, 24)
ERROR_BOX   = s(200, 300, 1000, 200)

# Helpers
def lerp(a, b, t): return a + (b - a) * t
def lerp2(p1, p2, t): return (lerp(p1[0], p2[0], t), lerp(p1[1], p2[1], t))

def draw_rounded_rect(r, color, border=0, radius=12, border_color=None):
    pygame.draw.rect(screen, color, r, 0, int(radius*SCALE))
    if border > 0 and border_color:
        pygame.draw.rect(screen, border_color, r, max(2, int(border*SCALE)), int(radius*SCALE))

def draw_text(x, y, txt, col=TEXT, f=small, outline=False):
    if outline:
        o = f.render(txt, True, (0,0,0))
        for dx, dy in [(-2,-2),(-2,2),(2,-2),(2,2)]:
            screen.blit(o, (int(x*SCALE)+dx, int(y*SCALE)+dy))
    s = f.render(txt, True, col)
    screen.blit(s, (int(x*SCALE), int(y*SCALE)))

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
        self.file_content = ""

    def parse(self, code_str=None, filepath=None):
        try:
            if filepath and os.path.exists(filepath):
                with open(filepath, encoding="utf-8") as f:
                    code = f.read()
            elif code_str:
                code = code_str
            else:
                self.error = "No code provided"
                return False

            # Store raw code lines and full content
            self.code_lines = code.splitlines()
            self.file_content = code
            
            # Remove comments more thoroughly
            code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            
            # Find class name and its content
            class_pattern = r'class\s+(\w+)\s*{'
            class_match = re.search(class_pattern, code)
            
            if not class_match:
                self.error = "No class found in the code"
                return False
                
            self.class_name = class_match.group(1)
            
            # Find the class body by matching braces
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
            
            print(f"Found class: {self.class_name}")
            
            # Parse member variables - look for declarations followed by semicolon
            var_pattern = r'(\w+(?:\s*[\*&])?)\s+(\w+)\s*[=;]'
            for match in re.finditer(var_pattern, class_body):
                typ, name = match.group(1).strip(), match.group(2).strip()
                # Filter out method declarations and common keywords
                if (name not in self.members and 
                    name != self.class_name and
                    '(' not in typ and
                    ')' not in name and
                    not any(x in name for x in ['(', ')', '{', '}'])):
                    self.members.append(name)
                    self.member_types[name] = typ
                    print(f"Found member: {typ} {name}")
            
            # Find constructor - look for class name followed by parentheses
            ctor_pattern = rf'{self.class_name}\s*\(([^)]*)\)\s*(?::[^{{]*)?\s*{{'
            ctor_match = re.search(ctor_pattern, code, re.DOTALL)
            
            if ctor_match:
                self.has_valid_constructor = True
                params_str = ctor_match.group(1).strip()
                
                # Find constructor body
                ctor_start = ctor_match.end()
                brace_count = 1
                ctor_end = ctor_start
                
                for i, char in enumerate(code[ctor_start:], ctor_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            ctor_end = i
                            break
                
                self.constructor_body = code[ctor_start:ctor_end]
                
                # Parse constructor parameters
                if params_str and params_str != 'void':
                    # Handle complex parameter types with default values
                    # Remove default values
                    params_str = re.sub(r'=\s*[^,)]+', '', params_str)
                    
                    # Split parameters respecting template brackets
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
                    
                    # Parse each parameter
                    for param in params:
                        # Split into type and name
                        parts = param.split()
                        if len(parts) >= 2:
                            name = parts[-1].replace('*', '').replace('&', '').strip()
                            typ = ' '.join(parts[:-1]).strip()
                            self.ctor_params.append(name)
                            self.ctor_param_types[name] = typ
                            print(f"Found parameter: {typ} {name}")
            
            # Map members to parameters based on constructor body assignments
            if self.constructor_body:
                for mem in self.members:
                    # Look for assignments like "this->member = param" or "member = param"
                    patterns = [
                        rf'{mem}\s*=\s*(\w+)',
                        rf'this->{mem}\s*=\s*(\w+)',
                        rf'{self.class_name}::\s*{mem}\s*=\s*(\w+)'
                    ]
                    
                    for pattern in patterns:
                        assign_match = re.search(pattern, self.constructor_body)
                        if assign_match:
                            param_name = assign_match.group(1)
                            if param_name in self.ctor_params:
                                self.member_to_param_map[mem] = param_name
                                print(f"Mapped {mem} to parameter {param_name}")
                                break
            
            # If no assignments found, try to map by name similarity
            if not self.member_to_param_map:
                for mem in self.members:
                    for param in self.ctor_params:
                        if mem == param or mem in param or param in mem:
                            self.member_to_param_map[mem] = param
                            print(f"Name-based mapping: {mem} -> {param}")
                            break
            
            # Find objects - look anywhere in the file, not just in main
            self._find_objects(code)
            
            # Try to find main function for context (optional)
            self._find_main(code)
            
            # Truncate code lines for display
            if len(self.code_lines) > 40:
                self.code_lines = self.code_lines[:35] + ['// ... (code truncated)']
            
            # Validate that we have objects
            if not self.objects:
                self.error = "No objects found - make sure your code creates objects of the class"
                return False
            
            print(f"Parsing successful! Found:")
            print(f"  - Class: {self.class_name}")
            print(f"  - Members: {len(self.members)}")
            print(f"  - Constructor parameters: {len(self.ctor_params)}")
            print(f"  - Objects: {len(self.objects)}")
            return True

        except Exception as e:
            self.error = f"Parse error: {str(e)}"
            print(f"Parse error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _find_main(self, code):
        """Find main function if it exists"""
        main_patterns = [
            r'int\s+main\s*\([^)]*\)\s*{',
            r'main\s*\(\s*\)\s*{',
            r'main\s*\(\s*int\s+argc\s*,\s*char\s*\*\s*argv\s*\[\]\s*\)\s*{',
            r'main\s*\(\s*int\s+argc\s*,\s*char\s*\*\*\s*argv\s*\)\s*{',
            r'void\s+main\s*\([^)]*\)\s*{'
        ]
        
        main_start = None
        for pattern in main_patterns:
            main_start = re.search(pattern, code)
            if main_start:
                break
        
        if main_start:
            start_idx = main_start.end()
            brace_count = 1
            end_idx = start_idx
            
            # Find matching closing brace
            for i, char in enumerate(code[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            main_body = code[start_idx:end_idx]
            self.main_lines = [l.strip() for l in main_body.split('\n') if l.strip()]
            print(f"Found main function with {len(self.main_lines)} lines")

    def _find_objects(self, code):
        """Find object declarations anywhere in the code"""
        
        # Multiple patterns for object creation
        obj_patterns = [
            # Pattern: ClassName objName(args);
            (rf'{self.class_name}\s+(\w+)\s*\(([^)]*)\)\s*;', True),
            # Pattern: ClassName objName = ClassName(args);
            (rf'{self.class_name}\s+(\w+)\s*=\s*{self.class_name}\s*\(([^)]*)\)\s*;', True),
            # Pattern: ClassName* objName = new ClassName(args);
            (rf'{self.class_name}\s*\*\s*(\w+)\s*=\s*new\s+{self.class_name}\s*\(([^)]*)\)\s*;', True),
            # Pattern: auto objName = ClassName(args);
            (rf'auto\s+(\w+)\s*=\s*{self.class_name}\s*\(([^)]*)\)\s*;', True),
            # Pattern: ClassName objName; (default constructor)
            (rf'{self.class_name}\s+(\w+)\s*;', False),
            # Pattern: ClassName objName = {args}; (C++11 uniform initialization)
            (rf'{self.class_name}\s+(\w+)\s*=\s*{{([^}}]*)}}\s*;', True),
            # Pattern: ClassName objName{args}; (C++11 uniform initialization)
            (rf'{self.class_name}\s+(\w+)\s*{{([^}}]*)}}\s*;', True),
        ]
        
        for pattern, has_args in obj_patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                if has_args and len(match.groups()) >= 2:
                    name, args_str = match.group(1), match.group(2)
                    
                    # Parse arguments
                    args = self._parse_arguments(args_str)
                    
                    # Check if this object already exists
                    if not any(obj['name'] == name for obj in self.objects):
                        self.objects.append({
                            'name': name,
                            'args': args,
                            'color': OBJ_COLORS[len(self.objects) % len(OBJ_COLORS)]
                        })
                        print(f"Found object: {name} with args {args}")
                        
                elif not has_args and len(match.groups()) >= 1:
                    name = match.group(1)
                    if not any(obj['name'] == name for obj in self.objects):
                        self.objects.append({
                            'name': name,
                            'args': [],
                            'color': OBJ_COLORS[len(self.objects) % len(OBJ_COLORS)]
                        })
                        print(f"Found object (default constructor): {name}")
        
        # If still no objects found, look for any variable of class type
        if not self.objects:
            # Look for variable declarations that might be of this class type
            var_pattern = rf'{self.class_name}\s+(\w+)'
            for match in re.finditer(var_pattern, code):
                name = match.group(1)
                # Make sure it's not part of a larger word
                if (name not in self.objects and 
                    name != self.class_name and
                    not any(x in name for x in ['(', ')', ';', '='])):
                    # Check if it's a declaration (followed by ; or = or ())
                    pos = match.end()
                    next_chars = code[pos:pos+10]
                    if ';' in next_chars or '=' in next_chars or '(' in next_chars:
                        self.objects.append({
                            'name': name,
                            'args': [],
                            'color': OBJ_COLORS[len(self.objects) % len(OBJ_COLORS)]
                        })
                        print(f"Found object by variable pattern: {name}")

    def _parse_arguments(self, args_str):
        """Parse argument string into list of arguments"""
        args = []
        if not args_str.strip():
            return args
            
        bracket_level = 0
        current = ''
        
        for char in args_str + ',':
            if char == ',' and bracket_level == 0:
                if current.strip():
                    # Clean up the argument
                    arg = current.strip()
                    # Remove quotes if present
                    if arg.startswith(('"', "'")) and arg.endswith(('"', "'")):
                        arg = arg[1:-1]
                    args.append(arg)
                current = ''
            else:
                if char in '([{':
                    bracket_level += 1
                elif char in ')]}':
                    bracket_level -= 1
                current += char
        
        return args

# ───────────────────────────────────────────────
#                   STEPS
# ───────────────────────────────────────────────

class Step:
    def __init__(self, label, where="main", main_hl=None, code_hl=None, out=None, action=None):
        self.label = label
        self.where = where
        self.main_highlight = main_hl
        self.code_highlight = code_hl
        self.output_text = out
        self.action = action
        self.completed = False
        self._action_done = False
        self._output_added = False

# ───────────────────────────────────────────────
#                VISUALIZER
# ───────────────────────────────────────────────

class Visualizer:
    def __init__(self):
        self.parser = None
        self.loaded = False
        self.show_code = True
        self.console = []
        self.current_obj = 0
        self.step = -1
        self.t = 0.0
        self.auto = False
        self.paused = False
        self.steps_cache = []
        self.error_message = None

        self.created = []
        self.initialized = []

    def load_file(self):
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            filetypes=[
                ("C++ files", "*.cpp *.cxx *.cc *.h *.hpp"),
                ("All files", "*.*")
            ]
        )
        if not path:
            return False

        print(f"\nLoading file: {path}")
        self.parser = CPPCodeParser()
        
        if self.parser.parse(filepath=path):
            self.loaded = True
            self.error_message = None
            self._reset_state()
            self.steps_cache = self.build_steps()
            print(f"Successfully loaded {os.path.basename(path)}")
            return True
        else:
            self.error_message = self.parser.error or "Unknown parse error"
            print(f"Failed to load: {self.error_message}")
            messagebox.showerror("Parse Error", self.error_message)
            return False

    def _reset_state(self):
        n = len(self.parser.objects) if self.parser else 0
        self.created = [False] * n
        self.initialized = [{m: False for m in self.parser.members} for _ in range(n)]
        self.current_obj = 0
        self.step = -1
        self.t = 0.0
        self.console.clear()
        self.steps_cache = []

    def build_steps(self):
        if not self.parser or self.current_obj >= len(self.parser.objects):
            return []

        obj = self.parser.objects[self.current_obj]
        name = obj["name"]
        args = obj["args"]
        steps = []

        # Find line numbers for highlighting
        obj_line = -1
        # Look in the full file content for the object declaration
        for i, line in enumerate(self.parser.code_lines):
            if f"{self.parser.class_name} {name}" in line or f"{name} =" in line:
                obj_line = i
                break

        ctor_line = -1
        for i, line in enumerate(self.parser.code_lines):
            if f"{self.parser.class_name}::" in line and f"{self.parser.class_name}::" + self.parser.class_name not in line:
                ctor_line = i
                break
        if ctor_line == -1:
            for i, line in enumerate(self.parser.code_lines):
                if f"{self.parser.class_name}(" in line and ')' in line and 'class' not in line:
                    ctor_line = i
                    break

        # Determine where we are (main or global scope)
        where = "main" if self.parser.main_lines else "global"

        # Step 1: Call constructor
        steps.append(Step(
            f"1. Call {name} constructor",
            where,
            main_hl=max(0, obj_line),
            out=f"Calling {self.parser.class_name} constructor for {name}"
        ))

        # Step 2: Enter constructor
        steps.append(Step(
            "2. Enter constructor",
            "ctor",
            code_hl=max(0, ctor_line),
            out=f"Entering {self.parser.class_name} constructor"
        ))

        # Step 3: Pass arguments (if any)
        if args and self.parser.ctor_params:
            param_strs = []
            for i, param in enumerate(self.parser.ctor_params):
                if i < len(args):
                    param_strs.append(f"{param} = {args[i]}")
            if param_strs:
                steps.append(Step(
                    "3. Pass arguments",
                    "ctor",
                    out="→ " + ", ".join(param_strs)
                ))
        elif args:
            # If we have args but no params, just show the values
            steps.append(Step(
                "3. Pass arguments",
                "ctor",
                out="→ " + ", ".join(str(a) for a in args)
            ))

        # Steps for member initialization
        if self.parser.members:
            member_num = 4
            for i, mem in enumerate(self.parser.members):
                # Find value for this member
                val = "?"
                param_name = self.parser.member_to_param_map.get(mem, "")
                
                if param_name and param_name in self.parser.ctor_params:
                    param_idx = self.parser.ctor_params.index(param_name)
                    if param_idx < len(args):
                        val = args[param_idx]
                elif i < len(args) and i < len(self.parser.ctor_params):
                    val = args[i]
                elif i < len(args):
                    val = args[i]

                def make_action(m=mem, v=val, idx=i):
                    def act(t_val):
                        if t_val >= 0.75:
                            self.initialized[self.current_obj][m] = True
                            if t_val >= 1.0 and not self.steps_cache[self.step]._action_done:
                                self.console.append(f"✓ {m} ← {v}")
                                self.steps_cache[self.step]._action_done = True
                                if len(self.console) > 7:
                                    self.console.pop(0)
                    return act

                steps.append(Step(
                    f"{member_num}.{i+1} Initialize {mem} = {val}",
                    "ctor",
                    out=f"Setting {mem} to {val}",
                    action=make_action()
                ))

        # Step: Constructor complete
        def complete_action(t_val):
            if t_val >= 0.75:
                self.created[self.current_obj] = True
                if t_val >= 1.0 and not self.steps_cache[self.step]._action_done:
                    self.console.append(f"✓ Object {name} created")
                    self.steps_cache[self.step]._action_done = True
                    if len(self.console) > 7:
                        self.console.pop(0)

        steps.append(Step(
            f"5. Constructor complete - {name} created",
            where,
            main_hl=max(0, obj_line),
            out=f"✓ {name} object created",
            action=complete_action
        ))

        # Look for method calls (only if we have main lines)
        if self.parser.main_lines:
            method_line = -1
            if obj_line >= 0:
                # Try to find method calls after the object declaration
                for i in range(obj_line + 1, min(obj_line + 5, len(self.parser.code_lines))):
                    if f"{name}." in self.parser.code_lines[i]:
                        method_line = i
                        break

            if method_line >= 0:
                method_name = re.search(rf'{name}\.(\w+)', self.parser.code_lines[method_line])
                if method_name:
                    steps.append(Step(
                        f"6. Call {name}.{method_name.group(1)}()",
                        where,
                        main_hl=method_line,
                        out=f"Calling {method_name.group(1)}() on {name}"
                    ))

        return steps

    def current_steps(self):
        return self.steps_cache

    def next_step(self):
        if not self.loaded or not self.parser:
            return
            
        steps = self.current_steps()
        if not steps:
            return
            
        if self.step < len(steps) - 1:
            self.step += 1
            self.t = 0.0
            # Reset action done flag for the new step
            if hasattr(steps[self.step], '_action_done'):
                steps[self.step]._action_done = False
            if hasattr(steps[self.step], '_output_added'):
                steps[self.step]._output_added = False
            print(f"Step {self.step + 1}/{len(steps)}: {steps[self.step].label}")
        elif self.current_obj < len(self.parser.objects) - 1:
            self.current_obj += 1
            self.step = 0
            self.t = 0.0
            self.console.clear()
            self.steps_cache = self.build_steps()
            print(f"Moving to object {self.current_obj + 1}/{len(self.parser.objects)}")
        else:
            self.step = len(steps)
            self.console.append("✓ Visualization complete!")
            print("Visualization complete!")

    def restart(self):
        self.current_obj = 0
        self.step = -1
        self.t = 0.0
        self.auto = False
        self.paused = False
        if self.loaded:
            self._reset_state()
            self.steps_cache = self.build_steps()

    def update(self):
        if not self.loaded or self.paused or self.step < 0:
            return
            
        steps = self.current_steps()
        if not steps or self.step >= len(steps):
            return
            
        self.t = min(1.0, self.t + 0.015)
        step = steps[self.step]
        
        if step.action:
            step.action(self.t)
        
        if self.t >= 0.8 and step.output_text and not step._output_added:
            if step.output_text not in self.console:
                self.console.append(step.output_text)
                step._output_added = True
                if len(self.console) > 7:
                    self.console.pop(0)
        
        if self.auto and self.t >= 1.0:
            self.next_step()

    def draw_error(self):
        if self.error_message:
            r = ERROR_BOX
            draw_rounded_rect(r, PANEL_BG, border=4, border_color=ERROR_COLOR)
            draw_text(r.x/SCALE + 50, r.y/SCALE + 30, "Error Loading File", ERROR_COLOR, font, True)
            
            # Word wrap error message
            words = self.error_message.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line + " " + word) < 60:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            y = r.y/SCALE + 100
            for line in lines[:4]:
                draw_text(r.x/SCALE + 50, y, line, ERROR_COLOR, tiny)
                y += 30
            
            draw_text(r.x/SCALE + 50, r.y/SCALE + 250, "Press O to try another file", TEXT, small)

    def draw_class(self):
        if not self.parser:
            return
        r = CLASS_BOX
        draw_rounded_rect(r, PANEL_BG, border=3, border_color=CLASS_COLOR)
        draw_text(r.x/SCALE+25, r.y/SCALE+20, f"Class {self.parser.class_name}", CLASS_COLOR, font, True)

        y = r.y/SCALE + 80
        draw_text(r.x/SCALE+35, y, "private:", PRIVATE_COLOR, small)
        y += 40
        
        if self.parser.members:
            for m in self.parser.members[:7]:
                t = self.parser.member_types.get(m, "?")
                draw_text(r.x/SCALE+50, y, f"{t} {m};", PRIVATE_COLOR, tiny)
                y += 28
        else:
            draw_text(r.x/SCALE+50, y, "(No members found)", PRIVATE_COLOR, tiny)
            y += 28

        y += 20
        draw_text(r.x/SCALE+35, y, "public:", PUBLIC_COLOR, small)
        y += 40
        
        if self.parser.ctor_params:
            params = ", ".join(self.parser.ctor_params)
            draw_text(r.x/SCALE+50, y, f"{self.parser.class_name}({params})", PUBLIC_COLOR, tiny)
        else:
            draw_text(r.x/SCALE+50, y, f"{self.parser.class_name}()", PUBLIC_COLOR, tiny)

    def draw_code(self, hl_line=None):
        if not self.show_code or not self.parser:
            return
        r = CODE_BOX
        draw_rounded_rect(r, PANEL_BG, border=3, border_color=PUBLIC_COLOR)
        draw_text(r.x/SCALE+25, r.y/SCALE+20, "C++ Code", PUBLIC_COLOR, font, True)

        y = r.y/SCALE + 70
        start_line = max(0, hl_line - 5) if hl_line is not None else 0
            
        for i in range(start_line, min(start_line + 15, len(self.parser.code_lines))):
            line = self.parser.code_lines[i]
            col = HIGHLIGHT if i == hl_line else TEXT
            txt = line[:60] + "..." if len(line) > 60 else line
            draw_text(r.x/SCALE+30, y, txt, col, tiny)
            y += 24

    def draw_console(self):
        r = CONSOLE_BOX
        draw_rounded_rect(r, CONSOLE_BG, border=3, border_color=CONSOLE_TEXT)
        draw_text(r.x/SCALE+25, r.y/SCALE+18, "Console Output", CONSOLE_TEXT, small, True)

        y = r.y/SCALE + 60
        for line in self.console[-7:]:
            draw_text(r.x/SCALE+35, y, f"> {line}", CONSOLE_TEXT, tiny)
            y += 24

    def draw_main(self, hl_line=None, in_ctor=False):
        if not self.parser:
            return
            
        r = MAIN_BOX
        draw_rounded_rect(r, PANEL_BG, border=3, border_color=CONTROL)
        
        # Determine what to show in this panel
        if self.parser.main_lines:
            draw_text(r.x/SCALE+25, r.y/SCALE+20, "main() function", CONTROL, font, True)
            lines_to_show = self.parser.main_lines
        else:
            draw_text(r.x/SCALE+25, r.y/SCALE+20, "Global Scope", CONTROL, font, True)
            # Show relevant parts of the code (object declarations)
            lines_to_show = []
            for obj in self.parser.objects[:3]:
                for line in self.parser.code_lines:
                    if obj['name'] in line and self.parser.class_name in line:
                        lines_to_show.append(line)
                        break
            if not lines_to_show:
                lines_to_show = ["(Object declarations found elsewhere)"]

        # Show control flow
        ax = r.right/SCALE - 100
        ay = r.y/SCALE + 80 + (min(self.step, 10) * 10 if self.step >= 0 else 0)
        
        if in_ctor:
            # Arrow pointing right (to constructor)
            pts = [(ax, ay), (ax+40, ay-10), (ax+40, ay+10)]
            pygame.draw.polygon(screen, CONTROL, [(p[0]*SCALE, p[1]*SCALE) for p in pts])
            draw_text(ax+50, ay-15, "in constructor", CONTROL, tiny)
        elif self.step >= 0:
            # Arrow pointing left (in current scope)
            pts = [(ax, ay), (ax-40, ay-10), (ax-40, ay+10)]
            pygame.draw.polygon(screen, CONTROL, [(p[0]*SCALE, p[1]*SCALE) for p in pts])
            scope_name = "main" if self.parser.main_lines else "global"
            draw_text(ax-200, ay-15, f"in {scope_name}", CONTROL, tiny)

        y = r.y/SCALE + 70
        for i, line in enumerate(lines_to_show[:10]):
            col = HIGHLIGHT if i == hl_line else TEXT
            txt = line[:70] + "..." if len(line) > 70 else line
            draw_text(r.x/SCALE+35, y, txt, col, tiny)
            y += 26

    def draw_object(self, idx, bx, by, is_current):
        if idx >= len(self.parser.objects) or not self.parser:
            return
            
        obj = self.parser.objects[idx]
        r = pygame.Rect(bx*SCALE, by*SCALE, 380*SCALE, 240*SCALE)

        # Pulse effect for current object
        if is_current and 0 <= self.step < len(self.current_steps()):
            p = 1.0 + 0.03 * math.sin(pygame.time.get_ticks() * 0.006)
            r.width = int(380*SCALE*p)
            r.height = int(240*SCALE*p)
            r.x -= (r.width - 380*SCALE)//2
            r.y -= (r.height - 240*SCALE)//2

        draw_rounded_rect(r, obj["color"], border=4, border_color=HIGHLIGHT if is_current else TEXT)

        # "CREATED" badge
        if self.created[idx]:
            br = pygame.Rect(r.right-100, r.top-25, 90, 30)
            draw_rounded_rect(br, (0,80,30), border=2, border_color=OK_GREEN)
            draw_text(br.x/SCALE+10, br.y/SCALE+6, "CREATED", OK_GREEN, tiny)

        # Object name
        draw_text(r.x/SCALE+20, r.y/SCALE+20, f"Object: {obj['name']}", TEXT, small, True)

        # Member variables
        y = r.y/SCALE + 70
        for m in self.parser.members[:6]:
            init = self.initialized[idx].get(m, False)
            
            # Find value
            val = "?"
            param_name = self.parser.member_to_param_map.get(m, "")
            if param_name and param_name in self.parser.ctor_params:
                param_idx = self.parser.ctor_params.index(param_name)
                if param_idx < len(obj["args"]):
                    val = obj["args"][param_idx]
            elif m in self.parser.ctor_params:
                param_idx = self.parser.ctor_params.index(m)
                if param_idx < len(obj["args"]):
                    val = obj["args"][param_idx]
            
            if init:
                color = OK_GREEN
                prefix = "✓"
            else:
                color = (160,160,160)
                prefix = "○"
                val = "—"
            
            draw_text(r.x/SCALE+25, y, f"{prefix} {m}: {val}", color, tiny)
            y += 32

    def draw_step_info(self):
        r = STEP_BOX
        draw_rounded_rect(r, STEP_BG, border=4, border_color=HIGHLIGHT)
        
        steps = self.current_steps()
        if steps and 0 <= self.step < len(steps):
            step = steps[self.step]
            draw_text(r.x/SCALE+30, r.y/SCALE+20, f"Step {self.step+1}/{len(steps)}", HIGHLIGHT, small, True)
            draw_text(r.x/SCALE+30, r.y/SCALE+50, step.label, TEXT, tiny)
            
            if self.current_obj < len(self.parser.objects):
                objname = self.parser.objects[self.current_obj]["name"]
                draw_text(r.x/SCALE+30, r.y/SCALE+75, f"Object: {objname}", (200,200,200), tiny)
        else:
            draw_text(r.x/SCALE+30, r.y/SCALE+40, "Press SPACE to start", HIGHLIGHT, small)

    def draw_help(self):
        r = HELP_BOX
        draw_rounded_rect(r, (40,40,60), border=2, border_color=HIGHLIGHT)
        msg = "O: Open file | SPACE: Next step | R: Restart | C: Toggle code | A: Auto-play | P: Pause | ESC: Exit"
        draw_text(r.x/SCALE+20, r.y/SCALE+16, msg, HIGHLIGHT, tiny)

    def draw_progress(self):
        if self.step < 0:
            return
            
        steps = self.current_steps()
        if not steps:
            return
            
        progress = (self.step + self.t) / len(steps)
        pygame.draw.rect(screen, (70,70,90), PROGRESS, 0, 10)
        pr = pygame.Rect(PROGRESS.x, PROGRESS.y, int(PROGRESS.width * progress), PROGRESS.height)
        pygame.draw.rect(screen, HIGHLIGHT, pr, 0, 10)
        draw_text(PROGRESS.x/SCALE + PROGRESS.width/SCALE + 20, PROGRESS.y/SCALE - 6,
                  f"{int(progress*100)}%", HIGHLIGHT, tiny)

    def render(self):
        screen.fill(DARK_BG)

        if not self.loaded:
            # Welcome screen
            draw_rounded_rect(s(400, 250, 1000, 300), PANEL_BG, border=4, border_color=HIGHLIGHT)
            draw_text(600, 300, "C++ Constructor Visualizer", HIGHLIGHT, font, True)
            draw_text(650, 380, "Press O to open a C++ file", TEXT, small)
            draw_text(620, 440, "Supports .cpp, .cxx, .cc, .h, .hpp files", (200,200,200), tiny)
            
            if self.error_message:
                self.draw_error()
            return

        self.draw_class()
        
        # Get current step info for highlighting
        hl_code = None
        hl_main = None
        in_ctor = False
        steps = self.current_steps()
        if steps and 0 <= self.step < len(steps):
            st = steps[self.step]
            hl_code = st.code_highlight
            hl_main = st.main_highlight
            in_ctor = st.where == "ctor"

        self.draw_code(hl_code)
        self.draw_console()
        self.draw_main(hl_main, in_ctor)
        self.draw_step_info()
        self.draw_help()
        self.draw_progress()

        # Draw objects
        for i in range(min(2, len(self.parser.objects))):
            y = 40 if i == 0 else 340
            is_current = (i == self.current_obj)
            self.draw_object(i, 970, y, is_current)

        # Completion message
        if (self.parser.objects and 
            self.current_obj == len(self.parser.objects)-1 and 
            self.step >= len(self.current_steps())):
            cr = s(600, 400, 600, 140)
            draw_rounded_rect(cr, (0,80,30), border=4, border_color=OK_GREEN)
            draw_text(680, 440, "✓ Visualization Complete!", OK_GREEN, font, True)
            draw_text(720, 500, "Press R to restart", OK_GREEN, small)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_o:
                        self.load_file()
                    elif event.key == pygame.K_SPACE and self.loaded:
                        self.next_step()
                    elif event.key == pygame.K_r and self.loaded:
                        self.restart()
                    elif event.key == pygame.K_c and self.loaded:
                        self.show_code = not self.show_code
                    elif event.key == pygame.K_a and self.loaded:
                        self.auto = not self.auto
                        print(f"Auto mode: {'ON' if self.auto else 'OFF'}")
                    elif event.key == pygame.K_p and self.loaded:
                        self.paused = not self.paused
                        print(f"Paused: {'YES' if self.paused else 'NO'}")
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            self.update()
            self.render()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

# ───────────────────────────────────────────────
#                     MAIN
# ───────────────────────────────────────────────

if __name__ == "__main__":
    viz = Visualizer()
    
    print("=" * 50)
    print("C++ Constructor Visualizer")
    print("=" * 50)
    print("Press O to open a C++ file")
    print("Press SPACE to step through constructor execution")
    print("Press A for auto-play mode")
    print("Press R to restart")
    print("Press ESC to exit")
    print("=" * 50)
    
    viz.run()
