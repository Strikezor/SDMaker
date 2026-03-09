# 📄 Solution Document (SD) Synthesizer

An architecture-driven, AI-powered document pipeline built with Streamlit and the Groq API. This application intelligently synthesizes Business Requirement Documents (BRD/URF) and Regulatory Guidelines into a structured JSON dataset, which is directly injected into a customized Microsoft Word (`.docx`) template using Llama 3 models.

## ✨ Features

* **Multi-Format Document Parsing:** Upload multiple `.txt`, `.pdf`, and `.docx` files simultaneously for each input category.
* **Dynamic Word Templating (`docxtpl`):** Replaces rigid text generation with smart document injection. The AI outputs strict JSON mapped directly to Jinja2 tags (e.g., `{{ scope_of_change }}`) inside a standard Microsoft Word `template.docx` file.
* **Two-Tier AI Processing:**
* Uses the fast `llama-3.1-8b-instant` model for rapid input validation (ensuring files are relevant) and missing information detection.
* Uses the powerful `llama-3.3-70b-versatile` model for heavy context mapping, structured JSON generation, and writing.


* **Interactive Missing Information Loop:** If the AI detects that uploaded inputs are missing core architectural details, it pauses to ask the user to provide the missing details manually before generation.
* **Iterative AI Editing & Undo:** Use the "Refine Generated Document" prompt box to ask the AI to expand or rewrite specific sections. Includes an **Undo Last Revision** feature to safely revert unwanted changes.
* **Persistent JSON Knowledge Base (KB):** Automatically saves your finalized JSON data into a local `knowledge_base.json` file for future reference. Includes a **Human-Readable Preview** mode so non-technical users can read the JSON cleanly on-screen.
* **CR Number Management:** Auto-generates incremental Change Request (CR) numbers (e.g., `CR000001`) with built-in duplicate conflict resolution.
* **Parent CR Referencing:** Input an older CR number to automatically pull its architecture and constraints from the KB to use as a contextual baseline for new documents.
* **Native Word (.docx) Export:** Download the fully synthesized, styled, and mapped Word document directly to your machine.

---

## 🛠️ Prerequisites & Installation

1. **Clone the repository:**

```bash
   git clone https://github.com/yourusername/solution-document-synthesizer.git
   cd solution-document-synthesizer

```

2. **Create a virtual environment (Recommended):**

```bash
   python -m venv venv
   # On Windows use: venv\Scripts\activate
   # On macOS/Linux use: source venv/bin/activate

```

3. **Install the required dependencies:**

```bash
   pip install streamlit PyPDF2 python-docx docxtpl python-dotenv groq

```

4. **Set up Environment Variables:**
Create a `.env` file in the root directory of the project and add your Groq API key:

```env
   GROQ_API_KEY=your_groq_api_key_here

```

5. **Set up the Word Template:**
Create a `template.docx` file in the root directory. Add your company's styling, logos, and layout to this file. Place Jinja2 tags wherever you want the AI to inject text. *(See Example Structure below)*

---

## 🚀 Usage

1. **Start the Streamlit App:**

```bash
   streamlit run app.py

```

2. **Input Documents:** Upload your Regulatory, BRD/URF, and any Optional Supporting documents in the provided drop zones.
3. **Analyze & Generate:** Click "Analyze Documents & Generate SD". The app will validate your files, check for missing info, and generate a structured JSON object.
4. **Review & Refine:** Review the human-readable preview on the screen. Use the AI revision tools to make edits if necessary.
5. **Save or Export:** Click "Insert into Knowledge Base" to save the data locally, or click "Download as Word Doc" to generate your final `.docx` file.

---

## 📁 Project Structure

```text
solution-document-synthesizer/
├── app.py                 # Main Streamlit application
├── template.docx          # MUST CREATE: The styled Word Document containing Jinja2 tags
├── .env                   # MUST CREATE: Stores your GROQ_API_KEY
├── knowledge_base.json    # Auto-generated: Stores finalized JSON document data locally
└── README.md              # Project documentation

```

---

## 📝 Example `template.docx` Tags

Your `template.docx` should be a standard Word Document formatted however you prefer. To map the AI's output to the document, use double curly braces (`{{ tag_name }}`).

Based on the default `SYSTEM_PROMPT` in the code, the AI expects to fill these exact tags:

* `{{ cr_number }}`
* `{{ month_year }}`
* `{{ module_name }}`
* `{{ functionality_name }}`
* `{{ brief_description }}`
* `{{ cr_details }}`
* `{{ scope_of_change }}`
* `{{ executive_summary }}`
* `{{ existing_functionality }}`
* `{{ technical_feasibility }}`
* `{{ proposed_solution_details }}`
* `{{ assumptions }}`
* `{{ limitations }}`
* `{{ user_type_specifications }}`
* `{{ maker_checker_specifications }}`
* `{{ data_migration }}`
* `{{ implementation_plan }}`
* `{{ archival_policy }}`
* `{{ business_acceptance_scenario }}`
* `{{ references }}`

*Example inside the Word doc:*
**1.1 Scope of Change**
{{ scope_of_change }}

**1.2 Executive Summary**
{{ executive_summary }}

---

## 🤖 Models Used

* **Groq:** Infrastructure provider for blazing-fast inference.
* **Meta Llama 3.1 8B Instant:** Used for validation and missing info extraction.
* **Meta Llama 3.3 70B Versatile:** Used for high-fidelity structured JSON synthesis and deep technical writing.

---

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).
