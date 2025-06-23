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
pip install python-dotenv

For Google Cloud TTS, you'll also need to:
1. Create a Google Cloud project
2. Enable the Text-to-Speech API
3. Create a service account key
4. Set the path to your service account key in the .env file

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
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    print("⚠️ python-dotenv not available. Install with: pip install python-dotenv")
    DOTENV_AVAILABLE = False

# Handle missing dependencies gracefully
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    print("⚠️ Google Cloud Text-to-Speech not available. Install with: pip install google-cloud-texttospeech")
    GOOGLE_TTS_AVAILABLE = False
    texttospeech = None

try:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, AudioClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    print("⚠️ MoviePy not available. Install with: pip install moviepy")
    MOVIEPY_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    print("⚠️ PIL/Pillow not available. Install with: pip install pillow")
    PIL_AVAILABLE = False


class Config:
    """Configuration settings for the AI Video Generator."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load API credentials from environment
        self.GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.DEEPAI_API_KEY = os.getenv('DEEPAI_API_KEY')
        self.OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
        
        # Video Settings
        self.VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', '900'))
        self.VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', '600'))
        self.VIDEO_FPS = int(os.getenv('VIDEO_FPS', '24'))
        self.DEFAULT_SCENE_DURATION = float(os.getenv('DEFAULT_SCENE_DURATION', '4.0'))
        
        # API URLs
        self.OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
        self.DEEPAI_URL = "https://api.deepai.org/api/text2img"
        
        # Validate required credentials
        self._validate_credentials()
    
    def _validate_credentials(self):
        """Validate that required API credentials are present."""
        missing_keys = []
        
        if not self.OPENROUTER_API_KEY:
            missing_keys.append('OPENROUTER_API_KEY')
        
        if not self.DEEPAI_API_KEY:
            missing_keys.append('DEEPAI_API_KEY')
            
        if GOOGLE_TTS_AVAILABLE and not self.GOOGLE_CREDENTIALS_PATH:
            missing_keys.append('GOOGLE_APPLICATION_CREDENTIALS')
            
        if missing_keys:
            print("❌ Missing required environment variables:")
            for key in missing_keys:
                print(f"   - {key}")
            print("\nPlease check your .env file and ensure all required keys are set.")


class AIVideoGenerator:
    """Main class for generating educational explainer videos."""
    
    def __init__(self, config: Config = None):
        """Initialize the AI Video Generator with configuration."""
        self.config = config or Config()
        self._check_dependencies()
        self._setup_credentials()
    
    def _check_dependencies(self) -> None:
        """Check if all required dependencies are available."""
        missing_deps = []
        
        if not DOTENV_AVAILABLE:
            missing_deps.append("python-dotenv")
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
        """Set up API credentials and environment variables."""
        if self.config.GOOGLE_CREDENTIALS_PATH and os.path.exists(self.config.GOOGLE_CREDENTIALS_PATH):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.config.GOOGLE_CREDENTIALS_PATH
        elif GOOGLE_TTS_AVAILABLE:
            print("⚠️ Google credentials file not found. TTS will use fallback audio.")
        
    def generate_script(self, concept: str) -> str:
        """
        Generate an educational script for the given concept using OpenRouter API.
        
        Args:
            concept: The educational concept to explain
            
        Returns:
            Generated script text
        """
        prompt = f"""Generate a 5-scene explanation of the concept '{concept}' for students in clear, simple English. 
Make sure the information is accurate and factually correct.
Each scene should contain:
- A short scene title
- One narration line (as speech)
- A brief description of what the visual should include

Format:
Scene 1:
Title: ...
Speech: ...
Visual: ..."""
        
        headers = {
            "Authorization": f"Bearer {self.config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:3000",  # Required by OpenRouter
            "X-Title": "AI Video Generator"  # Optional but recommended
        }
        payload = {
            "model": "openai/gpt-4o-mini",  # Updated model name format
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            print("🧠 Generating script with AI...")
            print(f"🔑 Using API key: {self.config.OPENROUTER_API_KEY[:20]}...")
            response = requests.post(
                self.config.OPENROUTER_URL, 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            
            if response.status_code == 401:
                print("❌ Authentication failed. Please check your OpenRouter API key.")
                print("💡 Make sure your API key is valid and has sufficient credits.")
            
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"❌ OpenRouter API error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            return self._get_fallback_script(concept)
    
    def _get_fallback_script(self, concept: str) -> str:
        """Generate a fallback script when API fails."""
        return f"""Scene 1:
Title: Introduction to {concept}
Speech: Let's explore how {concept} works step by step.
Visual: A student looking at a blackboard with educational content.

Scene 2:
Title: Understanding the Basics
Speech: First, we need to understand the fundamental principles.
Visual: A clear diagram showing the basic concept.

Scene 3:
Title: Step-by-Step Process
Speech: Now let's break down the process into manageable steps.
Visual: A flowchart showing the sequential steps.

Scene 4:
Title: Practical Application
Speech: Here's how we apply this concept in real situations.
Visual: A practical example or demonstration.

Scene 5:
Title: Summary and Conclusion
Speech: Let's review what we've learned about {concept}.
Visual: A summary graphic with key points highlighted."""

    def parse_scenes(self, script_text: str) -> List[Dict[str, str]]:
        """
        Parse the generated script into individual scenes.
        
        Args:
            script_text: Raw script text from AI generation
            
        Returns:
            List of scene dictionaries with title, speech, and visual keys
        """
        scenes = []
        scene_blocks = re.split(r'Scene\s*\d+:', script_text)
        
        for block in scene_blocks[1:]:  # Skip first empty block
            scene = {}
            
            # Extract title
            title_match = re.search(r'Title:\s*(.+?)(?=\n|Speech:|$)', block, re.IGNORECASE)
            if title_match:
                scene['title'] = title_match.group(1).strip()
            
            # Extract speech
            speech_match = re.search(r'Speech:\s*(.+?)(?=\n|Visual:|$)', block, re.IGNORECASE | re.DOTALL)
            if speech_match:
                scene['speech'] = speech_match.group(1).strip()
            
            # Extract visual description
            visual_match = re.search(r'Visual:\s*(.+?)(?=Scene\s*\d+:|$)', block, re.IGNORECASE | re.DOTALL)
            if visual_match:
                scene['visual'] = visual_match.group(1).strip()
            
            # Only add scene if it has required components
            if scene.get('title') and scene.get('speech'):
                scenes.append(scene)
        
        print(f"✅ Successfully parsed {len(scenes)} scenes")
        return scenes

    def generate_audio(self, text: str, filename: str) -> bool:
        """
        Generate audio narration using Google Text-to-Speech.
        
        Args:
            text: Text to convert to speech
            filename: Output audio filename
            
        Returns:
            Success status
        """
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
        """Create silent audio as fallback when TTS fails."""
        if not MOVIEPY_AVAILABLE:
            print("❌ MoviePy not available, cannot create silent audio")
            return False
            
        try:
            duration = max(3.0, len(text) * 0.1)  # Estimate duration
            silent_audio = AudioClip(lambda t: [0, 0], duration=duration)
            silent_audio.write_audiofile(filename, logger=None, verbose=False)
            silent_audio.close()
            return True
        except Exception as e:
            print(f"❌ Fallback audio creation failed: {e}")
            return False

    def create_visual(self, scene: Dict[str, str], index: int) -> Optional[str]:
        """
        Generate visual image for a scene using DeepAI or fallback method.
        
        Args:
            scene: Scene dictionary containing visual description
            index: Scene index for filename
            
        Returns:
            Path to generated image file or None if failed
        """
        prompt_text = scene.get("visual", "Educational illustration")
        image_path = f"scene_{index+1}.png"
        
        print(f"🖼️ Generating AI image for Scene {index+1}: {scene['title']}")
        
        # Try DeepAI first
        if self._generate_deepai_image(prompt_text, image_path):
            return image_path
            
        # Fallback to text-based image
        if self._create_text_image(scene, image_path):
            print(f"✅ Fallback image created for scene {index+1}")
            return image_path
            
        return None
    
    def _generate_deepai_image(self, prompt: str, image_path: str) -> bool:
        """Generate image using DeepAI API."""
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
        """Create a text-based image as fallback."""
        if not PIL_AVAILABLE:
            print("❌ PIL/Pillow not available, cannot create images")
            return False
            
        try:
            size = (self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT)
            img = Image.new('RGB', size, (70, 130, 180))  # Steel blue background
            draw = ImageDraw.Draw(img)
            
            # Try to load fonts
            try:
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw title
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
            
            # Draw visual description
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
        """
        Create a video clip for a single scene.
        
        Args:
            image_path: Path to scene image
            audio_path: Path to scene audio
            scene_index: Index of the scene
            
        Returns:
            MoviePy ImageClip or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            print("❌ MoviePy not available, cannot create video clips")
            return None
            
        try:
            # Load image with PIL first to ensure compatibility
            if PIL_AVAILABLE:
                from PIL import Image
                pil_img = Image.open(image_path)
                # Convert to RGB if necessary
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                # Resize using modern PIL resampling
                try:
                    # Try modern approach first (Pillow >= 10.0.0)
                    pil_img = pil_img.resize((self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT), Image.Resampling.LANCZOS)
                except AttributeError:
                    # Fallback for older Pillow versions
                    try:
                        pil_img = pil_img.resize((self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT), Image.LANCZOS)
                    except AttributeError:
                        # Ultimate fallback
                        pil_img = pil_img.resize((self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT))
                
                # Save the processed image temporarily
                temp_image_path = f"temp_scene_{scene_index+1}.png"
                pil_img.save(temp_image_path)
                pil_img.close()
                
                # Create ImageClip from processed image
                img_clip = ImageClip(temp_image_path)
            else:
                img_clip = ImageClip(image_path)
                img_clip = img_clip.resize(newsize=(self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT))
            
            # Set duration based on audio or default
            if os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                img_clip = img_clip.set_duration(duration).set_audio(audio_clip)
            else:
                duration = self.config.DEFAULT_SCENE_DURATION
                img_clip = img_clip.set_duration(duration)
            
            print(f"✅ Scene {scene_index + 1} video clip created (duration: {duration:.1f}s)")
            return img_clip
            
        except Exception as e:
            print(f"❌ Failed to create video clip for scene {scene_index + 1}: {e}")
            traceback.print_exc()  # Add detailed error info for debugging
            return None

    def create_final_video(self, scenes: List[Dict[str, str]]) -> str:
        """
        Create the final assembled video from all scenes.
        
        Args:
            scenes: List of scene dictionaries
            
        Returns:
            Path to final video file
        """
        clips = []
        successful_scenes = 0
        
        for i, scene in enumerate(scenes):
            print(f"\n🎬 Processing Scene {i+1}: {scene.get('title', 'Untitled')}")
            
            audio_file = f"scene_{i+1}.mp3"
            
            # Generate audio
            if self.generate_audio(scene.get("speech", ""), audio_file):
                print(f"✅ Audio generated for scene {i+1}")
            else:
                print(f"⚠️ Audio generation failed for scene {i+1}")

            # Generate image
            image_file = self.create_visual(scene, i)
            if not image_file or not os.path.exists(image_file):
                print(f"❌ Image generation failed for scene {i+1}, skipping scene")
                continue

            # Create video clip
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

        # Assemble final video
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
            
            # Clean up resources
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            try:
                final.close()
            except:
                pass
            
            # Clean up temporary files
            for i in range(len(scenes)):
                temp_files = [
                    f"temp_scene_{i+1}.png",
                    f"scene_{i+1}.mp3",
                    f"scene_{i+1}.png"
                ]
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except:
                        pass
            
            return final_path
            
        except Exception as e:
            print(f"❌ Error creating final video: {e}")
            raise

    def generate_video(self, concept: str) -> str:
        """
        Main method to generate a complete educational video.
        
        Args:
            concept: Educational concept to explain
            
        Returns:
            Path to generated video file
        """
        print(f"🚀 Starting video generation for concept: '{concept}'")
        
        try:
            # Generate script
            raw_script = self.generate_script(concept)
            print("\n📜 Script Generated:")
            print("-" * 50)
            print(raw_script)
            print("-" * 50)
            
            # Parse scenes
            scenes = self.parse_scenes(raw_script)
            if not scenes:
                raise ValueError("No scenes were parsed from the script")
            
            print(f"\n🎯 Found {len(scenes)} scenes to process:")
            for i, scene in enumerate(scenes, 1):
                print(f"  Scene {i}: {scene.get('title', 'Untitled')}")
            
            # Create final video
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
    """Main execution function."""
    try:
        # Initialize generator
        generator = AIVideoGenerator()
        
        # Get concept from user or use default
        concept = input("Enter the concept you want to explain (or press Enter for 'Large Language Models'): ").strip()
        if not concept:
            concept = "Large Language Models"
        
        # Generate video
        output_path = generator.generate_video(concept)
        
        print(f"\n🎉 Success! Your educational video has been created: {output_path}")
        print("📺 You can now open the video file to view your explainer video!")
            
    except Exception as e:
        print(f"❌ Application failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())