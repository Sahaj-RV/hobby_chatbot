# 🤖 AI Hobby Discovery Platform

An intelligent, AI-powered chatbot that helps users discover hobbies tailored to their personality, interests, mood, and goals using Generative AI APIs.

---

## 🚀 Live Demo
🔗 https://hobby-chatbot-k5qh.onrender.com/

---

## 📌 Overview

The **AI Hobby Discovery Platform (HobbyBot)** is a domain-specific Generative AI chatbot designed to solve a real-world problem:  
👉 *“People struggle to find hobbies that truly fit them.”*

This platform interacts with users through a conversational interface, analyzes their preferences, and generates **personalized hobby recommendations** along with actionable guidance.

---

## ✨ Features

- 🎯 **Personalized Hobby Recommendations**
- 🧠 **Quiz-Based User Profiling**
- ⚡ **Real-Time AI Response Streaming (SSE)**
- 🔄 **Multi-Model Fallback (Claude → Grok → Gemini)**
- 😊 **Mood-Based Suggestions**
- 📈 **30-60-90 Day Hobby Roadmap Generator**
- 🔐 **OTP-Based Authentication System**
- 💬 **Session-Based Chat Memory**
- 🌐 **Public Profile Sharing**

---

## 🧠 Tech Stack

**Frontend:**
- HTML
- CSS
- JavaScript

**Backend:**
- Python (Flask)

**AI APIs:**
- Claude (Anthropic)
- Grok (via Groq API)
- Google Gemini

**Other:**
- SQLite (Database)
- Render (Deployment)

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Sahaj-RV/hobby_chatbot.git
cd hobby_chatbot

python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3. Install Dependencies
pip install -r requirements.txt

4. Setup Environment Variables

Create a .env file and add:

GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
SECRET_KEY=your_secret_key

5. Run the Application
python app.py

🏗️ System Architecture
User → Frontend → Flask Backend → AI APIs → Response → UI

👨‍💻 Author

Sahaj Singh
B.Tech CSE

📜 License

This project is licensed under the MIT License.
⭐ Acknowledgement

This project was developed as part of a Project-Based Assessment on Generative AI Chatbots, focusing on solving real-world problems using modern AI technologies.
