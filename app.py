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
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        padding: 10px;
        border-radius: 5px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #45a049;
        transform: scale(1.02);
    }
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
        font-size: 14px;
        border: 2px solid #4CAF50;
        border-radius: 5px;
    }
    .success-box {
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        color: #155724;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .info-box {
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #17a2b8;
        color: #0c5460;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .animation-container {
        border: 3px solid #4CAF50;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .step-indicator {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000;
        padding: 15px;
        border-radius: 10px;
        font-weight: bold;
        text-align: center;
        font-size: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .control-panel {
        background: #2D2D2D;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #4CAF50;
        margin: 20px 0;
    }
    .object-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        border: 2px solid #FFD700;
    }
    .parameter-tag {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
        padding: 8px 15px;
        border-radius: 20px;
        color: white;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
        animation: bounce 1s infinite;
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    .arrow {
        font-size: 30px;
        color: #FFD700;
        animation: moveArrow 1s infinite;
    }
    @keyframes moveArrow {
        0% { transform: translateX(0); }
        50% { transform: translateX(10px); }
        100% { transform: translateX(0); }
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
if 'current_object' not in st.session_state:
    st.session_state.current_object = 0

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
    objects = parsed_data.get('objects', [{'name': 'student1', 'params': ['Ali', '20', 'CS']}])
    
    # Step descriptions
    step_texts = [
        "📌 Step 1: main() calls constructor",
        "⚡ Step 2: Control transfers to constructor",
        "📦 Step 3: Parameters are passed",
        "🔧 Step 4: Initializing private member: " + private_members[0] if private_members else "name",
        "🔧 Step 5: Initializing private member: " + private_members[1] if len(private_members) > 1 else "age",
        "🔧 Step 6: Initializing private member: " + private_members[2] if len(private_members) > 2 else "major",
        "✅ Step 7: Constructor completes",
        "🔄 Step 8: Control returns to main()",
        "📢 Step 9: display() method called",
        "🎉 Step 10: Object successfully created!"
    ]
    
    current_text = step_texts[step] if step < len(step_texts) else "Complete!"
    
    # Build HTML animation
    html = f"""
    <div style="font-family: Arial, sans-serif;">
        <!-- Step Indicator -->
        <div class="step-indicator" style="margin-bottom: 20px;">
            {current_text}
        </div>
        
        <div style="display: flex; gap: 20px; margin-top: 20px;">
            <!-- Class Structure -->
            <div style="flex: 1; background: #1E1E1E; border-radius: 15px; padding: 20px; border: 3px solid #4CAF50;">
                <h3 style="color: #4CAF50; margin-top: 0;">📦 {class_name} Class</h3>
                <div style="border-top: 2px solid #4CAF50; margin: 10px 0;"></div>
                
                <div style="color: #FF6B6B; margin: 15px 0;">
                    <strong style="font-size: 16px;">🔒 private:</strong><br>
                    {''.join([f'<span style="display: block; margin: 5px 0 5px 20px;">• {member}</span>' for member in private_members])}
                </div>
                
                <div style="border-top: 1px solid #444; margin: 15px 0;"></div>
                
                <div style="color: #6BFF6B;">
                    <strong style="font-size: 16px;">🔓 public:</strong><br>
                    <span style="display: block; margin: 5px 0 5px 20px;">
                        + {class_name}({', '.join(constructor_params)})
                    </span>
                    <span style="display: block; margin: 5px 0 5px 20px;">+ display()</span>
                </div>
                
                <!-- Constructor Body (visible in steps 3-6) -->
                {f'''
                <div style="margin-top: 20px; padding: 15px; background: #2D2D2D; border-radius: 10px; border-left: 5px solid #FFD700;">
                    <strong style="color: #FFD700;">Constructor Body:</strong><br>
                    <code style="color: #fff;">
                        {chr(10).join([f'&nbsp;&nbsp;{member} = {param};' for member, param in zip(private_members, constructor_params)])}
                    </code>
                </div>
                ''' if 3 <= step <= 6 else ''}
            </div>
            
            <!-- Objects Area -->
            <div style="flex: 1; background: #1E1E1E; border-radius: 15px; padding: 20px; border: 3px solid #FFD700;">
                <h3 style="color: #FFD700; margin-top: 0;">🎯 Objects</h3>
                <div style="border-top: 2px solid #FFD700; margin: 10px 0;"></div>
                
                {''.join([f'''
                <div style="background: {'#FFD700' if i == 0 and step < 7 else '#2D2D2D'}; 
                           border-radius: 10px; 
                           padding: 15px; 
                           margin: 10px 0;
                           border: 2px solid {'#FFD700' if i == 0 and step < 7 else '#666'};
                           transition: all 0.3s;">
                    <h4 style="color: {'#000' if i == 0 and step < 7 else '#FFD700'}; margin: 0 0 10px 0;">
                        {obj['name']}
                        {f'<span style="float: right; font-size: 12px;">⚡ CREATING</span>' if i == 0 and 1 <= step <= 6 else ''}
                        {f'<span style="float: right; font-size: 12px; color: #4CAF50;">✓ CREATED</span>' if i == 0 and step >= 7 else ''}
                    </h4>
                    <table style="width: 100%; color: {'#000' if i == 0 and step < 7 else '#fff'};">
                        <tr>
                            <th>Member</th>
                            <th>Value</th>
                            <th>Status</th>
                        </tr>
                        {''.join([f'''
                        <tr>
                            <td>{private_members[j] if j < len(private_members) else 'member'}</td>
                            <td>{obj['params'][j] if j < len(obj['params']) else '...'}</td>
                            <td>
                                {f'✅' if step > j + 3 and i == 0 else '○'}
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
            <div style="display: flex; justify-content: center; gap: 30px; margin-bottom: 20px;">
                {''.join([f'<div class="parameter-tag">{param}: {obj["params"][i] if i < len(obj["params"]) else "..."}</div>' 
                         for i, param in enumerate(constructor_params)])}
            </div>
            <div class="arrow">⬇️ ⬇️ ⬇️</div>
            <div style="margin-top: 20px; padding: 15px; background: #4CAF50; border-radius: 10px; color: white;">
                📍 Parameters moving to constructor...
            </div>
        </div>
        ''' if 2 <= step <= 3 else ''}
        
        <!-- Control Flow Indicator -->
        {f'''
        <div style="margin-top: 20px; padding: 15px; background: {'#FFD700' if step < 2 else '#4CAF50'}; 
                    border-radius: 10px; text-align: center; font-weight: bold;">
            {'⚡ Control in main()' if step < 2 or step > 6 else '🔧 Control in Constructor'}
        </div>
        ''' if step > 0 else ''}
    </div>
    """
    
    return html

def main():
    # Header with animation
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.2);">
        <h1 style="color: white; font-size: 48px; margin: 0;">🎮 C++ Constructor Visualizer</h1>
        <p style="color: #FFD700; font-size: 20px; margin: 10px 0 0 0;">
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
        progress_text = f"Step {st.session_state.step + 1}/10"
        st.progress((st.session_state.step + 1) / 10, text=progress_text)
        
        # Animation display
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
    <div style="text-align: center; color: #666; padding: 20px;">
        Made with ❤️ for C++ Students | Step-by-Step Constructor Visualization
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
