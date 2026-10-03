# Student Academic Assistance

A Streamlit-based AI assistant designed to help university students study, understand academic topics, and work with written material. It uses LangChain to connect to Google Gemini or OpenAI models, with configurable instructions and a simple chat interface.

## Features

- **Choose an AI provider and model:** use Google Gemini or OpenAI, validate an API key, and load available models from the provider.
- **Student-focused assistant:** select the Student Academic Assistant prompt preset, or choose another built-in role such as Math Tutor, Writing Coach, or Language Partner.
- **Custom instructions:** write a system prompt to tailor the assistant's tone and behavior.
- **Adjustable temperature:** control how focused or varied the responses are.
- **Ask questions about files:** attach a PDF, DOCX, or supported text-based file in the chat. The app extracts text and includes it in the request.
- **Remember settings locally:** provider, model, temperature, prompt, and API key are saved to a local `.env` file for the next run.

## Technology

- Python and Streamlit
- LangChain
- Google Gemini through `langchain-google-genai`
- OpenAI through `langchain-openai`
- `pypdf` and `python-docx` for document text extraction
- `python-dotenv` for local settings persistence

## Requirements

- Windows
- Python 3.12 recommended (the included launcher installs it with `winget` if Python is not found)
- An API key for Google Gemini or OpenAI
- Internet access to install packages and contact the selected AI provider

## Run on Windows

1. Download or clone this repository.
2. Open the project folder.
3. Double-click `run.bat`, or run it from Command Prompt or PowerShell.
4. The launcher creates a local `.venv`, installs packages from `requirements.txt`, and starts the Streamlit app.
5. Open the local address printed in the terminal (usually [http://localhost:8501](http://localhost:8501)).
6. Select the gear icon, choose a provider, enter your API key, select **Load Models**, choose a model, and save the settings.
7. Start a conversation. Select **Student Academic Assistant** from the system prompt preset for the student-oriented behavior.

The first launch can take a few minutes while Python (if needed) and the project dependencies are installed.

## Manual setup

If you already have Python installed, run these commands in the project folder using PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown in the terminal and configure the API key in the app's Settings panel.

The app creates or updates `.env` when you save settings. For reference, `.env.example` lists the supported configuration variables. If you configure `.env` manually, copy `.env.example` to `.env` and replace the placeholder API keys with your own; never commit the resulting `.env` file.

## Using file attachments

Use the attachment control in the chat input to add a file. The app accepts PDF, DOCX, TXT, Markdown, CSV, JSON, Python, and log files. PDF and DOCX content is extracted with the corresponding document libraries; other accepted files are read as text. The extracted content is included in the message sent to the selected AI provider. Only the first attached file is processed, and the app limits the included text to 12,000 characters.

## Privacy and API key safety

- API keys are stored in `.env` in the project folder on your computer. The app sends prompts and any included file text to the selected AI provider to generate responses.
- **Never commit or publish `.env` or share your API key.** The provided `.gitignore` excludes `.env` and local Python environment files.
- `.env.example` contains placeholder values only and is safe to include in the repository. Replace placeholders only in your local `.env` file.
- Review your provider's privacy, retention, and usage policies before sending sensitive or personal information.
- Chat history is held in Streamlit's session state and is not saved as a persistent chat database. Clearing or restarting the session may remove it.

## Project files

- `app.py` — Streamlit interface, provider/model configuration, chat handling, and file text extraction.
- `requirements.txt` — Python package dependencies.
- `run.bat` — Windows setup and launch script.
- `.env.example` — safe template showing the available environment settings.

## Academic use note

Use the assistant as a study aid to explore ideas and get explanations. Check important claims against course materials and reliable sources, and follow your institution's academic integrity rules. AI-generated responses can be inaccurate.
