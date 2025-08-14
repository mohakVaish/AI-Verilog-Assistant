import os
import re
import json
import streamlit as st
from graphviz import Digraph
from dotenv import load_dotenv



load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

try:
    import google.generativeai as genai
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    GOOGLE_AI_AVAILABLE = True if GOOGLE_API_KEY else False
except ImportError:
    GOOGLE_AI_AVAILABLE = False

def get_module_code(module_name: str, full_verilog_text: str) -> str:
    """Extracts the full text of a single Verilog module from a file."""
    module_regex = re.compile(
        r'^\s*module\s+' + re.escape(module_name) + r'[\s\S]*?endmodule',
        re.DOTALL | re.MULTILINE
    )
    match = module_regex.search(full_verilog_text)
    return match.group(0) if match else None

def get_module_names(verilog_text: str) -> list:
    """Finds all module names in a Verilog file."""
    return re.findall(r'^\s*module\s+(\w+)', verilog_text, re.MULTILINE)

def get_ports_for_testbench(module_name: str, verilog_text: str) -> tuple:
    """Extracts detailed input/output ports for a specific module."""
    try:
        module_regex = re.compile(r'module\s+' + re.escape(module_name) + r'\s*#?\s*\(([\s\S]*?)\);', re.DOTALL | re.IGNORECASE)
        module_match = module_regex.search(verilog_text)
        if not module_match: return [], []

        ports_text = module_match.group(1)
        inputs, outputs = [], []

        port_regex = re.compile(r'(input|output)\s*(?:reg|wire)?\s*(\[[^\]]+\])?\s*([\w\s,]+?)(?=(?:,?\s*(?:input|output|inout|$)))')

        for p_type, p_width, p_names in port_regex.findall(ports_text + "\n"):
            names = [name.strip() for name in p_names.strip().split(',') if name.strip()]
            for name in names:
                port_info = f"{p_width.strip() if p_width else ''} {name}"
                if p_type == 'input':
                    inputs.append(port_info.strip())
                else:
                    outputs.append(port_info.strip())
        return inputs, outputs
    except Exception:
        return [], []

def ask_gemini_for_gate_level_netlist(module_code: str) -> dict:
    """Asks Gemini to synthesize Verilog into a detailed, gate-level JSON netlist."""
    if not GOOGLE_AI_AVAILABLE:
        return {"error": "Google AI is not configured. Please set GOOGLE_API_KEY in .env."}

    prompt = f"""
    You are an expert logic synthesis tool. Your task is to analyze the following Verilog module and convert it into a detailed gate-level netlist.
    **Instructions:**
    1.  Identify all inputs, outputs, and internal wires.
    2.  Decompose all `assign` statements and logic into primitive gates: `and`, `or`, `not`, `xor`, `nand`, `nor`, `xnor`.
    3.  Generate a response in a single, valid JSON object format. Do not add any text or markdown formatting before or after the JSON block.
    4.  The JSON object must have three keys: "inputs", "outputs", and "gates".
        -   "inputs": A list of strings with the names of all input ports.
        -   "outputs": A list of strings with the names of all output ports.
        -   "gates": A list of all synthesized gates. Each gate is an object with "type" (e.g., 'and', 'or'), "output" (the wire this gate drives), and "inputs" (a list of wires connected to the gate's inputs).
    5.  For a statement like `assign y = a & b;`, you would identify 'a' and 'b' as inputs, 'y' as an output, and create a gate object: {{"type": "and", "output": "y", "inputs": ["a", "b"]}}.
    6.  Handle multi-bit buses by treating each bit as a separate wire (e.g., `a[0]`, `a[1]`).
    **Verilog Code to Synthesize:**
    ```verilog
    {module_code}
    ```
    **Output JSON:**
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        json_text = response.text.strip().lstrip("```json").rstrip("```")
        return json.loads(json_text)
    except (json.JSONDecodeError, AttributeError, Exception) as e:
        return {"error": f"Failed to get a valid JSON response from the AI. The AI response may have been malformed. Details: {e}"}

def generate_testbench_with_gemini(module_name: str, inputs: list, outputs: list) -> str:
    """Uses Google Gemini to generate a Verilog testbench."""
    if not GOOGLE_AI_AVAILABLE: return "// Google AI is not configured. Please set GOOGLE_API_KEY in .env."

    prompt = f"""
    Act as a VLSI verification expert. Generate a complete Verilog testbench for the module `{module_name}`.
    **Inputs:** {', '.join(inputs) or 'None'}
    **Outputs:** {', '.join(outputs) or 'None'}
    **Requirements:**
    1. Module name: `{module_name}_tb`.
    2. Instantiate the DUT.
    3. If 'clk' exists, generate a clock. If 'rst' exists, apply a reset.
    4. Apply at least 5 distinct test vectors with a 10ns delay.
    5. Use `$display` to show inputs/outputs for each vector.
    6. End with `$finish`.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        code = response.text.strip()
        if '```verilog' in code:
            code = code.split('```verilog')[1].split('```')[0].strip()
        return code
    except Exception as e:
        return f"// Gemini API call for testbench failed: {e}"

