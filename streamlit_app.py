# streamlit_app.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import re
import pandas as pd
from urllib.parse import urljoin

st.set_page_config(page_title="Contract Prórroga Checker")

st.title("📄 Contract Extension (Prórroga) Checker")

# Step 1: User pastes a URL
url = st.text_input("Paste the contract page URL here:")

def extract_pdf_links(base_url):
    try:
        response = requests.get(base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        pdf_links = [urljoin(base_url, link) for link in links if link.endswith('.pdf')]
        return pdf_links
    except Exception as e:
        st.error(f"Error extracting links: {e}")
        return []

def extract_text_from_pdf(pdf_url):
    try:
        response = requests.get(pdf_url)
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
        text = ""
        with fitz.open("temp.pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"[ERROR] Failed to read {pdf_url}: {e}"

def find_prorroga_info(text):
    # Looks for lines with "prórroga" and associated dates
    matches = re.findall(r"(pr[oó]rroga.*?(\d{2}/\d{2}/\d{4}))", text, re.IGNORECASE)
    return [m[0] for m in matches]

# Main logic
if url:
    st.info("🔍 Scanning website for PDF links...")
    pdf_links = extract_pdf_links(url)

    if not pdf_links:
        st.warning("No PDFs found at this URL.")
    else:
        data = []
        for pdf_url in pdf_links:
            st.write(f"📎 Checking PDF: {pdf_url}")
            text = extract_text_from_pdf(pdf_url)
            prorrogas = find_prorroga_info(text)
            data.append({
                "PDF URL": pdf_url,
                "Prórroga Info Found": "; ".join(prorrogas) if prorrogas else "❌ Not found"
            })

        df = pd.DataFrame(data)
        st.success("✅ Scan completed!")
        st.dataframe(df)

        # CSV download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV", csv, "prorrogas_results.csv", "text/csv")
