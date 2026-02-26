import streamlit as st
import streamlit.components.v1 as components
import re
import time

# Page configuration
st.set_page_config(
    page_title="C++ Constructor Visualizer",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- PAGE (STREAMLIT) CSS ----------
st.markdown("""
<style>
    /* Main container styles */
    .main-title {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 20px 30px rgba(0,0,0,0.3);
    }
    .main-title h1 {
        color: white;
        font-size: 52px;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .main-title p {
        color: #FFD700;
        font-size: 24px;
        margin: 10px 0 0 0;
        font-weight: bold;
    }

    /* Button styles */
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

    /* Text area styles */
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
        font-size: 14px;
        border: 3px solid #4CAF50;
        border-radius: 10px;
        background: #1E1E1E;
        color: #FFD700;
    }

    /* Success box */
    .success-box {
        padding: 20px;
        border-radius: 15px;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 3px solid #28a745;
        color: #155724;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        font-size: 16px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #888;
        padding: 20px;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None
if 'auto_play' not in st.session_state:
    st.session_state.auto_play = False
if 'show_animation' not in st.session_state:
    st.session_state.show_animation = False
if 'sample' not in st.session_state:
    st.session_state.sample = None


class CPPCodeParser:
    def __init__(self):
        self.class_name = ""
        self.private_members = []
        self.constructor_params = []
        self.objects = []
        self.error = None

    def parse(self, code: str):
    try:
        # Reset
        self.class_name = ""
        self.private_members = []
        self.constructor_params = []
        self.objects = []
        self.error = None

        # 1) Remove comments (so // and /* */ don't break regex)
        code_no_comments = re.sub(r'//.*', '', code)
        code_no_comments = re.sub(r'/\*.*?\*/', '', code_no_comments, flags=re.DOTALL)

        # 2) Extract class name
        class_match = re.search(r'\bclass\s+(\w+)\b', code_no_comments)
        if not class_match:
            return {"error": "No class found. Please include a C++ class definition."}
        self.class_name = class_match.group(1)

        # 3) Extract private members (simple: type name;)
        private_section = re.search(r'private:\s*(.*?)(?=public:|protected:|};)', code_no_comments, re.DOTALL)
        if private_section:
            private_text = private_section.group(1)
            # allow types like: unsigned int count;
            members = re.findall(r'\b([\w:<>]+(?:\s+[\w:<>]+)*)\s+(\w+)\s*;', private_text)
            self.private_members = [name for _typ, name in members]

        # 4) Extract constructor parameters:
        # Match: ClassName( ... ) { ... }
        # Also match: ClassName( ... ) : initlist { ... }
        ctor_match = re.search(
            rf'\b{re.escape(self.class_name)}\s*\((.*?)\)\s*(?::[^\{{]]*)?\{{',
            code_no_comments,
            re.DOTALL
        )
        if ctor_match:
            params_text = ctor_match.group(1).strip()
            if params_text:
                raw_params = [p.strip() for p in params_text.split(",")]
                params = []
                for p in raw_params:
                    p = p.split("=")[0].strip()  # remove default values
                    # pick last identifier as param name
                    m = re.findall(r'(\w+)\s*$', p)
                    if m:
                        params.append(m[-1])
                self.constructor_params = params
            else:
                self.constructor_params = []
        else:
            self.constructor_params = []

        # 5) Extract objects created inside main()
        main_match = re.search(r'\bint\s+main\s*\([^)]*\)\s*\{(.*)\}\s*$', code_no_comments, re.DOTALL)
        if main_match:
            main_body = main_match.group(1)

            # 5a) Pattern A: ClassName obj(arg1, arg2);
            pat_params = rf'\b{re.escape(self.class_name)}\s+(\w+)\s*\((.*?)\)\s*;'
            for obj_name, params_str in re.findall(pat_params, main_body, re.DOTALL):
                raw = [p.strip() for p in params_str.split(",")] if params_str.strip() else []
                cleaned = [p.strip().strip('"').strip("'") for p in raw]
                self.objects.append({"name": obj_name, "params": cleaned})

            # 5b) Pattern B: ClassName a, b, c;
            # But NOT when it already matched Pattern A (those have parentheses)
            # We'll scan statements ending with ';'
            stmt_pat = rf'\b{re.escape(self.class_name)}\s+([^;]+);'
            for decl in re.findall(stmt_pat, main_body):
                # skip if it contains '(' because that is Pattern A
                if '(' in decl or ')' in decl:
                    continue

                # decl example: "c1, c2" or "c1 = something, c2"
                parts = [p.strip() for p in decl.split(",")]
                for part in parts:
                    # capture name before optional = initializer
                    m = re.match(r'^(\w+)\b', part)
                    if m:
                        name = m.group(1)
                        # avoid duplicates (if any)
                        if not any(o["name"] == name for o in self.objects):
                            self.objects.append({"name": name, "params": []})

        return {
            "class_name": self.class_name,
            "private_members": self.private_members,
            "constructor_params": self.constructor_params,
            "objects": self.objects,
            "error": None
        }

    except Exception as e:
        return {"error": str(e)}


def create_animation_html(step: int, parsed_data: dict) -> str:
    """Return FULL HTML (with CSS) for components.html() rendering."""
    if not parsed_data or parsed_data.get("error"):
        return "<div style='color:red;padding:20px;font-family:sans-serif;'>No valid data to display</div>"

    class_name = parsed_data.get("class_name", "Student")
    private_members = parsed_data.get("private_members", ["name", "age", "major"])
    constructor_params = parsed_data.get("constructor_params", ["n", "a", "m"])
    objects = parsed_data.get("objects", []) or [{"name": "student1", "params": ["Ali Raza", "20", "Computer Science"]}]

    step_texts = [
        "📌 main() calls constructor",
        "⚡ Control transfers to constructor",
        "📦 Parameters are being passed",
        f"🔧 Initializing: {private_members[0] if private_members else 'member1'}",
        f"🔧 Initializing: {private_members[1] if len(private_members) > 1 else 'member2'}",
        f"🔧 Initializing: {private_members[2] if len(private_members) > 2 else 'member3'}",
        "✅ Constructor completes",
        "🔄 Control returns to main()",
        "📢 display() method called",
        "🎉 Object successfully created!"
    ]
    current_text = step_texts[step] if step < len(step_texts) else "Complete!"

    # build private members html
    private_members_html = "".join([f'<div class="private-member">• {m}</div>' for m in private_members])

    # constructor body (assignment view)
    constructor_body_html = ""
    if 2 <= step <= 6:
        constructor_body_html += """
        <div class="ctor-box">
            <h4 class="ctor-title">⚙️ Constructor Execution:</h4>
        """
        for i, member in enumerate(private_members):
            if i < len(constructor_params):
                constructor_body_html += f'<div class="ctor-line">{member} = {constructor_params[i]};</div>'
        constructor_body_html += "</div>"

    # objects html
    objects_html = ""
    for i, obj in enumerate(objects):
        active = (i == 0 and step < 7)
        bg = "#FFD700" if active else "#363636"
        text = "black" if active else "#FFD700"
        border = "#FFD700" if active else "#666"
        value_color = "black" if active else "white"

        status_badge = ""
        if i == 0:
            if 1 <= step <= 6:
                status_badge = '<span class="status-badge creating-badge">⚡ CREATING</span>'
            elif step >= 7:
                status_badge = '<span class="status-badge created-badge">✓ CREATED</span>'

        table_rows = ""
        for j in range(min(3, len(private_members))):
            value = obj["params"][j] if j < len(obj["params"]) else "..."
            init_done = (step > j + 3 and i == 0)
            status_class = "init-check" if init_done else "init-pending"
            status_text = "✓ Initialized" if init_done else "○ Pending"

            table_rows += f"""
            <tr>
                <td style="color:{text};">{private_members[j]}</td>
                <td style="color:{value_color};">{value}</td>
                <td><span class="{status_class}">{status_text}</span></td>
            </tr>
            """

        objects_html += f"""
        <div class="obj-card" style="background:{bg};border:2px solid {border};">
            <div class="obj-title" style="color:{text};">
                <span>{obj["name"]}</span>
                {status_badge}
            </div>
            <table class="member-table">
                <thead>
                    <tr><th>Member</th><th>Value</th><th>Status</th></tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """

    # parameter flow
    parameter_html = ""
    if 2 <= step <= 3 and objects:
        pills = ""
        for i, param in enumerate(constructor_params):
            if i < len(objects[0]["params"]):
                pills += f'<div class="parameter-pill">{param}: {objects[0]["params"][i]}</div>'
        parameter_html = f"""
        <div class="param-area">
            <div class="param-row">{pills}</div>
            <div class="arrow-animation">⬇️ ⬇️ ⬇️ PARAMETERS FLOWING TO CONSTRUCTOR ⬇️ ⬇️ ⬇️</div>
        </div>
        """

    # control flow
    control_html = ""
    if step > 0:
        control_text = "⚡ CONTROL IN main() FUNCTION" if (step < 2 or step > 6) else "🔧 CONTROL INSIDE CONSTRUCTOR"
        control_html = f'<div class="control-flow">{control_text}</div>'

    # IMPORTANT: Include CSS INSIDE this HTML because components.html() is an iframe.
    html = f"""
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        body {{
          margin: 0;
          font-family: 'Segoe UI', Arial, sans-serif;
          color: white;
        }}

        .wrapper {{
          border: 4px solid #4CAF50;
          border-radius: 20px;
          padding: 25px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          box-shadow: 0 20px 30px rgba(0,0,0,0.3);
        }}

        .step-badge {{
          background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
          color: black;
          padding: 15px 25px;
          border-radius: 50px;
          font-weight: bold;
          font-size: 22px;
          text-align: center;
          margin-bottom: 20px;
          border: 2px solid white;
        }}

        .grid {{
          display: flex;
          gap: 25px;
          margin-top: 10px;
        }}

        .class-box {{
          background: #1E1E1E;
          border-radius: 15px;
          padding: 20px;
          border: 3px solid #4CAF50;
          box-shadow: 0 5px 15px rgba(0,0,0,0.3);
          flex: 1;
        }}

        .object-box {{
          background: #2D2D2D;
          border-radius: 15px;
          padding: 20px;
          border: 3px solid #FFD700;
          box-shadow: 0 5px 15px rgba(0,0,0,0.3);
          flex: 1;
        }}

        .private-member {{
          color: #FF6B6B;
          font-size: 16px;
          margin: 8px 0;
          padding-left: 10px;
          font-family: 'Courier New', monospace;
        }}

        .public-member {{
          color: #6BFF6B;
          font-size: 16px;
          margin: 8px 0;
          padding-left: 10px;
          font-family: 'Courier New', monospace;
        }}

        .ctor-box {{
          margin-top: 20px;
          padding: 15px;
          background: #2D2D2D;
          border-radius: 10px;
          border-left: 5px solid #FFD700;
        }}
        .ctor-title {{ color:#FFD700; margin:0 0 10px 0; }}
        .ctor-line {{
          color: white;
          font-family: monospace;
          margin: 5px 0;
        }}

        .obj-card {{
          border-radius: 12px;
          padding: 15px;
          margin: 15px 0;
          transition: all 0.3s;
        }}
        .obj-title {{
          font-size: 20px;
          font-weight: 700;
          display:flex;
          justify-content: space-between;
          align-items:center;
          margin-bottom: 10px;
        }}

        .status-badge {{
          padding: 5px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 700;
        }}
        .creating-badge {{ background:#FFD700; color:black; }}
        .created-badge {{ background:#4CAF50; color:white; }}

        .member-table {{
          width: 100%;
          border-collapse: collapse;
        }}
        .member-table th {{
          color: #FFD700;
          text-align: left;
          padding: 8px;
          border-bottom: 2px solid #FFD700;
        }}
        .member-table td {{
          padding: 8px;
          border-bottom: 1px solid #444;
        }}
        .init-check {{ color:#4CAF50; font-weight: 800; }}
        .init-pending {{ color:#BBB; }}

        .param-area {{ margin-top: 25px; text-align:center; }}
        .param-row {{
          display:flex;
          justify-content:center;
          gap: 20px;
          flex-wrap: wrap;
          margin-bottom: 10px;
        }}
        .parameter-pill {{
          background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
          color: white;
          padding: 10px 18px;
          border-radius: 30px;
          font-weight: bold;
          font-size: 16px;
          border: 2px solid white;
          box-shadow: 0 5px 10px rgba(0,0,0,0.2);
          animation: bounce 1s infinite;
        }}
        @keyframes bounce {{
          0%,100% {{ transform: translateY(0); }}
          50% {{ transform: translateY(-8px); }}
        }}

        .arrow-animation {{
          font-size: 18px;
          color: #FFD700;
          font-weight: 800;
          margin-top: 6px;
        }}

        .control-flow {{
          background: #2D2D2D;
          padding: 12px;
          border-radius: 50px;
          text-align: center;
          font-weight: bold;
          font-size: 18px;
          margin-top: 20px;
          border: 3px solid #FFD700;
          color: #FFD700;
        }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="step-badge">Step {step + 1}/10: {current_text}</div>

        <div class="grid">
          <div class="class-box">
            <h2 style="color:#4CAF50;margin-top:0;border-bottom:2px solid #4CAF50;padding-bottom:10px;">📦 {class_name} Class</h2>

            <div style="margin:20px 0;">
              <h3 style="color:#FF6B6B;margin:10px 0;">🔒 Private Members:</h3>
              {private_members_html}
            </div>

            <div style="margin:20px 0;">
              <h3 style="color:#6BFF6B;margin:10px 0;">🔓 Public Methods:</h3>
              <div class="public-member">+ {class_name}({', '.join(constructor_params)})</div>
              <div class="public-member">+ display()</div>
            </div>

            {constructor_body_html}
          </div>

          <div class="object-box">
            <h2 style="color:#FFD700;margin-top:0;border-bottom:2px solid #FFD700;padding-bottom:10px;">🎯 Objects</h2>
            {objects_html}
          </div>
        </div>

        {parameter_html}
        {control_html}
      </div>
    </body>
    </html>
    """
    return html


def main():
    # Header
    st.markdown("""
    <div class="main-title">
        <h1>🎮 C++ Constructor Visualizer</h1>
        <p>Visualize Parameterized Constructors Step by Step</p>
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
            st.session_state.sample = '''#include <iostream>
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
            st.rerun()

    # Main content
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("### 📝 Enter Your C++ Code")

        default_code = st.session_state.sample or '''#include <iostream>
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

        cpp_code = st.text_area(
            "##",
            value=default_code,
            height=300,
            key="code_input",
            label_visibility="collapsed"
        )

        if st.button("🎬 Generate Animation", use_container_width=True):
            parser = CPPCodeParser()
            parsed = parser.parse(cpp_code)
            st.session_state.parsed_data = parsed
            st.session_state.step = 0
            st.session_state.auto_play = False
            st.session_state.show_animation = True

    with col2:
        st.markdown("### 📊 Analysis")
        if st.session_state.parsed_data and not st.session_state.parsed_data.get("error"):
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
        elif st.session_state.parsed_data and st.session_state.parsed_data.get("error"):
            st.error(f"❌ {st.session_state.parsed_data['error']}")

    # Animation Player
    if st.session_state.show_animation and st.session_state.parsed_data and not st.session_state.parsed_data.get("error"):
        st.markdown("---")
        st.markdown("## 🎬 Animation Player")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("⏮️ First", use_container_width=True):
                st.session_state.step = 0
                st.session_state.auto_play = False
                st.rerun()
        with c2:
            if st.button("⏪ Prev", use_container_width=True):
                st.session_state.step = max(0, st.session_state.step - 1)
                st.session_state.auto_play = False
                st.rerun()
        with c3:
            play_text = "⏸️ Pause" if st.session_state.auto_play else "▶️ Play"
            if st.button(play_text, use_container_width=True):
                st.session_state.auto_play = not st.session_state.auto_play
                st.rerun()
        with c4:
            if st.button("⏩ Next", use_container_width=True):
                st.session_state.step = min(9, st.session_state.step + 1)
                st.session_state.auto_play = False
                st.rerun()
        with c5:
            if st.button("⏭️ Last", use_container_width=True):
                st.session_state.step = 9
                st.session_state.auto_play = False
                st.rerun()

        st.progress((st.session_state.step + 1) / 10, text=f"**Step {st.session_state.step + 1}/10**")

        # ✅ Render animation HTML correctly (no raw HTML text)
        html_anim = create_animation_html(st.session_state.step, st.session_state.parsed_data)
        components.html(html_anim, height=720, scrolling=True)

        # Auto-play
        if st.session_state.auto_play:
            if st.session_state.step < 9:
                time.sleep(1.2)
                st.session_state.step += 1
                st.rerun()
            else:
                st.session_state.auto_play = False
                st.balloons()

    st.markdown("---")
    st.markdown("""
    <div class="footer">
        Made with ❤️ for C++ Students | Step-by-Step Constructor Visualization
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

