# AI-Powered Verilog Synthesis & Verification Assistant 🤖

A Python-based web application that leverages the Google Gemini API to automate critical stages of the VLSI design workflow. This tool instantly generates detailed, gate-level logic schematics and creates functional Verilog testbenches from user-provided HDL code.

---

### ## Demo

https://drive.google.com/file/d/1ChLv_w5rSPnZXRGL3Drjix4jvi_MPQwk/view?usp=sharing

---

### ## Key Features

-   **AI-Driven Logic Synthesis**: Translates behavioral or structural Verilog (e.g., `assign` statements) into a clean, professional gate-level schematic with standard logic symbols.
-   **Automated Testbench Generation**: Creates a ready-to-use Verilog testbench for any given module, significantly reducing the time and effort required for functional verification.
-   **Interactive Web Interface**: Built with Streamlit for an easy-to-use, intuitive user experience that allows for file uploads and interactive controls.
-   **Multi-Module Support**: Automatically detects and allows the user to select from multiple modules within a single uploaded Verilog file.
-   **Debugging and Verification**: Provides the AI-generated logic expressions alongside the schematic, allowing for easy verification and debugging of the synthesized logic.

---

### ## Tech Stack

-   **Backend**: Python
-   **AI/ML**: Google Gemini API
-   **UI Framework**: Streamlit
-   **Schematic Generation**: SchemDraw
-   **Hardware Description Language**: Verilog

---

### ## Local Setup and Usage

Follow these steps to run the project on your local machine.

#### **1. Prerequisites**

-   Python 3.8+
-   Git

#### **2. Clone the Repository**

```bash
git clone [https://github.com/mohakVaish/AI-Verilog-Assistant.git]
