import os
import streamlit as st
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

# .env'den API anahtarını al
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Gemini modelini başlat
model = genai.GenerativeModel("gemini-2.5-flash-lite")

st.set_page_config(page_title="Gemini Excel Chatbot", page_icon="📊")
st.title("📊 Gemini Excel Chatbot (ilk 50 satırı baz alır)")

# Excel içeriğini saklamak için session state
if "excel_text" not in st.session_state:
    st.session_state.excel_text = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

# Excel dosyası yükleme
uploaded_file = st.file_uploader("Bir Excel dosyası yükle:", type=["xlsx", "csv"])
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # DataFrame’in ilk satırlarını göster
        st.write("📄 Dosyanın ilk 50 satırı:")
        st.dataframe(df.head(50))

        # Tabloyu string olarak sakla
        st.session_state.excel_text = df.to_csv(index=False)
        st.success("Excel başarıyla yüklendi ✅")
    except Exception as e:
        st.error(f"Excel okunamadı: {e}")

# Daha önceki mesajları göster
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Kullanıcıdan soru al
if prompt := st.chat_input("Tabloyla ilgili bir şey sor…"):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini’den streaming cevap
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            context_prompt = f"""Sen bir veri analizi yardımcısısın.
            Kullanıcı bir Excel tablosu yükledi. İşte tablo verisi (CSV formatında):

            {st.session_state.excel_text[:3000]}  # çok büyük dosyalarda ilk kısımla sınırlıyoruz

            Soru:
            {prompt}

            Lütfen tablo verisine dayalı olarak cevap ver. 
            Tabloda bulunmayan bilgi hakkında "Excel içeriğinde bu bilgi yok" de.
            """
            
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
