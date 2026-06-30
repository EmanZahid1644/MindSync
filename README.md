# MindSync AI - Student Success & Wellness Platform

MindSync AI is an enterprise-grade, web-based student success, telemetry analytics, and AI-driven pedagogical assistance platform. Built on a highly modular Django Model-View-Template (MVT) architecture and backed by a robust PostgreSQL relational database, the platform integrates intelligent document parsing with third-party generative AI pipelines (Google Gemini API) to synthesize custom learning materials while actively tracking multi-dimensional academic indicators.

---

## 🚀 Key Features

### 👤 Identity & Role-Based Access Control (RBAC)
* **Secure Authentication:** Powered by Django's native PBKDF2 hashing algorithm with SHA-256 signatures.
* **Granular Authorization:** Structural separation between Student and Teacher workspaces via distinct database profile extensions (`student_profile` vs. `teacher_profile`).
* **Dynamic UI Layouts:** Client-side interfaces fluidly render features depending on active authentication flags.

### 🧠 AI Ingestion & Synthesis Engine (`ai_engines`)
* **Document Stream Pipeline:** Ingests raw `.pdf`, `.txt`, and `.md` file structures up to 5MB.
* **Dynamic Study Packs:** Extracts textual content and dispatches structured context-prompts to the Google Gemini API (`gemini-1.5-pro`).
* **Structured Output Engineering:** Enforces strict programmatic JSON parsing to seamlessly map responses into reusable UI flashcards and interactive quiz components.
* **AI Coach:** Maintains persistent multi-turn conversational records (`AICoachConversation`) leveraging user-specific contextual recommendations.

### 📊 Telemetry Tracking & Predictive Analytics (`dashboard`)
* **Time-Series Performance Logging:** Records daily metrics including study allocations and self-reported biometric wellness indicators.
* **GPA Projection Engine:** Executes deterministic linear interpolation algorithms to forecast future CGPA trends based on simulated academic variable changes.

### ⚡ Optimization & Resource Discovery (`planner`)
* **Zero-Redundancy Registry:** Implements a localized database lookup caching mechanism (`TopicResourceCache`) to eliminate duplicate external lookup lookups and optimize retrieval latency.

---

## 🛠️ Technology Stack

| Layer | Component Technology | Version / Spec |
| :--- | :--- | :--- |
| **Front-End** | HTML5 / CSS3 / JavaScript (ES6+) | Vanilla ECMA, Dynamic DOM |
| **UI Framework** | Tailwind CSS | v3.4+ Production |
| **Back-End** | Python / Django Framework | Python v3.13+ / Django v6.x LTS |
| **Database** | PostgreSQL | v16+ Core Cluster |
| **AI Processing**| Google Gemini API | `gemini-1.5-pro` SDK |

---

## 📂 System Directory Structure

```text
mindsync_root/
│
├── mindsync_core/              # Core System Setting Engine
│   ├── settings.py            # Main Global Project Settings
│   └── urls.py                # Main System Root Routing Engine
│
├── authentication/            # User Custom Identity Management Sub-app
│   ├── models.py              # Identity Database Tables Schema Definitions
│   ├── views.py               # User Verification & Dynamic Access Controls
│   └── templates/             # Onboarding Login/Signup Layout Interfaces
│
├── dashboard/                 # Metric Performance Telemetry Processing Engine
│   ├── models.py              # Telemetry, Simulation, and Linear Tracker Logs
│   └── views.py               # Computational Models & View Layout Assemblers
│
├── ai_engines/                # Generative Processing Automation Core Module
│   ├── models.py              # Extracted Notes Data and JSON Serialization Maps
│   ├── pipeline.py            # Low-Level Google Gemini API Connection Wrappers
│   └── views.py               # Multi-Stream Ingestion Ingestion Processing Orchestration
│
└── planner/                   # Strategy Discovery Engine Layout
    ├── models.py              # Local Database Network Cache Maps
    └── views.py               # Search Route Operations Controllers
## 💻 Installation & Local Environment Setup
### Follow these precise steps to provision a local deployment runtime instance of MindSync AI.

### Prerequisite Checklist
Python 3.13 or higher installed.

PostgreSQL 16 server active instance running locally.

A valid Google Gemini API Key access token.

### Step 1: Clone the Repository
### Step 2: Establish a Virtual Environment
python -m venv venv
# On Windows Activation:
venv\Scripts\activate
# On macOS/Linux Activation:
source venv/bin/activate

###Step 3: Install Required System Dependencies
pip install --upgrade pip
pip install -r requirements.txt

###Step 4: Environment Variables Configuration
Create a .env configuration file within the root directory root workspace:
DEBUG=True
SECRET_KEY=django-insecure-production-fallback-token-key
DB_NAME=mindsync_db
DB_USER=postgres
DB_PASSWORD=your_secure_postgresql_password
DB_HOST=127.0.0.1
DB_PORT=5432
GEMINI_API_KEY=AIzaSyYourActualGoogleGeminiAPIKeyToken Here

### Step 5: Database Provisioning & Schema Migrations
Initialize your PostgreSQL database cluster, verify that the database named mindsync_db exists, then run the active migrations to generate system relational tables:

Bash
python manage.py makemigrations
python manage.py migrate

### Step 6: Initialize an Administrative Superuser Account
Bash
python manage.py createsuperuser

### Step 7: Launch the Local Development Web Server
Bash
python manage.py runserver
The application will boot up and map local listening ports securely at: http://127.0.0.1:8000/

## 🗺️ System Architecture Blueprint

    subsc1[Client Browser: HTML5/Tailwind/JS] --- HTTP[Secure HTTP / JSON]
    
    subgraph Web_Application_Server [Django Application Tier]
        HTTP --> Routing[Django URL Dispatcher]
        Routing --> Controllers[Django Views & App Logic]
        Controllers --> Context[MVT Template Processor Engine]
        Context --> subsc1
    end
    
    subgraph Persistent_Data_Tier [Infrastructure Store]
        Controllers --- ORM[Django ORM Object Mapping]
        ORM --> DB[(PostgreSQL Database Instance)]
    end
    
    subgraph External_Service_Mesh [Third Party API Layer]
        Controllers --> HTTPS_SDK[Google Gemini API REST Interface]
    end
## 🗄️ Database Schema Blueprint
The platform relies on a strict relational data system structured across multiple core target application modules:

authentication_user: Houses primary identity credentials, featuring customized indexing vectors and binary boolean system state authorization flags (is_student, is_teacher).

student_profile: Extends identity records one-to-one to track academic metrics including institutional year and running CGPA indices.

dashboard_completestudenttelemetry: A heavy time-series tracking repository logging multi-variable performance and wellness inputs.

ai_engines_uploadedmaterial: Records historical upload events, capturing raw absolute path destinations alongside binary-extracted plaintext formats.

ai_engines_generatedstudypack: Maps one-to-one with active text inputs to cache synthesized structural payload summaries, mock test structures, and flashcard asset dictionaries.

## 🧪 Testing Strategies
To run the platform's verification suites and confirm structural integrity across URLs, business logic layers, and model objects, execute:

Bash
python manage.py test
## 📜 License
Distributed under the MIT License. See LICENSE for further explicit legal information details.
