import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import base64
from io import BytesIO
import sys
from pathlib import Path
import re
import numpy as np

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.code_parser import CPPCodeParser

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
    }
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
        font-size: 14px;
    }
    .success-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .animation-container {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        background-color: white;
    }
    .class-box {
        border: 3px solid #4CAF50;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #1E1E1E;
        color: white;
    }
    .object-box {
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #2D2D2D;
        color: white;
    }
    .parameter-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 10px;
        border-radius: 8px;
        color: white;
        text-align: center;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'animation_generated' not in st.session_state:
    st.session_state.animation_generated = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'parsed_code' not in st.session_state:
    st.session_state.parsed_code = None
if 'auto_play' not in st.session_state:
    st.session_state.auto_play = False

def create_animation_frame(step, parsed_data):
    """Create matplotlib animation frame"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#f0f2f6')
    
    # Left side - Class structure
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 8)
    ax1.set_facecolor('#1E1E1E')
    ax1.axis('off')
    
    # Draw class box
    class_rect = patches.Rectangle((1, 3), 4, 3, 
                                  linewidth=3, 
                                  edgecolor='#4CAF50', 
                                  facecolor='#2D2D2D')
    ax1.add_patch(class_rect)
    ax1.text(2, 5.5, f'{parsed_data["class_name"]} Class', 
             color='white', fontsize=14, fontweight='bold')
    
    # Private members
    y_pos = 4.5
    ax1.text(1.5, y_pos, 'private:', color='#FF6B6B', fontsize=10, fontweight='bold')
    for i, member in enumerate(parsed_data['private_members']):
        ax1.text(2, y_pos - 0.5 - i*0.4, f'• {member}', color='#FF6B6B', fontsize=9)
    
    # Public members
    ax1.text(1.5, 2.8, 'public:', color='#6BFF6B', fontsize=10, fontweight='bold')
    ax1.text(2, 2.4, f'+ {parsed_data["class_name"]}({", ".join(parsed_data["constructor_params"])})', 
             color='#6BFF6B', fontsize=8)
    ax1.text(2, 2.0, '+ display()', color='#6BFF6B', fontsize=8)
    
    # Right side - Objects
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 8)
    ax2.set_facecolor('#1E1E1E')
    ax2.axis('off')
    
    # Draw objects based on step
    for i, obj in enumerate(parsed_data['objects']):
        y_offset = 5 - i * 2.5
        color = '#FFD700' if i == 0 and step < 7 else '#4CAF50'
        
        # Object box
        obj_rect = patches.Rectangle((1, y_offset-1), 4, 1.5,
                                    linewidth=2 if i != 0 or step >= 7 else 3,
                                    edgecolor=color,
                                    facecolor='#2D2D2D')
        ax2.add_patch(obj_rect)
        ax2.text(1.5, y_offset-0.3, obj['name'], color='white', fontsize=12, fontweight='bold')
        
        # Show initialization status
        if i == 0:  # Current object
            for j, (member, param) in enumerate(zip(parsed_data['private_members'], obj['params'])):
                if step > j + 3:  # Members initialized in steps 4-6
                    ax2.text(1.5, y_offset-0.8 - j*0.3, 
                            f'✓ {member} = {param}', 
                            color='#6BFF6B', fontsize=8)
                else:
                    ax2.text(1.5, y_offset-0.8 - j*0.3, 
                            f'○ {member} = ...', 
                            color='#888888', fontsize=8)
    
    # Parameter passing animation
    if 2 <= step <= 3:
        arrow_props = dict(arrowstyle='->', color='yellow', lw=2)
        ax1.annotate('', xy=(4.5, 4.5), xytext=(7, 5.5),
                    arrowprops=arrow_props)
        ax1.text(6, 5.8, 'Parameters →', color='yellow', fontsize=10)
    
    # Control flow indicator
    if step == 1:
        fig.suptitle('⚡ Control transfers to Constructor', fontsize=16, color='#FFD700', fontweight='bold')
    elif step == 2:
        fig.suptitle('📦 Parameters being passed', fontsize=16, color='#FFD700', fontweight='bold')
    elif step == 3:
        fig.suptitle('🔧 Initializing private members', fontsize=16, color='#FFD700', fontweight='bold')
    elif step == 7:
        fig.suptitle('✅ Object Created! Control returns to main()', fontsize=16, color='#4CAF50', fontweight='bold')
    
    plt.tight_layout()
    
    # Convert to base64
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return base64.b64encode(buf.getvalue()).decode()

def main():
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🎮 C++ Constructor Visualizer")
        st.markdown("### Visualize Parameterized Constructors Step by Step")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Paste your C++ code** in the text area
        2. **Click 'Generate Animation'** button
        3. **Watch the step-by-step** visualization
        4. **Use controls** to navigate through steps
        """)
        
        st.markdown("---")
        st.header("🎯 Sample Codes")
        
        if st.button("📚 Student Class Example"):
            sample_code = '''#include <iostream>
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
}'''
            st.session_state['sample_code'] = sample_code
            st.rerun()
        
        if st.button("📐 Rectangle Class Example"):
            sample_code = '''#include <iostream>
using namespace std;

class Rectangle {
private:
    double length;
    double width;
    
public:
    Rectangle(double l, double w) {
        length = l;
        width = w;
    }
    
    double area() {
        return length * width;
    }
};

int main() {
    Rectangle rect1(5.0, 3.0);
    return 0;
}'''
            st.session_state['sample_code'] = sample_code
            st.rerun()

    # Main content area
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📝 Enter Your C++ Code")
        
        default_code = st.session_state.get('sample_code', '''#include <iostream>
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
            "Paste your C++ code here:",
            value=default_code,
            height=300,
            key="code_input"
        )
        
        if st.button("🎬 Generate Animation", use_container_width=True):
            with st.spinner("🔍 Analyzing your code..."):
                parser = CPPCodeParser()
                parsed_data = parser.parse(cpp_code)
                st.session_state.parsed_code = parsed_data
                st.session_state.animation_generated = True
                st.session_state.current_step = 0
    
    with col2:
        st.subheader("📊 Code Analysis")
        
        if st.session_state.parsed_code:
            parsed = st.session_state.parsed_code
            
            if parsed.get('error'):
                st.error(f"❌ {parsed['error']}")
            else:
                st.success("✅ Code parsed successfully!")
                
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.metric("Class Name", parsed.get('class_name', 'N/A'))
                    st.metric("Constructor Params", len(parsed.get('constructor_params', [])))
                with col_info2:
                    st.metric("Private Members", len(parsed.get('private_members', [])))
                    st.metric("Objects Found", len(parsed.get('objects', [])))
    
    # Animation display
    if st.session_state.animation_generated and st.session_state.parsed_code:
        st.markdown("---")
        st.subheader("🎬 Animation Player")
        
        # Animation controls
        col_anim1, col_anim2, col_anim3, col_anim4, col_anim5 = st.columns(5)
        with col_anim1:
            if st.button("⏮️ First", use_container_width=True):
                st.session_state.current_step = 0
        with col_anim2:
            if st.button("⏪ Previous", use_container_width=True):
                st.session_state.current_step = max(0, st.session_state.current_step - 1)
        with col_anim3:
            if st.button("▶️ Play", use_container_width=True):
                st.session_state.auto_play = not st.session_state.auto_play
        with col_anim4:
            if st.button("⏩ Next", use_container_width=True):
                st.session_state.current_step = min(9, st.session_state.current_step + 1)
        with col_anim5:
            if st.button("⏭️ Last", use_container_width=True):
                st.session_state.current_step = 9
        
        # Progress bar
        step_names = [
            "Main() calls constructor",
            "Control transfers to constructor",
            "Parameters being passed",
            "Initializing name",
            "Initializing age",
            "Initializing major",
            "Constructor completes",
            "Control returns to main()",
            "display() called",
            "Output displayed"
        ]
        
        st.progress((st.session_state.current_step + 1) / 10, 
                   text=f"Step {st.session_state.current_step + 1}/10: {step_names[st.session_state.current_step]}")
        
        # Generate and display animation frame
        img_base64 = create_animation_frame(
            st.session_state.current_step, 
            st.session_state.parsed_code
        )
        
        st.markdown('<div class="animation-container">', unsafe_allow_html=True)
        st.image(f"data:image/png;base64,{img_base64}", use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Auto-play logic
        if st.session_state.auto_play:
            if st.session_state.current_step < 9:
                time.sleep(1.5)
                st.session_state.current_step += 1
                st.rerun()
            else:
                st.session_state.auto_play = False

if __name__ == "__main__":
    main()
