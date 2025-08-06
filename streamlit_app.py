# streamlit_app.py

import streamlit as st
import requests
import fitz  # PyMuPDF
import time
import os
import re
import pandas as pd
import asyncio
import subprocess

# Install Chromium browser for Playwright (first-time only)
subprocess.run(["playwright", "install", "chromium"])

from playwright.async_api import async_playwright


st.set_page_config(page_title="Prórroga Paragraph Extractor", layout="centered")
st.title("📄 Contract Prórroga Paragraph Extractor")
st.markdown("""
Paste a [contrataciondelestado.es](https://contrataciondelestado.es) **contract page URL**, and this app will:
- Load dynamic content
- Extract any PDF links
- Check for paragraphs mentioning prórrogas
""")

url = st.text_input("🔗 Paste the contract detail page URL:")


# --------------- Extract PDF Links with Playwright ----------------
async def extract_pdf_links_with_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(4000)

        anchors = await page.query_selector_all("a")
        links = []
        for a in anchors:
            href = await a.get_attribute("href")
            if href and href.lower().endswith(".pdf"):
                if href.startswith("http"):
                    links.append(href)
                else:
                    full_url = page.url.split('?')[0] + href
                    links.append(full_url)
        await browser.close()
        return list(set(links))


# --------------- Extract PDF Text ----------------
def extract_text_from_pdf(pdf_url):
    try:
        response = requests.get(pdf_url, timeout=10)
        path = "temp.pdf"
        with open(path, "wb") as f:
            f.write(response.content)

        text = ""
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text("text")
        os.remove(path)
        return text
    except Exception as e:
        return f"[ERROR reading PDF: {e}]"


# --------------- Find Prórroga Paragraphs ----------------
def find_prorroga_paragraphs(text):
    # Split into paragraphs and sentences
    blocks = re.split(r'\n{2,}|(?<=\.)\s+(?=[A-ZÁÉÍÓÚÜÑ])', text)
    trigger_words = ["prórroga", "prorrogable", "puede prorrogar", "prorrogará", "prorrogado"]

    matches = [block.strip() for block in blocks if any(t in block.lower() for t in trigger_words)]
    return matches


# --------------- Main Logic ----------------
if url:
    st.info("🔍 Extracting PDF links from dynamic page...")
    pdf_links = asyncio.run(extract_pdf_links_with_playwright(url))

    if not pdf_links:
        st.warning("⚠️ No PDFs found.")
    else:
        st.success(f"✅ Found {len(pdf_links)} PDF(s). Scanning...")

        for pdf_url in pdf_links:
            st.markdown(f"---\n### 📎 PDF: [{pdf_url}]({pdf_url})")

            text = extract_text_from_pdf(pdf_url)
            matches = find_prorroga_paragraphs(text)

            if not matches:
                st.write("❌ No prórroga-related paragraphs found.")
            else:
                st.success(f"✅ Found {len(matches)} paragraph(s) mentioning prórrogas:")
                for i, para in enumerate(matches, 1):
                    st.markdown(f"**Paragraph {i}:**\n> {para}")
