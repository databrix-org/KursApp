# SingleCourseWebApp

A Django-based web application for managing and delivering online courses with support for Shibboleth authentication.

## Features

- Course Management System
  - Create and manage courses with modules and lessons
  - Support for different lesson types (video, reading, exercises)
  - Track student progress and completion
  - Group management for collaborative exercises

- User Management
  - Shibboleth authentication integration
  - Separate instructor and student roles
  - Custom user profiles

- Content Types
  - Video lessons
  - Reading materials
  - Programming exercises
  - Traditional exercises
  - JupyterHub integration for interactive programming

- Progress Tracking
  - Individual lesson progress tracking
  - Course completion monitoring
  - Time spent tracking
  - Exercise submissions and scoring

## Prerequisites

- Python 3.x
- Django 5.1.3
- Shibboleth SP
- SQLite3 (default database)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd SingleCourseWebApp
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Create development data (optional):
```bash
python manage.py setup_dev_data
```

## Development Setup

The project includes development data with test users:

- Instructor account:
  - Username: instructor
  - Password: instructor123

- Student account:
  - Username: student
  - Password: student123

## Project Structure

- `app/` - Main Django project directory
  - `settings.py` - Project settings and configuration
  - `urls.py` - Main URL routing

- `course/` - Main application directory
  - `models.py` - Database models
  - `views.py` - View controllers
  - `urls.py` - Application URL routing
  - `templates/` - HTML templates
  - `static/` - Static files (CSS, JS, images)
  - `management/commands/` - Custom management commands

## Configuration

The application uses the following directory structure for data storage:

- `data/` - Root directory for all data storage
  - `user_directories/` - User-specific files
  - `exercise_files/` - Exercise-related files
  - `media/` - Media files (videos, images)
  - `exercise_submissions/` - Student exercise submissions

## Running the Application

1. Start the development server:
```bash
python manage.py runserver
```

2. Access the application at `http://localhost:8000`

## Production Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Configure a proper database (e.g., PostgreSQL)
3. Set up proper static file serving
4. Configure Shibboleth SP
5. Use a production-grade server (e.g., Gunicorn)
6. Set up proper security measures (HTTPS, secure cookies, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Specify your license here]