def create_gate_level_diagram(netlist: dict) -> Digraph:
    """Draws a gate-level diagram from a JSON netlist."""
    dot = Digraph()
    dot.attr(rankdir='LR', splines='ortho', ranksep='1.2', nodesep='0.6', bgcolor='transparent')
    dot.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='10')
    dot.attr('edge', arrowhead='vee', arrowsize='0.7')

    if "error" in netlist:
        dot.node("error", f"Error:\n{netlist['error']}", shape="box", style="filled", fillcolor="#FFCCCC")
        return dot

    all_nodes = set()

  
    colors = {
        'input': '#C1FFC1',   
        'output': '#FFDDC1',  
        'gate': '#C1DDFF',    
        'wire': '#E0E0E0'      
    }

    with dot.subgraph(name='cluster_inputs') as c:
        c.attr(label='Inputs', style='rounded', color='gray')
        for port in netlist.get("inputs", []):
            c.node(port, label=port, shape='ellipse', fillcolor=colors['input'])
            all_nodes.add(port)

    with dot.subgraph(name='cluster_outputs') as c:
        c.attr(label='Outputs', style='rounded', color='gray')
        for port in netlist.get("outputs", []):
            c.node(port, label=port, shape='ellipse', fillcolor=colors['output'])
            all_nodes.add(port)

    for i, gate in enumerate(netlist.get("gates", [])):
        gate_type = gate.get("type", "gate").upper()
        gate_id = f"gate_{i}_{gate_type.lower()}"
        gate_output = gate.get("output")
        gate_inputs = gate.get("inputs", [])

        dot.node(gate_id, label=gate_type, fillcolor=colors['gate'])
        if gate_output:
            dot.edge(gate_id, gate_output)
            all_nodes.add(gate_output)
        for g_input in gate_inputs:
            dot.edge(g_input, gate_id)
            all_nodes.add(g_input)
            
 
    for node in all_nodes:
        if node not in netlist.get("inputs", []) and node not in netlist.get("outputs", []):
            is_gate_output = any(gate.get("output") == node for gate in netlist.get("gates", []))
       
            if not is_gate_output:
                 dot.node(node, label=node, shape='point', width='0.01', color='gray')

    return dot



