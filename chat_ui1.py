import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from openai import AzureOpenAI
import os

load_dotenv()

st.set_page_config(page_title="🧠 Chat with your PDF", layout="centered")
st.title("🧠 Chat with your PDF")

# Session state init
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# PDF Upload
if not st.session_state.pdf_uploaded:
    with st.expander("📤 Upload a PDF", expanded=True):
        pdf_file = st.file_uploader("Upload your PDF", type=["pdf"])
        if pdf_file:
            with open("temp.pdf", "wb") as f:
                f.write(pdf_file.read())
            st.success("✅ PDF uploaded successfully!")
            st.session_state.pdf_uploaded = True

            loader = PyPDFLoader("temp.pdf")
            docs = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1024,
                chunk_overlap=400
            )
            split_docs = text_splitter.split_documents(docs)

            embeddings = AzureOpenAIEmbeddings(
                model="text-embedding-ada-002",  # or your deployed embedding model
                chunk_size=1024,
            )

            st.session_state.vector_db = InMemoryVectorStore.from_documents(split_docs, embeddings)
            st.balloons()

# Chat section
if st.session_state.pdf_uploaded:
    st.divider()
    st.subheader("💬 Ask anything from your PDF")

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

            system_prompt = f"""return all the page numbers related to the keyword given and if asked for summary then return the summary.
        
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
        
                        # If we hit a space or newline, it’s the end of a word
                        if char in [" ", "\n"]:
                            full_response += current_word
                            placeholder.markdown(full_response + "▌")  # update UI
                            current_word = ""  # reset
        
            # Add any remaining word
            full_response += current_word
            placeholder.markdown(full_response)  # Final display
        
            # Store in session
            st.session_state.messages.append({"role": "assistant", "content": full_response})