import streamlit as st
import pygame
import base64
from io import BytesIO
import tempfile
import os
import sys
from pathlib import Path
import time
import re

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.code_parser import CPPCodeParser
from utils.animation_generator import AnimationGenerator

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
        padding: 10px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'animation_generated' not in st.session_state:
    st.session_state.animation_generated = False
if 'animation_path' not in st.session_state:
    st.session_state.animation_path = None
if 'parsed_code' not in st.session_state:
    st.session_state.parsed_code = None

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
        
        **Code Requirements:**
        - Must contain a class with constructor
        - Constructor should be parameterized
        - Class should have private members
        - Include main() function with object creation
        
        **Example Structure:**
        ```cpp
        class Student {
        private:
            string name;
            int age;
        public:
            Student(string n, int a) {
                name = n;
                age = a;
            }
        };
        
        int main() {
            Student s1("John", 20);
            return 0;
        }
        ```
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
    // Parameterized constructor
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
    // Create student objects
    Student student1("Ali Raza", 20, "Computer Science");
    student1.display();
    
    Student student2("Hassan Ali", 22, "Electrical Engineering");
    student2.display();
    
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
    // Parameterized constructor
    Rectangle(double l, double w) {
        length = l;
        width = w;
    }
    
    double area() {
        return length * width;
    }
    
    void display() {
        cout << "Length: " << length << ", Width: " << width << endl;
        cout << "Area: " << area() << endl;
    }
};

int main() {
    Rectangle rect1(5.0, 3.0);
    rect1.display();
    
    Rectangle rect2(7.5, 4.2);
    rect2.display();
    
    return 0;
}'''
            st.session_state['sample_code'] = sample_code
            st.rerun()

    # Main content area
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📝 Enter Your C++ Code")
        
        # Code input area
        default_code = st.session_state.get('sample_code', '''#include <iostream>
#include <string>
using namespace std;

class Student {
private:
    string name;
    int age;
    string major;
    
public:
    // Parameterized constructor
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
            height=400,
            key="code_input"
        )
        
        # Buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            generate_btn = st.button("🎬 Generate Animation", use_container_width=True)
        with col_btn2:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.animation_generated = False
                st.rerun()
        with col_btn3:
            if st.button("💾 Save Code", use_container_width=True):
                st.success("Code saved temporarily!")
    
    with col2:
        st.subheader("📊 Code Analysis")
        
        if cpp_code and generate_btn:
            with st.spinner("🔍 Analyzing your code..."):
                # Parse the C++ code
                parser = CPPCodeParser()
                parsed_data = parser.parse(cpp_code)
                st.session_state.parsed_code = parsed_data
                
                if parsed_data['error']:
                    st.error(f"❌ Error parsing code: {parsed_data['error']}")
                else:
                    # Display parsed information
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.success("✅ Code parsed successfully!")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Class info
                    st.markdown("### 📌 Class Information")
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.metric("Class Name", parsed_data['class_name'])
                        st.metric("Constructor Parameters", len(parsed_data['constructor_params']))
                    with col_info2:
                        st.metric("Private Members", len(parsed_data['private_members']))
                        st.metric("Objects Found", len(parsed_data['objects']))
                    
                    # Private members
                    if parsed_data['private_members']:
                        st.markdown("### 🔒 Private Members")
                        for member in parsed_data['private_members']:
                            st.markdown(f"- `{member}`")
                    
                    # Objects to create
                    if parsed_data['objects']:
                        st.markdown("### 🎯 Objects to Create")
                        for i, obj in enumerate(parsed_data['objects'], 1):
                            st.markdown(f"**{i}. {obj['name']}**")
                            for param_name, param_value in zip(parsed_data['constructor_params'], obj['params']):
                                st.markdown(f"   - {param_name}: `{param_value}`")
                    
                    # Generate animation button
                    if st.button("▶️ Generate Animation Now", use_container_width=True):
                        st.session_state.animation_generated = True
    
    # Animation display section
    if st.session_state.get('animation_generated', False) and st.session_state.parsed_code:
        st.markdown("---")
        st.subheader("🎬 Animation Player")
        
        # Animation controls
        col_anim1, col_anim2, col_anim3, col_anim4, col_anim5 = st.columns(5)
        with col_anim1:
            st.button("⏮️ First", use_container_width=True)
        with col_anim2:
            st.button("⏪ Previous", use_container_width=True)
        with col_anim3:
            st.button("▶️ Play/Pause", use_container_width=True)
        with col_anim4:
            st.button("⏩ Next", use_container_width=True)
        with col_anim5:
            st.button("⏭️ Last", use_container_width=True)
        
        # Progress bar
        st.progress(0.3, text="Step 3 of 10: Parameters being passed...")
        
        # Animation display area
        st.markdown('<div class="animation-container">', unsafe_allow_html=True)
        
        # Create columns for animation layout
        anim_col1, anim_col2 = st.columns([1, 1])
        
        with anim_col1:
            st.markdown("#### 📦 Class Structure")
            
            # Display class structure based on parsed data
            parsed = st.session_state.parsed_code
            
            # Class box
            st.markdown(f"""
            <div style="
                border: 3px solid #4CAF50;
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                background-color: #1E1E1E;
            ">
                <h4 style="color: #4CAF50; margin-top: 0;">{parsed['class_name']} Class</h4>
                <div style="color: #FF6B6B;">
                    <strong>private:</strong><br>
                    {''.join([f'&nbsp;&nbsp;- {member}<br>' for member in parsed['private_members']])}
                </div>
                <div style="color: #6BFF6B; margin-top: 10px;">
                    <strong>public:</strong><br>
                    &nbsp;&nbsp;+ {parsed['class_name']}({', '.join(parsed['constructor_params'])})<br>
                    &nbsp;&nbsp;+ display()
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with anim_col2:
            st.markdown("#### 🎯 Objects")
            
            # Display objects with initialization status
            for i, obj in enumerate(parsed['objects']):
                if i == 0:  # Highlight current object
                    status_color = "#FFD700"
                    border = "3px solid #FFD700"
                else:
                    status_color = "#FFFFFF"
                    border = "2px solid #666"
                
                st.markdown(f"""
                <div style="
                    border: {border};
                    border-radius: 10px;
                    padding: 15px;
                    margin: 10px 0;
                    background-color: #2D2D2D;
                ">
                    <h5 style="color: {status_color}; margin-top: 0;">{obj['name']}</h5>
                    <table style="width: 100%; color: #FFFFFF;">
                        <tr>
                            <th>Member</th>
                            <th>Value</th>
                            <th>Status</th>
                        </tr>
                        {''.join([f'''
                        <tr>
                            <td>{parsed['private_members'][j]}</td>
                            <td>{obj['params'][j]}</td>
                            <td>{"✅ Initialized" if j < 2 else "⏳ Pending"}</td>
                        </tr>
                        ''' for j in range(min(3, len(parsed['private_members'])))])}
                    </table>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Current step explanation
        st.info("""
        **Current Step:** Parameters are being passed to the constructor.
        - Control has transferred from main() to the constructor
        - Parameters are being received: name, age, major
        - Next: Private members will be initialized
        """)
    
    # Footer
    st.markdown("---")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f2:
        st.markdown("Made with ❤️ for C++ Students")

if __name__ == "__main__":
    main()