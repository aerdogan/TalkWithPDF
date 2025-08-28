import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Gemini PDF Chatbot", page_icon="📄")
st.title("📄 Gemini PDF Chatbot")

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_file = st.file_uploader("Bir PDF yükle:", type=["pdf"])
if uploaded_file is not None:
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    st.session_state.pdf_text = text
    st.success("PDF başarıyla yüklendi ✅")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Sorunu yaz…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            context_prompt = f"""
PDF içeriği:
{st.session_state.pdf_text}

Soru:
{prompt}

Cevabı sadece PDF içeriğine dayanarak ver. PDF’de yoksa “PDF içeriğinde bilgi yok” de.
"""
            response = model.generate_content(context_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            message_placeholder.markdown(f"Bir hata oluştu: {e}")

        st.session_state.messages.append({"role": "assistant", "content": full_response})
