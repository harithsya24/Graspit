# 🎓 GraspIt: Type It, Watch It, Learn It

**GraspIt** is a revolutionary tool that turns *any educational concept* into a complete explainer video — all in under 2 minutes. Just enter a topic like **"IP Address"**, and watch as GraspIt generates a 5-scene educational video with narration, visuals, and smooth transitions, fully automated using cutting-edge AI.

---

## 🌟 Features

- 💬 **GPT-4 Script Generation** via OpenRouter  
  Converts any concept into a 5-scene educational script, including narration and visual cues.

- 🔊 **Realistic Narration** using Google Cloud Text-to-Speech  
  Produces natural, human-like voiceovers for each scene.

- 🖼️ **AI Image Generation** with DeepAI  
  Creates custom illustrations for each scene based on the script.

- 🎬 **Video Assembly** with MoviePy  
  Combines images and audio into a polished, high-quality MP4 video.

---

## 📦 Installation

Install all required packages using `pip`:

```bash
pip install google-cloud-texttospeech moviepy pillow requests python-dotenv
```
---

## 🔐 API Setup

You’ll need API keys and credentials from the following platforms:

### 1. Google Cloud TTS

* Create a project at: [https://console.cloud.google.com/](https://console.cloud.google.com/)
* Enable **Text-to-Speech API**
* Create a Service Account → Download JSON key
* Save your key as `service-account.json`

### 2. OpenRouter API (GPT-4)

* Visit: [https://openrouter.ai](https://openrouter.ai)
* Generate an API key

### 3. DeepAI API

* Visit: [https://deepai.org](https://deepai.org)
* Create an account → Get API key

---

## 🛠 .env File Setup

Create a `.env` file in your project root:

```bash
 ⁠env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
OPENROUTER_API_KEY=your_openrouter_key
DEEPAI_API_KEY=your_deepai_key
VIDEO_WIDTH=900
VIDEO_HEIGHT=600
VIDEO_FPS=24
DEFAULT_SCENE_DURATION=4.0
```

⁠ ---

## 🚀 Usage

From your terminal or Google Colab, run:

 ⁠```bash
python main.py

```
When prompted, type your concept (e.g., `IP Address`, `Photosynthesis`, `Blockchain`).

GraspIt will:

1. Generate a 5-scene script
2. Convert narration to audio
3. Create relevant visuals
4. Assemble the video
5. Output: `final_explainer_video.mp4`

---

## 🧪 Demo Output Example

> Concept: **"Photosynthesis"**

🎞️ Output:

* 5 structured scenes
* Voice-over narration
* AI-generated visuals
* Smooth scene transitions

📁 Final File: `final_explainer_video.mp4`

---

## 🧠 How It Works

1. **Script Creation**
   Sends your topic to GPT-4 via OpenRouter → Receives 5 scenes with narration and visuals.

2. **Text-to-Speech**
   Google Cloud TTS converts narration into professional-quality voiceovers.

3. **Image Generation**
   Visual descriptions are sent to DeepAI to create illustrations for each scene.

4. **Video Editing**
   Uses MoviePy to combine images and audio into a cohesive video.

---

## ✅ Accomplishments

* Built an end-to-end AI orchestration system
* Integrated multiple APIs and handled fallbacks
* Generated educational videos in < 2 minutes
* Seamless visual and audio sync

---

## 🧠 What We Learned

* Handling asynchronous API responses
* Fallback strategies for failed API calls
* Automating educational content workflows
* Audio-video alignment and compression

---

## 🔮 What's Next for GraspIt

* 🌐 Web-based interface for drag-and-drop concepts
* 🎙️ Support for multilingual narration (Kannada, Hindi, etc.)
* 📚 Batch generation for syllabus-based content
* 📺 YouTube / Google Classroom integration
* 📝 Subtitles and closed captions

---

## 💡 Tagline

> “From concept to classroom — in under 2 minutes.”

---

## 🧑‍💻 Author

**Amrutha Kanakatte Ravishankar**
**Sneha Venkatesh**
Version: `1.0`
License: [MIT License](LICENSE)

---

## 📁 Project Structure

```bash
graspit/
├── main.py
├── .env
├── final_explainer_video.mp4
├── scene_*.mp3 / .png (temporary files)
└── README.md

```

---

## 📜 License

This project is licensed under the MIT License.
See the [LICENSE](LICENSE) file for details.



