import streamlit as st
import os
import io
import PyPDF2
import docx
import markdown
from fpdf import FPDF
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Solution Document Synthesizer",
    page_icon="📄",
    layout="wide" 
)

# --- Session State Initialization ---
if "generated_sd" not in st.session_state:
    st.session_state.generated_sd = ""

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = [] 

# NEW: States for the Missing Information flow
if "awaiting_missing_info" not in st.session_state:
    st.session_state.awaiting_missing_info = False

if "missing_info_report" not in st.session_state:
    st.session_state.missing_info_report = ""

if "cached_docs" not in st.session_state:
    st.session_state.cached_docs = {}

# --- State Management Helpers ---
def clear_inputs():
    """Clears uploaded files and resets generation state."""
    keys_to_clear = ['reg_file', 'brd_file', 'add_file']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    st.session_state.generated_sd = ""
    st.session_state.awaiting_missing_info = False
    st.session_state.missing_info_report = ""
    st.session_state.cached_docs = {}

# --- Groq & LLM Helper Functions ---
def check_document_relevance(content, doc_type, api_key):
    """Uses a smaller, faster model to validate if the document matches the expected type."""
    client = Groq(api_key=api_key)
    validation_prompt = f"""You are an expert document classifier. 
    Task: Determine if the provided text is a relevant '{doc_type}' document.
    - If it is relevant or contains elements of a {doc_type}, respond EXACTLY with the word: VALID
    - If it is completely irrelevant (e.g., a recipe, random code, a personal letter, unrelated topic), respond with: INVALID: [Brief 1-sentence reason]
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": validation_prompt},
                {"role": "user", "content": f"Document Text:\n{content[:4000]}"} 
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0,
            max_tokens=60,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"INVALID: API Error during validation - {str(e)}"

def check_missing_information(template_xml, reg_text, brd_text, api_key):
    """Checks if the inputs are missing mandatory sections required by the XML template."""
    client = Groq(api_key=api_key)
    prompt = f"""You are a precise business analyst.
    Task: Review the SD Template (XML) against the provided input documents.
    Identify if any specific sections required by the XML template are completely missing from the inputs.
    
    - If ALL necessary information to fill the template is present, respond EXACTLY with the word: NONE
    - If information is missing, provide a concise bulleted list of the missing details. Do not generate the SD.
    
    Template XML:
    {template_xml}
    
    Input Documents:
    [Regulatory]: {reg_text[:3000]}
    [BRD/URF]: {brd_text[:3000]}
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", # Fast model for quick comparison
            temperature=0.1,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "NONE" # Fail open: if error occurs, bypass the missing info check

def get_groq_response(system_content, user_content, api_key):
    """Main function to generate the heavy synthesis document."""
    if not api_key:
        st.error("Please set your Groq API Key in the .env file.")
        return None
    
    client = Groq(api_key=api_key)
    try:
        full_history = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content} 
        ]
        chat_completion = client.chat.completions.create(
            messages=full_history,
            model="llama-3.3-70b-versatile",
            temperature=0.4, 
            max_tokens=4096, 
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# --- File Processing Helpers ---
def extract_text_from_files(uploaded_files):
    """Extracts and concatenates text from a list of txt, pdf, or docx files."""
    if not uploaded_files:
        return ""
    
    # If a single file is passed by mistake, make it a list
    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]
        
    combined_text = ""
    for uploaded_file in uploaded_files:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        combined_text += f"\n\n--- Content from {uploaded_file.name} ---\n\n"
        
        try:
            if file_extension == 'txt':
                stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
                combined_text += stringio.read()
            elif file_extension == 'pdf':
                reader = PyPDF2.PdfReader(uploaded_file)
                text_blocks = [page.extract_text() for page in reader.pages if page.extract_text()]
                combined_text += "\n".join(text_blocks)
            elif file_extension == 'docx':
                doc = docx.Document(uploaded_file)
                combined_text += "\n".join([para.text for para in doc.paragraphs])
            else:
                st.error(f"Unsupported file type: {file_extension}")
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")
            
    return combined_text.strip()

def load_template_xml(filepath="template.xml"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"❌ Template file '{filepath}' not found.")
        return None
    except Exception as e:
        st.error(f"❌ Error reading template file: {e}")
        return None

def generate_pdf(md_text):
    html_text = markdown.markdown(md_text, extensions=['tables'])
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    try:
        pdf.write_html(html_text)
    except Exception as e:
        pdf.set_font("helvetica", size=11)
        pdf.multi_cell(0, 5, text=md_text)
    return bytes(pdf.output())

