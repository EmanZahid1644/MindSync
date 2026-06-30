# WEB TECHNOLOGY PROJECT DOCUMENTATION

## Project Title
**MindSync AI - Student Success & Wellness Platform**

## Submitted By
- **Name:** Your Name
- **Roll Number:** Your Roll Number
- **Registration Number:** Your Registration Number
- **Program:** BS Computer Science
- **Semester:** Your Semester

## Submitted To
- **Instructor:** Instructor Name
- **Course:** Web Technology
- **Department:** Department Name
- **Institution:** Institution Name
- **Submission Date:** DD/MM/YYYY

## Table of Contents
1. Abstract
2. Introduction
3. Problem Statement
4. Objectives
5. Scope of the Project
6. Technologies Used
7. Software & Hardware Requirements
8. System Analysis
9. Database Design
10. Implementation
11. Features
12. Challenges Faced
13. Future Enhancements
14. Conclusion
15. Acknowledgment

## Abstract
MindSync AI is a web-based student success and wellness platform designed to help learners manage study resources, track academic progress, and receive AI-assisted guidance in one place. The system combines a responsive Django-based web application with structured user accounts, role-based access, document upload and study-pack generation, academic telemetry tracking, and a planning hub for resource discovery. The application uses HTML5, CSS3, JavaScript, Tailwind CSS, Django, PostgreSQL, and the Google Gemini API to provide an interactive and intelligent user experience. Students can log in, sign up, upload learning materials, generate study packs, explore curated resources, and monitor academic indicators such as GPA, study sessions, and wellness-related metrics. Teachers can also access dedicated analytics views for broader academic oversight. The expected outcome of the project is a modern, responsive, and functional academic support system that improves learning organization, reduces manual effort, and demonstrates the use of web technologies, dynamic database-driven design, and AI integration in a practical educational context.

## Introduction
The increasing workload in academic environments has created a need for web applications that combine productivity, learning support, and progress tracking. MindSync AI was developed to address this need by offering a centralized platform where students can manage their study routine, upload notes, generate AI-powered study resources, and track academic performance. The project is important because it brings together several web development concepts such as user authentication, database integration, dynamic rendering, responsive UI design, and external API-based intelligence.

The platform is intended for students who want structured study support and for teachers who may need a simple way to view academic-related information. It also supports users who need quick access to resources, planning tools, and progress visualization through a modern browser-based interface.

## Problem Statement
Many students struggle to organize study material, keep track of progress, and find relevant resources quickly. In addition, manual note preparation and exam revision often take time and effort that could be reduced through automation. Existing solutions are frequently fragmented, requiring users to switch between multiple tools for learning materials, planning, progress tracking, and AI guidance.

MindSync AI solves this problem by providing a single web application that unifies authentication, study planning, document processing, resource discovery, and academic tracking. The system reduces manual effort, improves accessibility, and supports a more structured and interactive learning experience.

## Objectives
- Develop a responsive web application.
- Implement CRUD functionality.
- Create a user-friendly interface.
- Manage data efficiently.
- Provide secure user authentication and role-based access.
- Enable AI-assisted study support and resource discovery.
- Offer a centralized dashboard for academic progress and planning.

## Scope of the Project
The project covers user registration and login, role-based access for students and teachers, AI-powered study material generation, resource discovery, academic telemetry, and study session management. It includes a responsive front-end and a database-backed back-end for storing accounts, uploads, progress history, and generated outputs.

The current scope is limited to browser-based access and server-side processing within the Django application. It does not include a native mobile application, offline synchronization, or enterprise-level multi-tenant deployment. However, the project is designed in a way that these enhancements can be added later.

## Technologies Used
- HTML5
- CSS3
- JavaScript
- Tailwind CSS
- Django / Python
- PostgreSQL
- Google Gemini API
- XAMPP-style local development workflow concepts where applicable
- VS Code
- Git / GitHub

## Software & Hardware Requirements
### Software Requirements
- Visual Studio Code
- Python 3.13+
- Django 6.x
- PostgreSQL
- Chrome or any modern browser
- Git / GitHub

### Hardware Requirements
- Windows 10/11
- 4GB or more RAM
- Intel i3 or higher processor
- Internet connection for AI/API features

