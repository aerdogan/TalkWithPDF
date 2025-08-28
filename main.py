import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# .env'den API anahtarını al
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Gemini modelini başlat
model = genai.GenerativeModel("gemini-2.5-flash-lite")

st.set_page_config(page_title="Gemini PDF Chatbot", page_icon="🤖")
st.title("📄 Gemini PDF Chatbot")

# PDF içeriğini saklamak için session state
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

# PDF yükleme alanı
uploaded_file = st.file_uploader("Bir PDF yükle:", type=["pdf"])
if uploaded_file is not None:
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    st.session_state.pdf_text = text
    st.success("PDF başarıyla yüklendi ✅")

# Daha önceki mesajları göster
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Kullanıcıdan soru al
if prompt := st.chat_input("Sorunu yaz…"):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini'den streaming cevap
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Kullanıcının sorusunu PDF bağlamı ile birleştir
            context_prompt = f"""Sen bir yardımcı asistansın.
Aşağıda bir PDF içeriği var. Kullanıcı sadece bu içerikle ilgili sorular sorabilir.
Eğer cevap PDF'de yoksa "PDF içeriğinde buna dair bilgi yok" de.

PDF içeriği:
{st.session_state.pdf_text}

Soru:
{prompt}
"""
            # Streaming cevabı üret
            response = model.generate_content(context_prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"Bir hata oluştu: {e}"
            message_placeholder.markdown(full_response)

        # Sohbet geçmişine kaydet
        st.session_state.messages.append({"role": "assistant", "content": full_response})
