import streamlit as st
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

# Initialize session state
if 'animation_generated' not in st.session_state:
    st.session_state.animation_generated = False
if 'parsed_code' not in st.session_state:
    st.session_state.parsed_code = None


def main():
    st.title("🎮 C++ Constructor Visualizer")
    st.markdown("### Visualize Parameterized Constructors Step by Step")

    # Sidebar
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. Paste your C++ code
        2. Click Generate Animation
        3. View parsed constructor data
        """)

    # Layout
    col1, col2 = st.columns([3, 2])

    # ---------------- LEFT SIDE ----------------
    with col1:
        st.subheader("📝 Enter Your C++ Code")

        default_code = """#include <iostream>
#include <string>
using namespace std;

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
    Student s1("Ali", 20);
    return 0;
}"""

        cpp_code = st.text_area(
            "Paste your C++ code here:",
            value=default_code,
            height=400
        )

        if st.button("🎬 Generate Animation"):
            parser = CPPCodeParser()
            parsed_data = parser.parse(cpp_code)

            if parsed_data.get("error"):
                st.error(f"Error: {parsed_data['error']}")
            else:
                st.session_state.parsed_code = parsed_data
                st.session_state.animation_generated = True

    # ---------------- RIGHT SIDE ----------------
    with col2:
        st.subheader("📊 Code Analysis")

        if st.session_state.animation_generated and st.session_state.parsed_code:
            parsed = st.session_state.parsed_code

            st.success("✅ Code Parsed Successfully!")

            st.metric("Class Name", parsed.get("class_name", "N/A"))
            st.metric("Constructor Parameters", len(parsed.get("constructor_params", [])))
            st.metric("Private Members", len(parsed.get("private_members", [])))
            st.metric("Objects Found", len(parsed.get("objects", [])))

            if parsed.get("private_members"):
                st.markdown("### 🔒 Private Members")
                for member in parsed["private_members"]:
                    st.write(f"- {member}")

            if parsed.get("objects"):
                st.markdown("### 🎯 Objects Created")
                for obj in parsed["objects"]:
                    st.write(f"**{obj['name']}**")
                    for p in obj["params"]:
                        st.write(f"• {p}")

    # ---------------- Animation Section ----------------
    if st.session_state.animation_generated and st.session_state.parsed_code:
        st.markdown("---")
        st.subheader("🎬 Visualization")

        parsed = st.session_state.parsed_code

        st.info(
            f"Constructor of class '{parsed.get('class_name')}' "
            f"is called with parameters: {parsed.get('constructor_params')}"
        )


if __name__ == "__main__":
    main()
