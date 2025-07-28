```markdown
# 📑 Intelligent PDF Viewer 
*AI-Powered Document Analysis with Adobe Embed API*

![App Preview](https://via.placeholder.com/800x450.png?text=PDF+Viewer+Demo)  
*Replace with actual application screenshot*

## 🔑 Environment Configuration

### Required Credentials
Create a `.env` file with these variables (use `.env.example` as template):

```ini
# Azure OpenAI (GPT-4o Mini)
AZURE_OPENAI_ENDPOINT_4o="your_azure_endpoint_here"
AZURE_OPENAI_API_KEY_4o="your_api_key_here"
AZURE_OPENAI_API_VERSION_4o="2023-05-15"

# Adobe PDF Embed
ADOBE_CLIENT_ID="your_adobe_client_id_here"
```

## 🚀 Quick Deployment

### 1. Local Setup
```bash
git clone https://github.com/Yashgupta9798/pdfViewer.git
cd pdfViewer
pip install -r requirements.txt

# Start the application
streamlit run app.py
```

### 2. Cloud Deployment (Streamlit)
1. Set environment variables in your hosting platform:
   - Streamlit Cloud: Settings → Secrets
   - Azure App Service: Configuration → Application settings
2. Push your code:
```bash
git push origin main
```

## 🛡️ Security Notice
- Never commit `.env` to version control
- Add to `.gitignore`:
  ```bash
  echo ".env" >> .gitignore
  ```
- Rotate keys immediately if accidentally exposed

## 🌐 Live Demo
Access the deployed application:  
[https://pdfviewer.streamlit.app/](https://pdfviewer.streamlit.app/)

## 📚 API Documentation
| Service | Documentation |
|---------|---------------|
| Adobe PDF Embed | [Adobe Developer Docs](https://developer.adobe.com/document-services/docs/overview/pdf-embed-api/) |
| Azure OpenAI | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/openai/) |

## 🏗️ Project Structure
```
pdfViewer/
├── app.py                # Main application logic
├── services/
│   ├── azure_client.py   # OpenAI integration
│   └── adobe_embed.py    # PDF rendering service
├── utils/
│   └── config_loader.py  # Environment management
├── .env.example          # Configuration template
└── requirements.txt      # Python dependencies
```

## 🤖 AI Integration Example
```python
from services.azure_client import analyze_document

response = analyze_document(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_4o"),
    key=os.getenv("AZURE_OPENAI_API_KEY_4o"),
    document_text=extracted_text
)
```

## 📜 License
MIT License - See [LICENSE](LICENSE) for details.

---

*Developed for Adobe India Hackathon 2025 - Connecting the Dots Challenge*
```
