# Progress App

The Progress app tracks learner progress through courses, including lesson completion status and overall course progress tracking.

## Features

- **Lesson Progress Tracking**: Track when learners start and complete individual lessons
- **Course Progress Calculation**: Calculate overall course completion percentage
- **Enrollment Auto-Completion**: Automatically mark enrollments as completed when all lessons are finished
- **Progress Validation**: Ensure lessons are started before they can be completed
- **Role-Based Access**: Only learners can track their progress

## Models

### LessonProgress

Tracks individual lesson progress for enrolled learners.

**Fields:**
- `learner`: ForeignKey to User (the learner)
- `enrollment`: ForeignKey to Enrollment (the course enrollment)
- `lesson`: ForeignKey to Lesson (the lesson being tracked)
- `completed`: Boolean (whether the lesson is completed)
- `started_at`: DateTime (when the lesson was started)
- `completed_at`: DateTime (when the lesson was completed)
- `last_accessed_at`: DateTime (last time the lesson was accessed)
- `updated_at`: DateTime (last update timestamp)

**Constraints:**
- Unique constraint on (learner, lesson) - one progress record per lesson per learner

## API Endpoints

### Start Lesson Progress

**Endpoint:** `POST /api/progress/lessons/<lesson_id>/start/`

**Description:** Mark a lesson as started by the authenticated learner.

**Authentication:** Required (Learner only)

**Request:**
```json
{}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "lesson": 1,
  "lesson_title": "Introduction to React",
  "course_id": 1,
  "completed": false,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "last_accessed_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: User not authenticated
- `403 Forbidden`: User is not a learner or not enrolled in the course
- `404 Not Found`: Lesson does not exist or course is not published

### Complete Lesson

**Endpoint:** `POST /api/progress/lessons/<lesson_id>/complete/`

**Description:** Mark a lesson as completed by the authenticated learner.

**Authentication:** Required (Learner only)

**Business Logic:**
- Lesson must be started before it can be completed
- Learner must be enrolled in the course
- Automatically updates enrollment status if all lessons are completed

**Request:**
```json
{}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "lesson": 1,
  "lesson_title": "Introduction to React",
  "course_id": 1,
  "completed": true,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T11:00:00Z",
  "last_accessed_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: User not authenticated
- `403 Forbidden`: User is not a learner, not enrolled, or lesson not started
- `404 Not Found`: Lesson does not exist or course is not published

### Get My Progress

**Endpoint:** `GET /api/progress/my/`

**Description:** Get all lesson progress records for the authenticated learner.

