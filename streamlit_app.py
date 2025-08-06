# streamlit_app.py

import streamlit as st
import requests
import fitz  # PyMuPDF
import time
import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ----------------------- PAGE SETUP -----------------------
st.set_page_config(page_title="Prórroga Detector", layout="centered")
st.title("📄 Contract Prórroga Paragraph Extractor")
st.markdown("Paste a **contract detail page** from [contrataciondelestado.es](https://contrataciondelestado.es) to extract PDF links and detect paragraphs related to **prórrogas (extensions)** in those documents.")

# ----------------------- INPUT -----------------------
url = st.text_input("🔗 Contract page URL:", placeholder="https://contrataciondelestado.es/wps/poc?...")

# ----------------------- EXTRACT PDF LINKS (DYNAMIC) -----------------------
def extract_pdf_links_dynamic(page_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    pdf_links = []
    try:
        driver.get(page_url)
        time.sleep(4)  # Wait for JS

        elements = driver.find_elements("tag name", "a")
        for elem in elements:
            href = elem.get_attribute("href")
            if href and href.lower().endswith(".pdf"):
                pdf_links.append(href)

    except Exception as e:
        st.error(f"❌ Error extracting PDF links: {e}")
    finally:
        driver.quit()

    return list(set(pdf_links))

# ----------------------- EXTRACT TEXT FROM PDF -----------------------
def extract_text_from_pdf(pdf_url):
    try:
        response = requests.get(pdf_url, timeout=10)
        temp_path = "temp_downloaded.pdf"
        with open(temp_path, "wb") as f:
            f.write(response.content)

        text = ""
        with fitz.open(temp_path) as doc:
            for page in doc:
                text += page.get_text("text")

        os.remove(temp_path)
        return text

    except Exception as e:
        return f"[ERROR extracting PDF: {e}]"

# ----------------------- FIND PARAGRAPHS -----------------------
def find_prorroga_paragraphs(text):
    # Split by paragraph or sentence endings
    paragraphs = re.split(r'\n{2,}|(?<=\.)\s+(?=[A-ZÁÉÍÓÚÜÑ])', text)
    trigger_words = [
        "prórroga", "prorrogable", "puede prorrogar", "prorrogará", "prorrogado"
    ]
    matches = []

    for p in paragraphs:
        if any(trigger in p.lower() for trigger in trigger_words):
            matches.append(p.strip())

    return matches

# ----------------------- MAIN LOGIC -----------------------
if url:
    st.info("🔍 Loading and extracting PDF links from the page...")
    pdf_links = extract_pdf_links_dynamic(url)

    if not pdf_links:
        st.warning("⚠️ No PDF links found. Check if the page is correct.")
    else:
        st.success(f"✅ Found {len(pdf_links)} PDF(s). Scanning for prórroga mentions...")

        for pdf_url in pdf_links:
            st.markdown(f"---\n### 📎 PDF: [{pdf_url}]({pdf_url})")

            text = extract_text_from_pdf(pdf_url)
            paragraphs = find_prorroga_paragraphs(text)

            if not paragraphs:
                st.write("❌ No prórroga-related paragraphs found.")
            else:
                st.success(f"✅ Found {len(paragraphs)} relevant paragraph(s):")
                for i, para in enumerate(paragraphs, 1):
                    st.markdown(f"**Paragraph {i}:**\n> {para}")
