# 📄 Solution Document (SD) Synthesizer

An architecture-driven, AI-powered document pipeline built with Streamlit and the Groq API. This application intelligently synthesizes Business Requirement Documents (BRD/URF) and Regulatory Guidelines into a strictly formatted Solution Document (SD) using Llama 3 models.

## ✨ Features

- **Multi-Format Document Parsing:** Upload multiple `.txt`, `.pdf`, and `.docx` files simultaneously for each input category.
- **Smart XML Templating:** Enforces strict structural adherence by reading a customizable `template.xml` file to generate the final output.
- **Two-Tier AI Processing:**
  - Uses the fast `llama-3.1-8b-instant` model for rapid input validation (ensuring files are relevant) and missing information detection.
  - Uses the powerful `llama-3.3-70b-versatile` model for heavy context mapping, document synthesis, and writing.
- **Interactive Missing Information Loop:** If the AI detects that uploaded inputs are missing data required by your template, it pauses to ask the user to provide the missing details manually before generating the document.
- **Iterative AI Editing:** Use the "Refine Generated Document" text box to ask the AI to expand, format, or rewrite specific parts of the generated SD.
- **Persistent JSON Knowledge Base (KB):** Automatically saves your finalized Solution Documents into a local `knowledge_base.json` file for future reference.
- **CR Number Management:** Auto-generates incremental Change Request (CR) numbers (e.g., `CR000001`) with built-in duplicate conflict resolution.
- **Parent CR Referencing:** Input an older CR number to automatically pull its architecture and constraints from the KB to use as a contextual baseline for new documents.
- **PDF Export:** Convert the generated Markdown document directly into a downloadable `.pdf` file.

---

## 🛠️ Prerequisites & Installation

1. **Clone the repository:**

```bash
   git clone [https://github.com/yourusername/solution-document-synthesizer.git](https://github.com/yourusername/solution-document-synthesizer.git)
   cd solution-document-synthesizer
```

2. **Create a virtual environment (Recommended):**

```bash
python -m venv venv
   On Windows use: venv\Scripts\activate
   On macOS/Linux use: source venv/bin/activate

```

3. **Install the required dependencies:**

```bash
pip install streamlit PyPDF2 python-docx markdown fpdf python-dotenv groq

```

4. **Set up Environment Variables:**
   Create a `.env` file in the root directory of the project and add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here

```

5. **Set up the XML Template:**
   Create a `template.xml` file in the root directory. This file dictates the structure the AI will follow. _(See Example Structure below)_

---

## 🚀 Usage

1. **Start the Streamlit App:**

```bash
streamlit run app.py

```

2. **Input Documents:** Upload your Regulatory, BRD/URF, and any Optional Supporting documents in the provided drop zones.
3. **Analyze & Generate:** Click "Analyze Documents & Generate SD". The app will validate your files and check for missing information.
4. **Refine:** Use the "Refine Generated Document" prompt box to make iterative edits to the generated text.
5. **Save or Export:** Click "Insert into Knowledge Base" to save it to your local JSON database, or download it as a PDF.

---

## 📁 Project Structure

```text
solution-document-synthesizer/
├── app.py                 # Main Streamlit application
├── template.xml           # MUST CREATE: The XML file dictating output structure
├── .env                   # MUST CREATE: Stores your GROQ_API_KEY
├── knowledge_base.json    # Auto-generated: Stores finalized documents locally
└── README.md              # Project documentation

```

---

## 📝 Example `template.xml`

To get started, your `template.xml` should look something like this. The AI will use these exact tags to structure the final Markdown document.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SolutionDocument>
    <Header>
        <ProjectName>[Insert Project Name]</ProjectName>
        <Date>[Insert Date]</Date>
    </Header>
    <Section_1_ExecutiveSummary>
        [Provide a high-level summary mapping BRD to Regulatory limits]
    </Section_1_ExecutiveSummary>
    <Section_2_Assumptions>
        [List technical and business assumptions]
    </Section_2_Assumptions>
</SolutionDocument>

```

---

## 🤖 Models Used

- **Groq:** Infrastructure provider for blazing-fast inference.
- **Meta Llama 3.1 8B Instant:** Used for validation and missing info extraction.
- **Meta Llama 3.3 70B Versatile:** Used for high-fidelity document synthesis and refinement.

---

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).
