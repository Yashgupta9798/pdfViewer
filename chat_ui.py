import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from openai import AzureOpenAI
import os
import base64

load_dotenv()

st.set_page_config(page_title="🧠 Chat with your PDF", layout="wide")
st.title("🧠 Chat with your PDF")

# Session state init
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_file_path" not in st.session_state:
    st.session_state.pdf_file_path = None

# Adobe PDF Embed API configuration
ADOBE_CLIENT_ID = os.getenv("ADOBE_CLIENT_ID", "YOUR_ADOBE_CLIENT_ID")  # Add your Adobe Client ID to .env

def create_pdf_viewer(pdf_path, embed_mode="SIZED_CONTAINER"):
    """Create Adobe PDF Embed API viewer HTML"""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    pdf_viewer_html = f"""
    <div id="adobe-dc-view" style="height: 800px; border: 1px solid #ccc; border-radius: 8px;"></div>
    <script src="https://acrobatservices.adobe.com/view-sdk/viewer.js"></script>
    <script type="text/javascript">
        document.addEventListener("adobe_dc_view_sdk.ready", function() {{
            var adobeDCView = new AdobeDC.View({{
                clientId: "{ADOBE_CLIENT_ID}",
                divId: "adobe-dc-view"
            }});
            
            adobeDCView.previewFile({{
                content: {{
                    promise: Promise.resolve(Uint8Array.from(atob("{pdf_base64}"), c => c.charCodeAt(0)))
                }},
                metaData: {{
                    fileName: "document.pdf"
                }}
            }}, {{
                embedMode: "{embed_mode}",
                showAnnotationTools: true,
                showDownloadPDF: true,
                showPrintPDF: true,
                showLeftHandPanel: true,
                showPageControls: true,
                enableFormFilling: true,
                showToolbar: true,
                enableBookmarks: true,
                enableThumbnails: true,
                enableSearch: true,
                showPreviewOnly: false,
                dockPageControls: true
            }});
            
            // Analytics callback
            adobeDCView.registerCallback(
                AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
                function(event) {{
                    console.log("PDF Event:", event);
                }},
                {{
                    enablePDFAnalytics: true
                }}
            );
        }});
    </script>
    """
    return pdf_viewer_html

# Main layout with columns
col1, col2 = st.columns([1, 1])

# Left column - Chat interface
with col1:
    st.subheader("💬 Chat Interface")
    
    # PDF Upload
    if not st.session_state.pdf_uploaded:
        with st.expander("📤 Upload a PDF", expanded=True):
            pdf_file = st.file_uploader("Upload your PDF", type=["pdf"])
            if pdf_file:
                with open("temp.pdf", "wb") as f:
                    f.write(pdf_file.read())
                st.success("✅ PDF uploaded successfully!")
                st.session_state.pdf_uploaded = True
                st.session_state.pdf_file_path = "temp.pdf"
                
                # Process PDF for chat
                loader = PyPDFLoader("temp.pdf")
                docs = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1024,
                    chunk_overlap=400
                )
                split_docs = text_splitter.split_documents(docs)
                
                embeddings = AzureOpenAIEmbeddings(
                    model="text-embedding-ada-002",
                    chunk_size=1024,
                )
                
                st.session_state.vector_db = InMemoryVectorStore.from_documents(split_docs, embeddings)
                st.balloons()
                st.rerun()
    
    # Chat section
    if st.session_state.pdf_uploaded:
        st.divider()
        
        # Display past messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Input field
        user_query = st.chat_input("Ask a question...")
        
        if user_query:
            with st.chat_message("user"):
                st.markdown(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            # Vector search
            with st.spinner("Searching context..."):
                search_results = st.session_state.vector_db.similarity_search(user_query, k=3)
                context = "\n\n".join([
                    f"📄 {res.page_content}\n📘 Page: {res.metadata.get('page_label', 'N/A')}"
                    for res in search_results
                ])
                
                system_prompt = f"""Return all the page numbers related to the keyword given and if asked for summary then return the summary.
                
                Context: {context}
                """
            
            # Stream AI response
            client = AzureOpenAI(
                azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_4o"), 
                api_key= os.getenv("AZURE_OPENAI_API_KEY_4o"),  
                api_version= os.getenv("AZURE_OPENAI_API_VERSION_4o")
            )
            
            with st.chat_message("assistant"):
                full_response = ""
                current_word = ""
                placeholder = st.empty()
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    stream=True,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query},
                    ]
                )
                
                for chunk in response:
                    if not chunk.choices:
                        continue
                    
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", "")
                    
                    if content:
                        for char in content:
                            current_word += char
                            
                            if char in [" ", "\n"]:
                                full_response += current_word
                                placeholder.markdown(full_response + "▌")
                                current_word = ""
                
                full_response += current_word
                placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})

# Right column - PDF viewer
with col2:
    st.subheader("📄 PDF Viewer")
    
    if st.session_state.pdf_uploaded and st.session_state.pdf_file_path:
        # PDF Viewer controls
        with st.expander("🔧 PDF Viewer Settings", expanded=False):
            embed_mode = st.selectbox(
                "Embed Mode",
                ["SIZED_CONTAINER", "FULL_WINDOW", "IN_LINE", "LIGHT_BOX"],
                help="Choose how the PDF is displayed"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                show_annotations = st.checkbox("Show Annotation Tools", value=True)
                show_download = st.checkbox("Show Download", value=True)
            with col_b:
                show_print = st.checkbox("Show Print", value=True)
                enable_analytics = st.checkbox("Enable Analytics", value=True)
        
        # Create and display PDF viewer
        if ADOBE_CLIENT_ID != "YOUR_ADOBE_CLIENT_ID":
            pdf_html = create_pdf_viewer(st.session_state.pdf_file_path, embed_mode)
            st.components.v1.html(pdf_html, height=850, scrolling=True)
        else:
            st.warning("⚠️ Please add your Adobe Client ID to the .env file to enable PDF viewing")
            st.info("Get your free Client ID at: https://developer.adobe.com/document-services/apis/pdf-embed/")
            
            # Fallback to basic PDF display
            st.subheader("Basic PDF Display")
            with open(st.session_state.pdf_file_path, "rb") as f:
                pdf_bytes = f.read()
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                pdf_display = f'<embed src="data:application/pdf;base64,{pdf_base64}" width="100%" height="800" type="application/pdf">'
                st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("👆 Upload a PDF file to view it here")
        
        # Adobe PDF Embed API features showcase
        st.markdown("### 🚀 Adobe PDF Embed API Features")
        
        features = {
            "📝 Annotation Tools": "Add comments, highlights, and drawings",
            "📊 Analytics": "Track user interactions and engagement",
            "🤝 Collaborative Settings": "Enable multi-user collaboration",
            "💾 Save Controls": "Control document saving options",
            "🛠️ Menu & Tool Options": "Customize toolbar and menu visibility",
            "🎯 Multiple Embed Modes": "Full window, sized container, in-line, lightbox"
        }
        
        for feature, description in features.items():
            st.markdown(f"**{feature}**: {description}")
