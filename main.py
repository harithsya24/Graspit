"""
AI Educational Video Generator
============================

An automated system that generates educational explainer videos from concepts using:
- OpenRouter API (GPT-4) for script generation
- Google Cloud Text-to-Speech for narration
- DeepAI for image generation
- MoviePy for video assembly

Installation Requirements:
-------------------------
Run these commands to install required packages:

pip install google-cloud-texttospeech
pip install moviepy
pip install pillow
pip install requests

For Google Cloud TTS, you'll also need to:
1. Create a Google Cloud project
2. Enable the Text-to-Speech API
3. Create a service account key
4. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable

Author: [Your Name]
Version: 1.0
License: MIT
"""

import os
import re
import requests
import tempfile
import textwrap
import traceback
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()  

try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    print("⚠️ Google Cloud Text-to-Speech not available. Install with: pip install google-cloud-texttospeech")
    GOOGLE_TTS_AVAILABLE = False
    texttospeech = None

try:
    # Fix Pillow compatibility before importing MoviePy
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
    
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, AudioClip
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MoviePy not available: {e}")
    print("Install with: pip install moviepy")
    MOVIEPY_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    print("⚠️ PIL/Pillow not available. Install with: pip install pillow")
    PIL_AVAILABLE = False

class Config:
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", 900))
    VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", 600))
    VIDEO_FPS = int(os.getenv("VIDEO_FPS", 24))
    DEFAULT_SCENE_DURATION = float(os.getenv("DEFAULT_SCENE_DURATION", 4.0))
    OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
    DEEPAI_URL = os.getenv("DEEPAI_URL", "https://api.deepai.org/api/text2img")


