import streamlit as st
import google.generativeai as genai

# Use your existing secret to connect
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

print("Checking available Gemini models...")

# This loop finds every model your key can access
for m in genai.list_models():
    # We only want models that can 'generateContent' (the AI brain part)
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model Name: {m.name}")