# --- Core Synthesis Logic Execution ---
def execute_synthesis_pipeline(reg, brd, additional, template, api_key):
    """Executes the final prompt and updates the UI state."""
    synthesize_prompt = f"""
I am providing several key documents below to be synthesized into a single Solution Document (SD).

Please synthesize them exactly according to the provided system instructions and strictly follow the layout defined in the XML SD Template provided below.

---
### INPUT DOCUMENTS:
**1. Regulatory Document Content:**
{reg}

**2. Business Requirement Document (BRD/URF) Content:**
{brd}

**3. Solution Document (SD) Template Structure (MANDATORY OUTPUT FORMAT - XML):**
{template}
"""
    if additional.strip():
        synthesize_prompt += f"\n---\n**4. Additional Supporting Document Content:**\n{additional}\n"

    with st.status("🛠️ Synthesizing Final Solution Document...", expanded=True) as status:
        st.write("Mapping Regulatory constraints to Business requirements...")
        st.write("Formatting response using provided SD Template structure...")
        
        response = get_groq_response(SYSTEM_PROMPT, synthesize_prompt, api_key)
        
        st.write("Finalizing synthesized document...")
        status.update(label="Synthesis Complete!", state="complete", expanded=False)
        
        if response:
            st.session_state.generated_sd = response
            st.session_state.awaiting_missing_info = False
            st.rerun()

# --- Constants & System Prompt ---
SYSTEM_PROMPT = """
You are an expert AI Solution Document Architect.

YOUR MANDATE:
1.  **Solution Synthesis:** You will be provided with various inputs: a Regulatory Document, a Business Requirements Document (BRD/URF), and a Solution Document (SD) Template structure provided in XML format. Your core task is to synthesize these inputs into a final Solution Document.
2.  **Strict Adherence to Template:** The output **must** follow the exact format, structure, and hierarchy defined in the provided XML SD Template. Do not deviate from the structure of the template. Extract the section headers from the XML tags.
3.  **Synthesis Logic:** You must map the business requirements from the BRD/URF to the regulatory constraints in the Regulatory Document.
4.  **STRICT GROUNDING (NO HALLUCINATION):** You must ONLY use the information explicitly provided in the uploaded documents. Do not invent, assume, or hallucinate. 
5.  **Handling Missing Info:** If the XML template asks for a specific detail that is NOT present in any of the uploaded source documents, you must explicitly state: *"Information not provided in source documents."*
6.  **Formatting:** Professional, technical tone. Use Markdown (bolding, lists, headings).
"""

# --- Sidebar: Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = os.getenv("GROQ_API_KEY")
    
    if api_key:
        st.success("API Key loaded", icon="✅")
    else:
        st.error("No API Key found. Please set GROQ_API_KEY in your .env file.")
    
    st.markdown("---")
    st.markdown("### 📝 Instructions")
    st.markdown("1. Ensure `template.xml` is present in the app directory.")
    st.markdown("2. Upload all mandatory input documents below.")
    st.markdown("3. Click 'Analyze Documents'.")
    st.markdown("4. Supply missing info (if prompted) and Generate.")
    
    if st.button("Clear Inputs & Reset", key="clear_all_btn"):
        clear_inputs()
        st.rerun()

    st.markdown("---")
    st.markdown("### 🗄️ Legacy Import")
    with st.container(border=True):
        st.caption("Insert Old SD into Knowledge base")
        st.file_uploader("Upload existing SD files (TBD Later)", disabled=True)

# --- Main Interface Design ---
st.title("📄 Solution Document Synthesizer")
st.subheader("Architecture-Driven Document Pipeline")
st.divider()

# --- 1. Input Section (Always Visible) ---
st.header("1. Input Section") 
st.info("ℹ️ SD Template structure is automatically loaded from `template.xml`.")

colA, colB = st.columns(2)
with colA:
    reg_files = st.file_uploader("Upload Regulatory Document(s)", type=['txt', 'pdf', 'docx'], key="reg_file", accept_multiple_files=True)
with colB:
    brd_files = st.file_uploader("Upload BRD / URF Document(s)", type=['txt', 'pdf', 'docx'], key="brd_file", accept_multiple_files=True)

st.markdown("---")
add_files = st.file_uploader("Upload Additional Document(s) (Supporting - Optional)", type=['txt', 'pdf', 'docx'], key="add_file", accept_multiple_files=True)
st.markdown("<br>", unsafe_allow_html=True)