## System Analysis
### Functional Requirements
- User registration, login, and logout.
- Role-based access for students and teachers.
- Uploading learning materials.
- Generating study packs from uploaded content.
- Searching and discovering academic resources.
- Logging telemetry and academic progress.
- Creating and managing planned study sessions.
- Saving AI coach conversations and quiz results.

### Non-Functional Requirements
- Security through authentication and session management.
- Responsive design for desktop and mobile devices.
- Good performance for database-driven pages.
- Reliability of stored user data and generated outputs.
- Maintainability through modular Django apps and reusable templates.

## Database Design
The database used by the project is **mindsync_db**. It stores user accounts, student and teacher profiles, academic telemetry, generated study resources, and AI interaction history.

### Main Tables
- **authentication_user**: custom user table with student and teacher role flags.
- **student_profile**: stores student-specific profile data such as GPA and academic year.
- **teacher_profile**: stores teacher-related profile information.
- **dashboard_completestudenttelemetry**: tracks daily academic and wellness metrics.
- **dashboard_plannedstudysession**: stores planned study sessions and completion status.
- **dashboard_cgpapredictionhistory**: stores GPA prediction history and forecast snapshots.
- **dashboard_semestersimulationhistory**: stores semester simulation results.
- **ai_engines_uploadedmaterial**: stores uploaded learning materials and extracted text.
- **ai_engines_generatedstudypack**: stores summaries, concepts, flashcards, and study questions.
- **ai_engines_quizresult**: stores quiz attempts and performance data.
- **ai_engines_aicoachconversation**: stores AI coach conversation history and recommendations.
- **planner_topicresourcecache**: stores cached topic-based resource discovery results.

### Relationships
- Each user can have a student or teacher profile.
- Telemetry, study sessions, predictions, and simulations are linked to the user.
- Uploaded materials are linked to the user.
- Study packs are linked one-to-one with uploaded materials.
- Quiz results are linked to both the user and the uploaded material.
- AI coach conversations are linked to the user.
- Topic resource cache stores reusable resource results for faster future searches.

## Implementation
The project is implemented as a modular Django application with separate apps for authentication, dashboard, AI engines, and planner functionality.

### Key Modules
- **authentication**: handles sign up, login, logout, role assignment, and public pages.
- **dashboard**: manages student and teacher dashboards, telemetry, CGPA predictions, and study session workflows.
- **ai_engines**: manages note uploads, study pack generation, quiz results, and AI coach interactions.
- **planner**: provides a topic discovery hub and cached learning resource search.

### Routing and Navigation
The application uses Django URL routing to connect pages such as:
- Login and signup pages
- Main dashboard
- Notes generator page
- AI coach pages
- Planner hub
- About, Products, and Contact pages

### Front-End Design
The UI is built with Tailwind CSS and designed for a dark, modern look with responsive cards, gradients, and reusable layout patterns. Shared templates are used to keep the visual language consistent across public and authenticated pages.

## Features
- Responsive design
- Authentication and role-based access
- AI-powered study pack generation
- Document upload and text extraction
- Dashboard analytics and telemetry tracking
- Study session management
- Resource search and topic caching
- Quiz result tracking
- Modern UI with consistent footer and navigation links

## Challenges Faced
One challenge was maintaining a consistent design across multiple Django apps while keeping templates reusable. Another challenge was managing data relationships between user accounts, uploaded materials, AI outputs, and academic telemetry. Integrating AI-based resource generation also required careful handling of API responses, caching, and fallback behavior. Ensuring the interface remained responsive and visually coherent across different page types was another important implementation task.

## Future Enhancements
- Dark mode improvements and theme customization
- Mobile app version
- REST API for external integrations
- Analytics dashboard with charts and trends
- Notification and reminder system
- Export options for reports and study packs
- Improved collaboration and teacher feedback tools

## Conclusion
MindSync AI successfully demonstrates how modern web technologies can be used to build a practical educational platform. The project achieved its objectives by combining authentication, CRUD-style data management, responsive design, database integration, and AI-assisted learning support in one application. It also strengthened understanding of Django architecture, template reuse, routing, models, and user-centered interface design. The project provides a strong foundation for further development into a more advanced educational productivity platform.

## Acknowledgment
I would like to thank my instructor for valuable guidance throughout the project, my department for providing the learning environment and resources, and my institution for supporting my academic growth. I also acknowledge the effort and teamwork involved in completing this web technology project successfully.
