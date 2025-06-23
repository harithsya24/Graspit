import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Import the backend classes
from main import AIVideoGenerator, Config

# Streamlit page configuration
st.set_page_config(page_title="AI Educational Video Generator", layout="centered")

st.title("🎬 GraspIt")
st.write("Enter an educational concept or topic, then generate an explainer video automatically.")

concept = st.text_input("Enter Concept / Topic", max_chars=100)
generate_button = st.button("Generate Video")

@st.cache_resource
def get_generator():
    config = Config()
    # ✅ Load keys securely from environment
    config.DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")
    config.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    config.GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Set GOOGLE_APPLICATION_CREDENTIALS for Google TTS
    if config.GOOGLE_CREDENTIALS_PATH:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GOOGLE_CREDENTIALS_PATH

    return AIVideoGenerator(config)

generator = get_generator()

if generate_button:
    if not concept.strip():
        st.warning("Please enter a concept before generating a video.")
    else:
        with st.spinner(f"Generating video for concept: '{concept.strip()}' (this may take a few minutes)..."):
            try:
                video_path = generator.generate_video(concept.strip())
                if Path(video_path).exists():
                    st.success("✅ Video generated successfully!")
                    st.video(video_path)
                else:
                    st.error("❌ Video generation failed: video file not found.")
            except Exception as e:
                st.error(f"❌ An error occurred during video generation:\n\n{e}")