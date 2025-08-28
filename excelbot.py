import os
import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Gemini Excel Chatbot", page_icon="📊")
st.title("📊 Gemini Excel Chatbot")

if "excel_text" not in st.session_state:
    st.session_state.excel_text = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_file = st.file_uploader("Bir Excel dosyası yükle:", type=["xlsx", "csv"])
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.write("📄 Dosyanın ilk 10 satırı:")
        st.dataframe(df.head(10))
        st.session_state.excel_text = df.to_csv(index=False)
        st.session_state.df = df
        st.success("Excel başarıyla yüklendi ✅")
    except Exception as e:
        st.error(f"Excel okunamadı: {e}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Tabloyla ilgili bir şey sor…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            context_prompt = f"""
Excel tablosu (CSV formatında):
{st.session_state.excel_text[:3000]}  # büyük dosyalarda sınır

Soru:
{prompt}

Cevabı tabloya dayalı ver. Yoksa “Excel içeriğinde bilgi yok” de.
"""
            response = model.generate_content(context_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            # Basit grafik önerisi (sadece sayısal kolonları)
            if "grafik" in prompt.lower() and hasattr(st.session_state, "df"):
                numeric_cols = st.session_state.df.select_dtypes(include='number').columns
                if len(numeric_cols) >= 2:
                    fig = px.bar(st.session_state.df, x=numeric_cols[0], y=numeric_cols[1], title="Otomatik Grafik")
                    st.plotly_chart(fig)
        except Exception as e:
            message_placeholder.markdown(f"Bir hata oluştu: {e}")

        st.session_state.messages.append({"role": "assistant", "content": full_response})
