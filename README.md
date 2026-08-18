# Online Learning Platform

A comprehensive Django REST API for an online learning platform with role-based access control, course management, and user authentication.

## Features

- **User Authentication**: JWT-based authentication with email verification
- **Role-Based Access Control**: Learner, Instructor, and Admin roles
- **Course Management**: Create, publish, and manage courses with sections and lessons
- **Category System**: Hierarchical category structure for organizing courses
- **Google OAuth**: Social authentication via Google
- **Email Services**: Email verification and password reset
- **API Documentation**: OpenAPI/Swagger documentation
- **Async Tasks**: Celery integration for background tasks

## Tech Stack

- **Backend**: Django 6.1, Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: JWT (SimpleJWT), Django Allauth
- **Task Queue**: Celery with Redis
- **API Documentation**: drf-spectacular
- **Rate Limiting**: django-ratelimit

## Project Structure

```
online-learning-platform/
├── backend/
│   ├── apps/
│   │   ├── accounts/          # User authentication and profiles
│   │   ├── categories/        # Category management
│   │   └── courses/           # Course, section, and lesson management
│   ├── config/                # Django settings and configuration
│   ├── media/                 # User uploaded files
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/                  # Frontend application (to be implemented)
```

## Setup Instructions

### Prerequisites

- Python 3.12+
- PostgreSQL 12+
- Redis 6+
- pip

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd online-learning-platform
```

2. **Create virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True

POSTGRES_DB=online_learning_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

FRONTEND_URL=http://localhost:5173

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@onlinelearning.local

GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/accounts/google/login/callback/

CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
```

5. **Set up PostgreSQL database**
```bash
createdb online_learning_db
```

6. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create a superuser**
```bash
python manage.py createsuperuser
```

8. **Start Redis server**
```bash
redis-server
```

9. **Start Celery worker** (in a separate terminal)
```bash
cd backend
source venv/bin/activate
celery -A config worker -l info
```

10. **Run the development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, access the interactive API documentation:
- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

## API Endpoints

### Authentication (`/api/auth/`)
- `POST /register` - Register new user
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /me` - Get current user info
- `GET /my-profile` - Get user profile
- `PATCH /my-profile` - Update user profile
- `POST /verify-email` - Verify email address
- `POST /resend-verification` - Resend verification email
- `POST /password-reset-request` - Request password reset
- `POST /password-reset-confirm` - Confirm password reset
- `POST /google-login` - Google OAuth login
- `POST /admin-login` - Admin login

### Courses (`/api/courses/`)
- `GET /` - List all published courses (with filtering)
- `POST /` - Create new course (instructor only)
- `GET /{id}/` - Get course details
- `PUT /{id}/` - Update course (owner/admin only)
- `PATCH /{id}/` - Partial update course (owner/admin only)
- `DELETE /{id}/` - Delete course (owner/admin only)
- `POST /{id}/publish/` - Publish course (owner/admin only)
- `POST /{id}/archive/` - Archive course (owner/admin only)
- `GET /{course_id}/sections/` - List course sections
- `POST /{course_id}/sections/` - Create section (owner/admin only)
- `GET /sections/{id}/` - Get section details
- `PATCH /sections/{id}/` - Update section (owner/admin only)
- `DELETE /sections/{id}/` - Delete section (owner/admin only)
- `GET /sections/{section_id}/lessons/` - List section lessons
- `POST /sections/{section_id}/lessons/` - Create lesson (owner/admin only)
- `GET /lessons/{id}/` - Get lesson details
- `PATCH /lessons/{id}/` - Update lesson (owner/admin only)
- `DELETE /lessons/{id}/` - Delete lesson (owner/admin only)
- `GET /{id}/curriculum/` - Get full course curriculum

### Categories (`/api/categories/`)
- `GET /` - List all active categories
- `POST /` - Create category (admin only)
- `GET /{id}/` - Get category details
- `PATCH /{id}/` - Update category (admin only)
- `DELETE /{id}/` - Delete category (admin only)

## User Roles

### Learner
- Browse and view published courses
- View course curriculum
- Update learner profile

### Instructor
- All learner permissions
- Create and manage own courses
- Create and manage course sections and lessons
- Publish and archive courses
- Update instructor profile

### Admin
- All instructor permissions
- Manage any course
- Create and manage categories
- Access admin panel

## Running Tests

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test apps.accounts
python manage.py test apps.categories
python manage.py test apps.courses

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Development

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and small

### Git Workflow
1. Create a feature branch
2. Make your changes
3. Write tests for new functionality
4. Ensure all tests pass
5. Commit with descriptive messages
6. Push and create pull request

## Deployment

### Production Checklist
- Set `DJANGO_DEBUG=False`
- Configure `ALLOWED_HOSTS`
- Use strong `SECRET_KEY`
- Configure production database
- Set up static file serving
- Configure HTTPS
- Set up proper logging
- Configure CORS for production frontend
- Use production Redis instance
- Set up Celery with proper supervisor

### Environment Variables for Production
```env
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.com
POSTGRES_HOST=production-db-host
# ... other production settings
```

## Troubleshooting

### Common Issues

**Migration errors**
```bash
python manage.py migrate --fake-initial
```

**Celery connection issues**
- Ensure Redis is running
- Check CELERY_BROKER_URL in .env

**Email not sending**
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Check if email provider requires app-specific passwords

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please follow the established code style and submit pull requests for review.
