# 🧠 MindSync AI - Student Success & Wellness Platform

MindSync AI is an enterprise-grade, AI-powered student success and wellness platform developed using the **Django MVT (Model-View-Template)** architecture with a **PostgreSQL** database. The platform integrates intelligent learning assistance, academic telemetry, AI-powered study material generation, and personalized planning into a single web application.

---

# 📖 Table of Contents

- [Overview](#-overview)
- [Core Features](#-core-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation Guide](#-installation-guide)
- [Environment Variables](#-environment-variables)
- [Database Migration](#-database-migration)
- [Running the Project](#-running-the-project)
- [Application Architecture](#-application-architecture)
- [Database Schema](#-database-schema)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

# 📌 Overview

MindSync AI is designed to improve students' academic performance and learning experience using Artificial Intelligence.

The platform enables students and teachers to:

- 🔐 Securely authenticate into the system
- 📊 Track academic performance
- 🤖 Generate AI-powered study notes
- 📝 Create quizzes automatically
- 🧠 Generate flashcards
- 📈 Predict future GPA
- 💬 Chat with an AI Study Coach
- 📅 Plan study schedules
- 📚 Discover learning resources

The application follows a modular Django architecture where every major functionality is implemented inside an independent Django app.

---

# 🚀 Core Features

## 👤 Authentication & Role-Based Access

- Secure Login & Registration
- Django Password Hashing (PBKDF2)
- Student Dashboard
- Teacher Dashboard
- Session Authentication
- Role-Based Access Control (RBAC)

---

## 🤖 AI Study Engine

The AI Engine supports:

- PDF Upload
- TXT Upload
- Markdown Upload
- AI Notes Generation
- Flashcard Generation
- Quiz Generation
- Key Concept Extraction
- Personalized AI Study Coach

Powered by **Google Gemini API**.

---

## 📊 Academic Dashboard

Students can monitor:

- Daily Study Hours
- Wellness Score
- Academic Progress
- Performance Analytics
- Historical Telemetry

---

## 🎯 GPA Prediction

Features include:

- Current CGPA Tracking
- Semester Simulation
- GPA Forecasting
- Academic Performance Prediction

---

## 📅 Smart Planner

Planner Module provides:

- Study Planning
- Cached Learning Resources
- Topic Discovery
- Personalized Recommendations

---

# 🛠 Technology Stack

| Layer | Technology |
|--------|------------|
| Backend | Django 6.x |
| Programming Language | Python 3.13+ |
| Frontend | HTML5 |
| Styling | CSS3 |
| UI Framework | Tailwind CSS |
| JavaScript | Vanilla JavaScript (ES6+) |
| Database | PostgreSQL |
| ORM | Django ORM |
| AI Engine | Google Gemini 1.5 Pro |

---

# 📂 Project Structure

```text
MindSync/
│
├── apps/
│   ├── authentication/
│   ├── dashboard/
│   ├── ai_engines/
│   └── planner/
│
├── mindsync_core/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── manage.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

# ⚙️ Installation Guide

## Step 1 — Clone Repository

```bash
git clone https://github.com/your-username/MindSync.git

cd MindSync
```

---

## Step 2 — Create Virtual Environment

### Windows

```bash
python -m venv env

env\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv env

source env/bin/activate
```

---

## Step 3 — Install Dependencies

```bash
pip install --upgrade pip

pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file in the project root.

```env
DEBUG=True

SECRET_KEY=your_secret_key

DB_NAME=mindsync_db

DB_USER=postgres

DB_PASSWORD=your_password

DB_HOST=localhost

DB_PORT=5432

GEMINI_API_KEY=your_google_gemini_api_key
```

> ⚠️ **Never upload your `.env` file or API keys to GitHub.**

---

# 🗄 Database Migration

Run the following commands:

```bash
python manage.py makemigrations

python manage.py migrate
```

---

# 👤 Create Superuser

```bash
python manage.py createsuperuser
```

---

# ▶️ Running the Project

```bash
python manage.py runserver
```

Open your browser and visit:

```
http://127.0.0.1:8000/
```

---
# 🏗 Application Architecture

```text
                    Client Browser
                          │
                          ▼
                 Django URL Dispatcher
                          │
                          ▼
                  Views (Business Logic)
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
 Authentication      AI Engines      Dashboard
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                     Django ORM
                          │
                          ▼
                  PostgreSQL Database
                          │
                          ▼
                 Google Gemini API
```

---

# 📦 Django Applications

The project is divided into independent Django applications for better maintainability and scalability.

## 🔐 Authentication

Responsible for:

- User Registration
- User Login
- Logout
- Role-Based Authentication
- Student & Teacher Profiles

---

## 📊 Dashboard

Responsible for:

- Student Dashboard
- Teacher Dashboard
- Academic Telemetry
- CGPA Prediction
- Performance Analytics
- Semester Simulation

---

## 🤖 AI Engines

Responsible for:

- PDF Parsing
- TXT Processing
- Markdown Processing
- AI Notes Generation
- Flashcard Generation
- Quiz Generation
- AI Study Coach
- Google Gemini Integration

---

## 📅 Planner

Responsible for:

- Study Planner
- Cached Learning Resources
- Topic Search
- Resource Discovery
- Learning Recommendations

---

# 🗄 Database Schema

The application uses PostgreSQL as the primary relational database.

## Main Database Tables

| Table | Description |
|-------|-------------|
| authentication_user | Stores user authentication information |
| student_profile | Student academic profile |
| teacher_profile | Teacher profile |
| CompleteStudentTelemetry | Daily study and wellness logs |
| UploadedMaterial | Uploaded learning resources |
| GeneratedStudyPack | AI-generated notes and quizzes |
| AICoachConversation | AI Coach conversation history |
| TopicResourceCache | Cached educational resources |

---

## Entity Relationships

```text
User
 │
 ├──────── Student Profile
 │
 ├──────── Teacher Profile
 │
 ├──────── Uploaded Material
 │                │
 │                ▼
 │       Generated Study Pack
 │
 ├──────── AI Coach Conversations
 │
 └──────── Student Telemetry
```

---

# 🤖 AI Workflow

The AI pipeline follows the workflow below.

```text
Upload PDF / TXT / Markdown
              │
              ▼
      Extract Raw Text
              │
              ▼
     Google Gemini API
              │
              ▼
      AI Processing Engine
              │
     ┌────────┼───────────┐
     ▼        ▼           ▼
 Summary  Flashcards    Quiz
              │
              ▼
      Stored in Database
```

---

# 📊 Key Features Summary

| Feature | Status |
|---------|:------:|
| User Authentication | ✅ |
| Student Dashboard | ✅ |
| Teacher Dashboard | ✅ |
| PostgreSQL Database | ✅ |
| Google Gemini API | ✅ |
| AI Notes Generator | ✅ |
| Flashcards | ✅ |
| Quiz Generator | ✅ |
| AI Study Coach | ✅ |
| Study Planner | ✅ |
| Telemetry Analytics | ✅ |
| GPA Prediction | ✅ |

---

# 📁 Important Files

| File | Purpose |
|------|---------|
| manage.py | Django management commands |
| settings.py | Global Django configuration |
| urls.py | URL routing |
| wsgi.py | Production WSGI entry point |
| asgi.py | ASGI configuration |
| requirements.txt | Python dependencies |
| README.md | Project documentation |
| .gitignore | Git ignored files |

---
# 🔌 Google Gemini API Integration

MindSync AI integrates with the Google Gemini API to provide intelligent learning assistance.

### AI Features

- 📄 AI Notes Generation
- 📝 Quiz Generation
- 🧠 Flashcard Generation
- 🎯 Key Concept Extraction
- 💬 AI Study Coach

---

# 🧪 Running Tests

Run the test suite using:

```bash
python manage.py test
```

---

# 🚀 Deployment

This project can be deployed on any cloud platform that supports Python and Django.

## Recommended Platforms

- Render
- Railway
- PythonAnywhere
- DigitalOcean
- AWS EC2
- Azure App Service

### Production Stack

- Django
- Gunicorn
- WhiteNoise
- PostgreSQL
- Google Gemini API

---

# 🌟 Future Improvements

The following features are planned for future releases:

- Email Verification
- Password Reset via Email
- AI Chat Memory
- Attendance Tracking
- Assignment Submission Portal
- Teacher Analytics Dashboard
- Student Performance Reports
- Notification System
- REST API Support
- Docker Deployment
- CI/CD Pipeline
- Mobile Application

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository

2. Create a new branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push your branch

```bash
git push origin feature-name
```

5. Open a Pull Request

---

# 📜 License

This project is licensed under the **MIT License**.

Feel free to use, modify, and distribute this project according to the license terms.

---

# 👨‍💻 Developer

**Eman Zahid**

BS Computer Science Student

### Skills

- Python
- Django
- PostgreSQL
- HTML5
- CSS3
- JavaScript
- Tailwind CSS
- Artificial Intelligence
- Google Gemini API

---

# ⭐ Support

If you found this project helpful, please consider giving it a **⭐ Star** on GitHub.

It helps others discover the project and motivates future development.

---

# 🙏 Acknowledgements

Special thanks to:

- Django Framework
- PostgreSQL
- Google Gemini API
- Tailwind CSS
- Open Source Community

---

<p align="center">

Made with ❤️ using Django, PostgreSQL & Google Gemini AI

</p>
