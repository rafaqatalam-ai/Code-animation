import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np
import base64
from io import BytesIO
import sys
from pathlib import Path
import re
import time

# Page configuration
st.set_page_config(
    page_title="C++ Constructor Visualizer",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 18px;
        padding: 12px;
        border-radius: 10px;
        border: none;
        transition: all 0.3s;
        font-weight: bold;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
        font-size: 14px;
        border: 3px solid #4CAF50;
        border-radius: 10px;
        background: #1E1E1E;
        color: #FFD700;
    }
    .success-box {
        padding: 20px;
        border-radius: 15px;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 3px solid #28a745;
        color: #155724;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        font-size: 16px;
    }
    .animation-container {
        border: 4px solid #4CAF50;
        border-radius: 20px;
        padding: 25px;
        margin-top: 25px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 20px 30px rgba(0,0,0,0.3);
    }
    .class-box {
        background: #1E1E1E;
        border-radius: 15px;
        padding: 20px;
        border: 3px solid #4CAF50;
        color: white;
        margin: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .object-box {
        background: #2D2D2D;
        border-radius: 15px;
        padding: 20px;
        border: 3px solid #FFD700;
        color: white;
        margin: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .step-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: black;
        padding: 15px 25px;
        border-radius: 50px;
        font-weight: bold;
        font-size: 24px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        border: 2px solid white;
    }
    .private-member {
        color: #FF6B6B;
        font-size: 16px;
        margin: 8px 0;
        padding-left: 25px;
        font-family: 'Courier New', monospace;
    }
    .public-member {
        color: #6BFF6B;
        font-size: 16px;
        margin: 8px 0;
        padding-left: 25px;
        font-family: 'Courier New', monospace;
    }
    .parameter-pill {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
        color: white;
        padding: 12px 25px;
        border-radius: 30px;
        font-weight: bold;
        font-size: 18px;
        display: inline-block;
        margin: 10px;
        animation: bounce 1s infinite;
        border: 2px solid white;
        box-shadow: 0 5px 10px rgba(0,0,0,0.2);
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    .arrow-animation {
        font-size: 40px;
        color: #FFD700;
        animation: moveArrow 1s infinite;
        text-align: center;
        margin: 20px;
    }
    @keyframes moveArrow {
        0% { transform: translateX(0); }
        50% { transform: translateX(20px); }
        100% { transform: translateX(0); }
    }
    .control-flow {
        background: #2D2D2D;
        padding: 15px;
        border-radius: 50px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        margin-top: 25px;
        border: 3px solid #FFD700;
        color: #FFD700;
    }
    .status-badge {
        float: right;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: normal;
    }
    .creating-badge {
        background: #FFD700;
        color: black;
    }
    .created-badge {
        background: #4CAF50;
        color: white;
    }
    .member-table {
        width: 100%;
        margin-top: 15px;
        border-collapse: collapse;
    }
    .member-table th {
        color: #FFD700;
        text-align: left;
        padding: 8px;
        border-bottom: 2px solid #FFD700;
    }
    .member-table td {
        padding: 8px;
        border-bottom: 1px solid #444;
    }
    .init-check {
        color: #4CAF50;
        font-weight: bold;
    }
    .init-pending {
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None
if 'auto_play' not in st.session_state:
    st.session_state.auto_play = False

class CPPCodeParser:
    def __init__(self):
        self.class_name = ""
        self.private_members = []
        self.constructor_params = []
        self.objects = []
        self.error = None
        
    def parse(self, code):
        try:
            # Reset data
            self.class_name = ""
            self.private_members = []
            self.constructor_params = []
            self.objects = []
            
            # Extract class name
            class_match = re.search(r'class\s+(\w+)', code)
            if class_match:
                self.class_name = class_match.group(1)
            
            # Extract private members
            private_section = re.search(r'private:\s*(.*?)(?=public:|};)', code, re.DOTALL)
            if private_section:
                private_text = private_section.group(1)
                members = re.findall(r'(\w+)\s+(\w+);', private_text)
                for member_type, member_name in members:
                    self.private_members.append(member_name)
            
            # Extract constructor parameters
            constructor_match = re.search(r'(\w+)\s*\((.*?)\)\s*{', code)
            if constructor_match:
                params_text = constructor_match.group(2)
                params = re.findall(r'\w+\s+(\w+)', params_text)
                self.constructor_params = params
            
            # Extract object creations
            main_section = re.search(r'main\s*\(.*?\)\s*{(.*?)}', code, re.DOTALL)
            if main_section:
                main_text = main_section.group(1)
                obj_pattern = rf'{self.class_name}\s+(\w+)\s*\((.*?)\);'
                objects = re.findall(obj_pattern, main_text)
                
                for obj_name, params_str in objects:
                    params = [p.strip().strip('"') for p in params_str.split(',')]
                    self.objects.append({
                        'name': obj_name,
                        'params': params
                    })
            
            return {
                'class_name': self.class_name,
                'private_members': self.private_members,
                'constructor_params': self.constructor_params,
                'objects': self.objects,
                'error': self.error
            }
        except Exception as e:
            return {'error': str(e)}

def create_animation_html(step, parsed_data):
    """Create HTML/CSS animation based on current step"""
    
    if not parsed_data or parsed_data.get('error'):
        return "<div style='color: red; padding: 20px;'>No valid data to display</div>"
    
    class_name = parsed_data.get('class_name', 'Student')
    private_members = parsed_data.get('private_members', ['name', 'age', 'major'])
    constructor_params = parsed_data.get('constructor_params', ['n', 'a', 'm'])
    objects = parsed_data.get('objects', [])
    
    if not objects:
        objects = [{'name': 'student1', 'params': ['Ali Raza', '20', 'Computer Science']}]
    
    # Step descriptions
    step_texts = [
        "📌 main() calls constructor",
        "⚡ Control transfers to constructor",
        "📦 Parameters are being passed",
        "🔧 Initializing: " + (private_members[0] if private_members else "name"),
        "🔧 Initializing: " + (private_members[1] if len(private_members) > 1 else "age"),
        "🔧 Initializing: " + (private_members[2] if len(private_members) > 2 else "major"),
        "✅ Constructor completes",
        "🔄 Control returns to main()",
        "📢 display() method called",
        "🎉 Object successfully created!"
    ]
    
    current_text = step_texts[step] if step < len(step_texts) else "Complete!"
    
    # Build HTML animation as a proper HTML string
    html = f'''
    <div style="font-family: 'Segoe UI', Arial, sans-serif; color: white;">
        <!-- Step Indicator -->
        <div class="step-badge">
            Step {step + 1}/10: {current_text}
        </div>
        
        <!-- Main Animation Area -->
        <div style="display: flex; gap: 25px; margin-top: 25px;">
            <!-- Class Structure -->
            <div class="class-box" style="flex: 1;">
                <h2 style="color: #4CAF50; margin-top: 0; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">
                    📦 {class_name} Class
                </h2>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #FF6B6B; margin: 10px 0;">🔒 Private Members:</h3>
                    {''.join([f'<div class="private-member">• {member}</div>' for member in private_members])}
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #6BFF6B; margin: 10px 0;">🔓 Public Methods:</h3>
                    <div class="public-member">+ {class_name}({', '.join(constructor_params)})</div>
                    <div class="public-member">+ display()</div>
                </div>
                
                <!-- Constructor Body (visible during initialization) -->
                {f'''
                <div style="margin-top: 25px; padding: 15px; background: #2D2D2D; border-radius: 10px; border-left: 5px solid #FFD700;">
                    <h4 style="color: #FFD700; margin: 0 0 10px 0;">⚙️ Constructor Execution:</h4>
                    {''.join([f'<div style="color: white; font-family: monospace; margin: 5px 0;">{member} = {constructor_params[i]};</div>' 
                             for i, member in enumerate(private_members)])}
                </div>
                ''' if 2 <= step <= 6 else ''}
            </div>
            
            <!-- Objects Area -->
            <div class="object-box" style="flex: 1;">
                <h2 style="color: #FFD700; margin-top: 0; border-bottom: 2px solid #FFD700; padding-bottom: 10px;">
                    🎯 Objects
                </h2>
                
                {''.join([f'''
                <div style="background: {'#FFD700' if i == 0 and step < 7 else '#363636'}; 
                            border-radius: 12px; 
                            padding: 15px; 
                            margin: 15px 0;
                            border: 2px solid {'#FFD700' if i == 0 and step < 7 else '#666'};
                            transition: all 0.3s;">
                    <h3 style="color: {'black' if i == 0 and step < 7 else '#FFD700'}; 
                               margin: 0 0 10px 0;
                               display: flex;
                               justify-content: space-between;
                               align-items: center;">
                        <span>{obj['name']}</span>
                        {f'<span class="status-badge creating-badge">⚡ CREATING</span>' if i == 0 and 1 <= step <= 6 else ''}
                        {f'<span class="status-badge created-badge">✓ CREATED</span>' if i == 0 and step >= 7 else ''}
                    </h3>
                    
                    <table class="member-table">
                        <tr>
                            <th>Member</th>
                            <th>Value</th>
                            <th>Status</th>
                        </tr>
                        {''.join([f'''
                        <tr>
                            <td style="color: {'black' if i == 0 and step < 7 else '#FFD700'};">
                                {private_members[j] if j < len(private_members) else f'param{j}'}
                            </td>
                            <td style="color: {'black' if i == 0 and step < 7 else 'white'};">
                                {obj['params'][j] if j < len(obj['params']) else '...'}
                            </td>
                            <td>
                                <span class="{'init-check' if step > j + 3 and i == 0 else 'init-pending'}">
                                    {'✓ Initialized' if step > j + 3 and i == 0 else '○ Pending'}
                                </span>
                            </td>
                        </tr>
                        ''' for j in range(min(3, len(private_members)))])}
                    </table>
                </div>
                ''' for i, obj in enumerate(objects)])}
            </div>
        </div>
        
        <!-- Parameter Passing Animation -->
        {f'''
        <div style="margin-top: 30px; text-align: center;">
            <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-bottom: 20px;">
                {''.join([f'<div class="parameter-pill">{param}: {objects[0]["params"][i] if objects and i < len(objects[0]["params"]) else "..."}</div>' 
                         for i, param in enumerate(constructor_params)])}
            </div>
            <div class="arrow-animation">
                ⬇️ ⬇️ ⬇️  PARAMETERS FLOWING TO CONSTRUCTOR  ⬇️ ⬇️ ⬇️
            </div>
        </div>
        ''' if 2 <= step <= 3 else ''}
        
        <!-- Control Flow Indicator -->
        {f'''
        <div class="control-flow">
            {'⚡ CONTROL IN main() FUNCTION' if step < 2 or step > 6 else '🔧 CONTROL INSIDE CONSTRUCTOR'}
        </div>
        ''' if step > 0 else ''}
    </div>
    '''
    
    return html

def main():
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 20px; margin-bottom: 30px; box-shadow: 0 20px 30px rgba(0,0,0,0.3);">
        <h1 style="color: white; font-size: 52px; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            🎮 C++ Constructor Visualizer
        </h1>
        <p style="color: #FFD700; font-size: 24px; margin: 10px 0 0 0; font-weight: bold;">
            Visualize Parameterized Constructors Step by Step
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📋 Instructions")
        st.info("""
        1. **Paste your C++ code** in the text area
        2. **Click 'Generate Animation'** to parse
        3. **Use controls** to step through execution
        4. **Watch** as parameters are passed and members initialized
        """)
        
        st.markdown("---")
        st.markdown("## 🎯 Sample Codes")
        
        if st.button("📚 Student Class Example", use_container_width=True):
            sample = '''#include <iostream>
#include <string>
using namespace std;

class Student {
private:
    string name;
    int age;
    string major;
    
public:
    Student(string n, int a, string m) {
        name = n;
        age = a;
        major = m;
    }
    
    void display() {
        cout << name << ", " << age << ", " << major << endl;
    }
};

int main() {
    Student student1("Ali Raza", 20, "Computer Science");
    student1.display();
    return 0;
}'''
            st.session_state.sample = sample
            st.rerun()
    
    # Main content
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📝 Enter Your C++ Code")
        
        default_code = st.session_state.get('sample', '''#include <iostream>
#include <string>
using namespace std;

class Student {
private:
    string name;
    int age;
    string major;
    
public:
    Student(string n, int a, string m) {
        name = n;
        age = a;
        major = m;
    }
    
    void display() {
        cout << "Name: " << name << ", Age: " << age << ", Major: " << major << endl;
    }
};

int main() {
    Student student1("Ali Raza", 20, "Computer Science");
    student1.display();
    return 0;
}''')
        
        cpp_code = st.text_area(
            "",
            value=default_code,
            height=300,
            key="code_input"
        )
        
        if st.button("🎬 Generate Animation", use_container_width=True):
            parser = CPPCodeParser()
            parsed = parser.parse(cpp_code)
            st.session_state.parsed_data = parsed
            st.session_state.step = 0
            st.session_state.auto_play = False
    
    with col2:
        st.markdown("### 📊 Analysis")
        if st.session_state.parsed_data and not st.session_state.parsed_data.get('error'):
            data = st.session_state.parsed_data
            st.markdown(f"""
            <div class="success-box">
                <h4>✅ Code Parsed Successfully!</h4>
                <p><b>Class:</b> {data.get('class_name', 'N/A')}</p>
                <p><b>Private Members:</b> {len(data.get('private_members', []))}</p>
                <p><b>Constructor Params:</b> {len(data.get('constructor_params', []))}</p>
                <p><b>Objects Found:</b> {len(data.get('objects', []))}</p>
            </div>
            """, unsafe_allow_html=True)
        elif st.session_state.parsed_data and st.session_state.parsed_data.get('error'):
            st.error(f"❌ {st.session_state.parsed_data['error']}")
    
    # Animation Player
    if st.session_state.parsed_data and not st.session_state.parsed_data.get('error'):
        st.markdown("---")
        st.markdown("## 🎬 Animation Player")
        
        # Controls
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("⏮️ First", use_container_width=True):
                st.session_state.step = 0
                st.session_state.auto_play = False
        with col2:
            if st.button("⏪ Prev", use_container_width=True):
                st.session_state.step = max(0, st.session_state.step - 1)
                st.session_state.auto_play = False
        with col3:
            play_text = "⏸️ Pause" if st.session_state.auto_play else "▶️ Play"
            if st.button(play_text, use_container_width=True):
                st.session_state.auto_play = not st.session_state.auto_play
        with col4:
            if st.button("⏩ Next", use_container_width=True):
                st.session_state.step = min(9, st.session_state.step + 1)
                st.session_state.auto_play = False
        with col5:
            if st.button("⏭️ Last", use_container_width=True):
                st.session_state.step = 9
                st.session_state.auto_play = False
        
        # Progress
        st.progress((st.session_state.step + 1) / 10, 
                   text=f"**Step {st.session_state.step + 1}/10**")
        
        # Animation display - Use st.markdown with unsafe_allow_html=True
        html_anim = create_animation_html(st.session_state.step, st.session_state.parsed_data)
        st.markdown(f'<div class="animation-container">{html_anim}</div>', unsafe_allow_html=True)
        
        # Auto-play logic
        if st.session_state.auto_play:
            if st.session_state.step < 9:
                time.sleep(1.5)
                st.session_state.step += 1
                st.rerun()
            else:
                st.session_state.auto_play = False
                st.balloons()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 20px; font-size: 16px;">
        Made with ❤️ for C++ Students | Step-by-Step Constructor Visualization
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