class AIVideoGenerator:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._check_dependencies()
        self._setup_credentials()

    def _check_dependencies(self) -> None:
        missing_deps = []
        if not GOOGLE_TTS_AVAILABLE:
            missing_deps.append("google-cloud-texttospeech")
        if not MOVIEPY_AVAILABLE:
            missing_deps.append("moviepy")
        if not PIL_AVAILABLE:
            missing_deps.append("pillow")
        if missing_deps:
            print("❌ Missing required dependencies:")
            for dep in missing_deps:
                print(f"   - {dep}")
            print("\nInstall them with:")
            print(f"pip install {' '.join(missing_deps)}")
            raise ImportError(f"Missing required dependencies: {', '.join(missing_deps)}")

    def _setup_credentials(self) -> None:
        if self.config.GOOGLE_CREDENTIALS_PATH:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.config.GOOGLE_CREDENTIALS_PATH

    def generate_script(self, concept: str) -> str:
        prompt = f"""Generate a 5-scene explanation of the concept '{concept}' for students in clear, simple English. 
Make sure the information is accurate and factually correct.
Each scene should contain:
- A short scene title
- One narration line (as speech)
- A brief description of what the visual should include

Format:
**Scene 1: Title Here**
**Speech:** "Narration text here"
**Visual:** Visual description here

**Scene 2: Title Here**
**Speech:** "Narration text here"
**Visual:** Visual description here

Continue for all 5 scenes."""

        headers = {
            "Authorization": f"Bearer {self.config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            print("🧠 Generating script with AI...")
            response = requests.post(
                self.config.OPENROUTER_URL,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content'].strip()

        except Exception as e:
            print(f"❌ OpenRouter API error: {e}")
            return self._get_fallback_script(concept)

    def _get_fallback_script(self, concept: str) -> str:
        return f"""**Scene 1: Introduction to {concept}**
**Speech:** "Let's explore how {concept} works step by step."
**Visual:** A student looking at a blackboard with educational content.

**Scene 2: Understanding the Basics**
**Speech:** "First, we need to understand the fundamental principles."
**Visual:** A clear diagram showing the basic concept.

**Scene 3: Step-by-Step Process**
**Speech:** "Now let's break down the process into manageable steps."
**Visual:** A flowchart showing the sequential steps.

**Scene 4: Practical Application**
**Speech:** "Here's how we apply this concept in real situations."
**Visual:** A practical example or demonstration.

**Scene 5: Summary and Conclusion**
**Speech:** "Let's review what we've learned about {concept}."
**Visual:** A summary graphic with key points highlighted."""

    def parse_scenes(self, script_text: str) -> List[Dict[str, str]]:
        scenes = []
        scene_blocks = re.split(r'\*\*Scene\s*\d+:\s*.*?\*\*', script_text)
        titles = re.findall(r'\*\*Scene\s*\d+:\s*(.*?)\*\*', script_text)

        for idx, block in enumerate(scene_blocks[1:]):  # skip first split chunk before Scene 1
            scene = {}
            scene['title'] = titles[idx].strip() if idx < len(titles) else f"Scene {idx+1}"

            speech_match = re.search(r'\*\*Speech:\*\*\s*"(.*?)"', block, re.DOTALL)
            if speech_match:
                scene['speech'] = speech_match.group(1).strip()
            else:
                speech_match = re.search(r'\*\*Speech:\*\*\s*(.+?)(?=\n|\*\*Visual:\*\*|$)', block, re.DOTALL)
                scene['speech'] = speech_match.group(1).strip() if speech_match else ""

            visual_match = re.search(r'\*\*Visual:\*\*\s*(.+?)(?=\n\*\*Scene|\n---|$)', block, re.DOTALL)
            scene['visual'] = visual_match.group(1).strip() if visual_match else ""

            if scene.get('title') and scene.get('speech'):
                scenes.append(scene)

        print(f"✅ Successfully parsed {len(scenes)} scenes")
        return scenes

    def generate_audio(self, text: str, filename: str) -> bool:
        if not GOOGLE_TTS_AVAILABLE:
            print("⚠️ Google TTS not available, creating silent audio")
            return self._create_silent_audio(text, filename)

        try:
            client_tts = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = client_tts.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            with open(filename, "wb") as out:
                out.write(response.audio_content)
            return True

        except Exception as e:
            print(f"❌ TTS error: {e}")
            return self._create_silent_audio(text, filename)

    def _create_silent_audio(self, text: str, filename: str) -> bool:
        if not MOVIEPY_AVAILABLE:
            print("❌ MoviePy not available, cannot create silent audio")
            return False

        try:
            duration = max(3.0, len(text) * 0.1)
            silent_audio = AudioClip(lambda t: [0, 0], duration=duration)
            silent_audio.write_audiofile(filename, logger=None, verbose=False)
            silent_audio.close()
            return True
        except Exception as e:
            print(f"❌ Fallback audio creation failed: {e}")
            return False

    def create_visual(self, scene: Dict[str, str], index: int) -> Optional[str]:
        prompt_text = scene.get("visual", "Educational illustration")
        image_path = f"scene_{index+1}.png"
        print(f"🖼️ Generating AI image for Scene {index+1}: {scene['title']}")

        if self._generate_deepai_image(prompt_text, image_path):
            return image_path

        if self._create_text_image(scene, image_path):
            print(f"✅ Fallback image created for scene {index+1}")
            return image_path

        return None

    def _generate_deepai_image(self, prompt: str, image_path: str) -> bool:
        try:
            response = requests.post(
                self.config.DEEPAI_URL,
                data={'text': prompt},
                headers={'api-key': self.config.DEEPAI_API_KEY},
                timeout=60
            )
            if response.status_code == 200:
                img_url = response.json().get('output_url')
                if img_url:
                    img_data = requests.get(img_url, timeout=30).content
                    with open(image_path, 'wb') as f:
                        f.write(img_data)
                    print(f"✅ DeepAI image created for {image_path}")
                    return True
        except Exception as e:
            print(f"❌ DeepAI failed: {e}")
        return False

    def _create_text_image(self, scene: Dict[str, str], image_path: str) -> bool:
        if not PIL_AVAILABLE:
            print("❌ PIL/Pillow not available, cannot create images")
            return False

        try:
            size = (self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT)
            img = Image.new('RGB', size, (70, 130, 180))
            draw = ImageDraw.Draw(img)

            try:
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            title = scene.get('title', 'Scene')
            if font_large:
                title_bbox = draw.textbbox((0, 0), title, font=font_large)
                title_width = title_bbox[2] - title_bbox[0]
                draw.text(
                    ((size[0] - title_width) // 2, 100),
                    title,
                    fill=(255, 255, 255),
                    font=font_large
                )

            visual = scene.get('visual', 'Visual description')
            if font_small and visual:
                wrapped_text = textwrap.fill(visual, width=50)
                lines = wrapped_text.split('\n')
                y_offset = 250

                for line in lines:
                    line_bbox = draw.textbbox((0, 0), line, font=font_small)
                    line_width = line_bbox[2] - line_bbox[0]
                    draw.text(
                        ((size[0] - line_width) // 2, y_offset),
                        line,
                        fill=(255, 255, 255),
                        font=font_small
                    )
                    y_offset += 30

            img.save(image_path)
            return True

        except Exception as e:
            print(f"❌ Text image creation failed: {e}")
            return False

    def create_scene_video(self, image_path: str, audio_path: str, scene_index: int) -> Optional[ImageClip]:
        if not MOVIEPY_AVAILABLE:
            print("❌ MoviePy not available, cannot create video clips")
            return None

        try:
            img_clip = ImageClip(image_path)

            if os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                img_clip = img_clip.set_duration(duration).set_audio(audio_clip)
            else:
                duration = self.config.DEFAULT_SCENE_DURATION
                img_clip = img_clip.set_duration(duration)

            img_clip = img_clip.resize(newsize=(self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT))

            print(f"✅ Scene {scene_index + 1} video clip created (duration: {duration:.1f}s)")
            return img_clip

        except Exception as e:
            print(f"❌ Failed to create video clip for scene {scene_index + 1}: {e}")
            return None

    def create_final_video(self, scenes: List[Dict[str, str]]) -> str:
        clips = []
        successful_scenes = 0

        for i, scene in enumerate(scenes):
            print(f"\n🎬 Processing Scene {i+1}: {scene.get('title', 'Untitled')}")

            audio_file = f"scene_{i+1}.mp3"

            if self.generate_audio(scene.get("speech", ""), audio_file):
                print(f"✅ Audio generated for scene {i+1}")
            else:
                print(f"⚠️ Audio generation failed for scene {i+1}")

            image_file = self.create_visual(scene, i)
            if not image_file or not os.path.exists(image_file):
                print(f"❌ Image generation failed for scene {i+1}, skipping scene")
                continue

            video_clip = self.create_scene_video(image_file, audio_file, i)
            if video_clip:
                clips.append(video_clip)
                successful_scenes += 1
            else:
                print(f"❌ Video clip creation failed for scene {i+1}")

        print(f"\n📊 Successfully created {successful_scenes}/{len(scenes)} video clips")

        if not clips:
            raise ValueError("No video clips were created successfully. Please check your API keys and settings.")

        if len(clips) < len(scenes):
            print(f"⚠️ Warning: Only {len(clips)} out of {len(scenes)} scenes were created successfully")

        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is required for video assembly. Install with: pip install moviepy")

        try:
            print("🎬 Concatenating video clips...")
            final = concatenate_videoclips(clips, method="compose")
            final_path = "final_explainer_video.mp4"

            print("💾 Writing final video file...")
            final.write_videofile(
                final_path,
                fps=self.config.VIDEO_FPS,
                codec='libx264',
                audio_codec='aac'
            )

            for clip in clips:
                clip.close()
            final.close()

            return final_path

        except Exception as e:
            print(f"❌ Error creating final video: {e}")
            raise

    def generate_video(self, concept: str) -> str:
        print(f"🚀 Starting video generation for concept: '{concept}'")
        try:
            raw_script = self.generate_script(concept)
            print("\n📜 Script Generated:")
            print("-" * 50)
            print(raw_script)
            print("-" * 50)

            scenes = self.parse_scenes(raw_script)
            if not scenes:
                raise ValueError("No scenes were parsed from the script")

            print(f"\n🎯 Found {len(scenes)} scenes to process:")
            for i, scene in enumerate(scenes, 1):
                print(f"  Scene {i}: {scene.get('title', 'Untitled')}")

            print("\n🎞️ Creating video scenes and assembling final video...")
            output_path = self.create_final_video(scenes)
            print(f"\n✅ Video generation completed successfully!")
            print(f"📁 Final video saved as: {output_path}")

            return output_path

        except Exception as e:
            print(f"\n❌ Video generation failed: {e}")
            traceback.print_exc()
            raise


def main():
    config = Config()

    config.DEEPAI_API_KEY = "8956382d-2c37-4670-a1b6-c1b3fd39069f"
    config.OPENROUTER_API_KEY = "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"

    generator = AIVideoGenerator(config)
    concept = "Large Language Models"
    try:
        output_path = generator.generate_video(concept)
        try:
            from IPython.display import Video, display
            display(Video(output_path, embed=True, width=640, height=360))
        except ImportError:
            print("📺 Video created successfully! Open the file to view it.")
    except Exception as e:
        print(f"❌ Application failed: {e}")


if __name__ == "__main__":
    main()