st.set_page_config(
    page_title="Verilog AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    /* Main title style */
    h1 {
        color: #4A90E2;
        text-align: center;
        font-weight: bold;
    }
    /* Sub-header for the author's name */
    .author-name {
        font-size: 1.0rem;
        font-style: italic;
        text-align: center;
        color: #B0B0B0;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


st.title("🤖 Verilog AI Assistant")
st.markdown("<p class='author-name'>By Mohak Vaish</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1rem;'>An all-in-one tool to synthesize stunning <strong>gate-level diagrams</strong> and generate robust <strong>testbenches</strong> from your Verilog code, powered by AI.</p>", unsafe_allow_html=True)
st.markdown("---")  


if 'verilog_code' not in st.session_state:
    st.session_state.verilog_code = ""


with st.sidebar:
    st.header("⚙️ Controls")
    uploaded_file = st.file_uploader(
        "**1. Upload your Verilog file**",
        type=['v', 'sv'],
        help="Upload a Verilog (.v) or SystemVerilog (.sv) file to get started."
    )
    if uploaded_file:
        st.session_state.verilog_code = uploaded_file.read().decode('utf-8', errors='ignore')
        st.success(f"✅ Loaded `{uploaded_file.name}`")


if not st.session_state.verilog_code:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("👋 Welcome! Please upload a Verilog file using the sidebar to begin.")
        st.image("[https://i.imgur.com/kZ1hL6D.png](https://i.imgur.com/kZ1hL6D.png)", caption="Upload a file to start the magic!", use_column_width=True)
else:
    module_names = get_module_names(st.session_state.verilog_code)

    if not module_names:
        st.warning("⚠️ No Verilog modules found in the uploaded file. Please check the file's content and format.")
    else:

        with st.sidebar:
            st.markdown("**2. Select a Module**")
            selected_module = st.selectbox(
                "Choose the module you want to work with:",
                module_names,
                key="module_select"
            )
            st.markdown("---")


        tab1, tab2 = st.tabs(["**✨ Gate-Level Diagram**", "**🧪 Testbench Generator**"])

        with tab1:
            st.header(f"Gate-Level Diagram for `{selected_module}`")
            st.markdown("Click the button below to let the AI synthesize your module into a detailed gate-level circuit diagram.")
            
            if st.button(f"🚀 Generate Diagram for `{selected_module}`", type="primary", use_container_width=True):
                if not GOOGLE_AI_AVAILABLE:
                    st.error("❌ Google API key not configured. Please set `GOOGLE_API_KEY` in your environment.")
                else:
                    with st.spinner(f"🧠 AI is synthesizing `{selected_module}`... This might take a moment."):
                        module_code = get_module_code(selected_module, st.session_state.verilog_code)
                        if module_code:
                            netlist = ask_gemini_for_gate_level_netlist(module_code)
                            if "error" in netlist:
                                st.error(f"**AI Synthesis Error:** {netlist['error']}")
                            else:
                                st.success("✅ Synthesis complete! Here is your diagram.")
                                diagram = create_gate_level_diagram(netlist)
                                st.graphviz_chart(diagram, use_container_width=True)

                                png_data = diagram.pipe(format='png')
                                st.download_button(
                                    label="📥 Download Diagram (PNG)",
                                    data=png_data,
                                    file_name=f'{selected_module}_diagram.png',
                                    mime='image/png',
                                    use_container_width=True
                                )
                                with st.expander("🔬 View AI-Generated Netlist (JSON)"):
                                    st.json(netlist)
                        else:
                            st.error(f"❌ Could not extract the code for module `{selected_module}`.")

        with tab2:
            st.header(f"Testbench Generator for `{selected_module}`")
            st.markdown("Generate a comprehensive Verilog testbench for your selected module with a single click.")
            
            if st.button(f"⚡ Generate Testbench for `{selected_module}`", type="primary", use_container_width=True):
                if not GOOGLE_AI_AVAILABLE:
                    st.error("❌ Google API key not configured. Please set `GOOGLE_API_KEY` in your environment.")
                else:
                    with st.spinner(f"✍️ AI is writing the testbench for `{selected_module}`..."):
                        inputs, outputs = get_ports_for_testbench(selected_module, st.session_state.verilog_code)
                        if not inputs and not outputs:
                            st.warning(f"⚠️ Could not automatically parse I/O ports for `{selected_module}`. The generated testbench might be incomplete.")
                        
                        tb_code = generate_testbench_with_gemini(selected_module, inputs, outputs)
                        st.success("✅ Testbench generated successfully!")
                        st.code(tb_code, language='verilog', line_numbers=True)

                        st.download_button(
                            label="💾 Download Testbench File",
                            data=tb_code,
                            file_name=f"{selected_module}_tb.v",
                            mime="text/x-verilog",
                            use_container_width=True
                        )