# Logic Switch: Are we generating initially, or finalizing after gathering missing info?
if not st.session_state.awaiting_missing_info:
    generate_btn = st.button("🚀 Analyze Documents & Generate SD", type="primary", use_container_width=True)

    if generate_btn:
        reg_content = extract_text_from_files(reg_files)
        brd_content = extract_text_from_files(brd_files)
        additional_final_content = extract_text_from_files(add_files)
        template_content = load_template_xml()

        if not template_content:
            st.warning("Cannot proceed without `template.xml`.")
        elif not reg_content.strip() or not brd_content.strip():
            st.warning("Please upload both Regulatory and BRD/URF input documents.")
        elif not api_key:
            st.warning("GROQ_API_KEY is not configured in your .env file.")
        else:
            # 1. Validation Step
            with st.status("🔍 Analyzing input documents...", expanded=True) as val_status:
                st.write("Validating Regulatory Document relevance...")
                reg_validation = check_document_relevance(reg_content, "Regulatory or Compliance", api_key)
                if reg_validation.startswith("INVALID"):
                    val_status.update(label="Validation Failed", state="error", expanded=True)
                    st.error(f"**Regulatory Document Error:** {reg_validation.replace('INVALID:', '').strip()}")
                    st.stop()
                
                st.write("Validating BRD / URF Document relevance...")
                brd_validation = check_document_relevance(brd_content, "Business Requirement or Use Case", api_key)
                if brd_validation.startswith("INVALID"):
                    val_status.update(label="Validation Failed", state="error", expanded=True)
                    st.error(f"**BRD/URF Document Error:** {brd_validation.replace('INVALID:', '').strip()}")
                    st.stop()
                    
                # 2. Check for Missing Info
                st.write("Cross-referencing inputs with XML template requirements...")
                missing_report = check_missing_information(template_content, reg_content, brd_content, api_key)
                val_status.update(label="Analysis Complete!", state="complete", expanded=False)

            # 3. Decision Fork
            if missing_report != "NONE":
                # Pause and ask user for missing info
                st.session_state.awaiting_missing_info = True
                st.session_state.missing_info_report = missing_report
                st.session_state.cached_docs = {
                    "reg": reg_content,
                    "brd": brd_content,
                    "add": additional_final_content,
                    "tpl": template_content
                }
                st.rerun()
            else:
                # Everything looks good, proceed directly to generation
                execute_synthesis_pipeline(reg_content, brd_content, additional_final_content, template_content, api_key)

# --- 1.5 Missing Information Prompt ---
if st.session_state.awaiting_missing_info and not st.session_state.generated_sd:
    st.divider()
    st.warning("⚠️ Missing Information Detected in Source Documents")
    st.markdown("We found that the following details required by your template are missing from the uploads:")
    st.info(st.session_state.missing_info_report)
    
    user_supplemental = st.text_area(
        "📝 Provide the missing information here (or leave blank to proceed without it):", 
        height=150
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Proceed and Generate SD", type="primary", use_container_width=True):
            # Combine the original additional document info with the newly typed user info
            combined_additional = st.session_state.cached_docs['add']
            if user_supplemental.strip():
                combined_additional += f"\n\n[User Provided Supplemental Information]:\n{user_supplemental}"
                
            execute_synthesis_pipeline(
                st.session_state.cached_docs['reg'],
                st.session_state.cached_docs['brd'],
                combined_additional,
                st.session_state.cached_docs['tpl'],
                api_key
            )
    with col2:
        if st.button("Cancel Generation", use_container_width=True):
            clear_inputs()
            st.rerun()

# --- 2. Post-Processing View (Output Section) ---
if st.session_state.generated_sd:
    st.divider()
    st.header("2. Output Section") 
    st.markdown("### Synthesized Solution Document (SD)") 
    
    with st.container(border=True):
        st.markdown(st.session_state.generated_sd)
        
    st.markdown("### Post-Synthesis Pipeline")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Insert into Knowledge Base", key="save_kb_btn", type="primary", use_container_width=True):
            st.session_state.knowledge_base.append(st.session_state.generated_sd)
            st.success("Document added to Knowledge Base successfully!")
            st.session_state.generated_sd = ""
            st.rerun()
            
    with col2:
        pdf_bytes = generate_pdf(st.session_state.generated_sd)
        st.download_button(
            label="📥 Download as PDF",
            data=pdf_bytes,
            file_name="Synthesized_Solution_Document.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
    with col3:
        if st.button("❌ Discard Output & Start Over", key="discard_btn", use_container_width=True):
            clear_inputs()
            st.rerun()

# --- 3. Knowledge Base Section ---
st.divider()
st.header("3. Knowledge Base")
if not st.session_state.knowledge_base:
    st.info("The knowledge base is currently empty. Generated documents can be stored here for future reference.")
else:
    for i, sd_item in enumerate(reversed(st.session_state.knowledge_base), 1):
        first_line = sd_item.strip().split('\n')[0][:70] 
        title = first_line or "Stored Solution Document"
        
        with st.expander(f"🗃️ {title} (ID: {i})"):
            st.markdown(sd_item)