**Authentication:** Required (Learner only)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "lesson": 1,
    "lesson_title": "Introduction to React",
    "course_id": 1,
    "completed": true,
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T11:00:00Z",
    "last_accessed_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
]
```

**Error Responses:**
- `401 Unauthorized`: User not authenticated
- `403 Forbidden`: User is not a learner

### Get Course Progress

**Endpoint:** `GET /api/progress/courses/<course_id>/`

**Description:** Get overall progress statistics for a specific course.

**Authentication:** Required (Learner only)

**Response (200 OK):**
```json
{
  "course_id": 1,
  "course_title": "React Masterclass",
  "total_lessons": 10,
  "completed_lessons": 5,
  "progress_percentage": 50.0,
  "is_completed": false
}
```

**Error Responses:**
- `401 Unauthorized`: User not authenticated
- `403 Forbidden`: User is not a learner or not enrolled in the course
- `404 Not Found`: Course does not exist or is not published

## Services

### start_lesson(learner, lesson)

Starts tracking progress for a lesson.

**Parameters:**
- `learner`: User instance (the learner)
- `lesson`: Lesson instance (the lesson to start)

**Returns:** LessonProgress instance

**Raises:**
- `ProgressError`: If learner is not enrolled in the course

**Behavior:**
- Creates a new progress record if one doesn't exist
- Updates `last_accessed_at` if progress already exists
- Sets `started_at` if not already set

### complete_lesson(learner, lesson)

Marks a lesson as completed.

**Parameters:**
- `learner`: User instance (the learner)
- `lesson`: Lesson instance (the lesson to complete)

**Returns:** LessonProgress instance

**Raises:**
- `ProgressError`: If learner is not enrolled or lesson hasn't been started

**Behavior:**
- Validates that lesson progress exists and has been started
- Marks lesson as completed with timestamp
- Calls `update_enrollment_completion` to check if course is complete

### get_course_progress(learner, course)

Calculates overall progress for a course.

**Parameters:**
- `learner`: User instance (the learner)
- `course`: Course instance (the course to check)

**Returns:** Dictionary with progress statistics:
```python
{
    "course_id": int,
    "course_title": str,
    "total_lessons": int,
    "completed_lessons": int,
    "progress_percentage": float,
    "is_completed": bool
}
```

**Behavior:**
- Counts total lessons in the course
- Counts completed lessons for the learner
- Calculates percentage (rounded to 2 decimal places)
- Determines if course is completed (100% progress)

### update_enrollment_completion(enrollment)

Updates enrollment status when all lessons are completed.

**Parameters:**
- `enrollment`: Enrollment instance

**Returns:** Boolean (True if status was updated, False otherwise)

**Behavior:**
- Checks if all lessons in the course are completed
- Updates enrollment status to COMPLETED if all lessons done
- Sets `completed_at` timestamp
- Only updates if enrollment is currently ACTIVE

## Business Logic

### Progress Validation

1. **Enrollment Required**: Learners must be enrolled in a course to track progress
2. **Start Before Complete**: Lessons must be started before they can be completed
3. **Published Courses Only**: Only lessons from published courses can be tracked
4. **Role Restriction**: Only learners can track progress (instructors/admins cannot)

### Enrollment Auto-Completion

When a learner completes all lessons in a course:
- Enrollment status automatically changes from ACTIVE to COMPLETED
- `completed_at` timestamp is set
- This happens automatically via the `update_enrollment_completion` service

### Progress Calculation

- **Progress Percentage**: `(completed_lessons / total_lessons) * 100`
- **Course Completed**: `total_lessons > 0 and completed_lessons == total_lessons`
- **Zero Lessons**: Returns 0% progress and not completed

## Testing

The app includes comprehensive test coverage:

### Test Classes

- **LessonProgressModelTest**: Model creation, constraints, string representation
- **StartLessonServiceTest**: Start lesson business logic
- **CompleteLessonServiceTest**: Complete lesson business logic and validation
- **GetCourseProgressServiceTest**: Course progress calculation
- **UpdateEnrollmentCompletionServiceTest**: Enrollment auto-completion
- **StartLessonProgressViewTest**: Start lesson API endpoint
- **CompleteLessonViewTest**: Complete lesson API endpoint
- **MyProgressViewTest**: My progress API endpoint
- **CourseProgressViewTest**: Course progress API endpoint

### Running Tests

```bash
python manage.py test apps.progress --keepdb
```

### Test Coverage

- 37 tests covering all services and views
- Authentication and authorization tests
- Business logic validation tests
- Edge case handling (empty courses, partial completion, etc.)

## Dependencies

- Django REST Framework
- Django (core models and ORM)
- apps.accounts (User model)
- apps.courses (Course, CourseSection, Lesson models)
- apps.enrollments (Enrollment model)

## Integration Notes

### Enrollment Flow

1. User enrolls in a course via Enrollment app
2. User starts lessons via Progress app
3. Progress is tracked per lesson
4. Course completion percentage calculated
5. Enrollment auto-completed when all lessons done

### Course Structure

```
Course
├── CourseSection
│   └── Lesson
│       └── LessonProgress (per learner)
```

### Database Relationships

- `LessonProgress.learner` → `User`
- `LessonProgress.enrollment` → `Enrollment`
- `LessonProgress.lesson` → `Lesson`
- `Lesson.section` → `CourseSection`
- `CourseSection.course` → `Course`
- `Enrollment.course` → `Course`
- `Enrollment.learner` → `User`

## Future Enhancements

- Progress analytics and insights
- Time spent per lesson tracking
- Achievement badges for milestones
- Progress reminders and notifications
- Progress export functionality
- Comparative progress (class average, etc.)
