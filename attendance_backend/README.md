# Student Attendance Tracker - Backend API

A production-grade Django REST API for student attendance tracking with semester-wise subjects, routines, attendance records, analytics, and audit logging.

## Features

- **User Authentication**: Token-based authentication with username login
- **Semester Management**: Organize attendance by academic semesters
- **Subject Management**: Track subjects with credit values and minimum attendance requirements
- **Routine/Timetable**: Weekly class schedules with automatic class generation
- **Attendance Tracking**: Mark present/absent/cancelled with support for ad-hoc classes
- **Analytics**: Real-time attendance percentage, trends, and shortage alerts
- **Audit Logging**: Complete history of all data changes
- **CSV Export**: Export attendance records, summaries, and reports

## Tech Stack

- Django 5.x
- Django REST Framework
- SQLite (development) / PostgreSQL (production)
- Token-based authentication

## Installation

```bash
# Clone and navigate to project
cd attendance_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login and get token |
| POST | `/api/auth/logout/` | Logout (invalidate token) |
| GET/PUT | `/api/auth/profile/` | Get/update user profile |
| POST | `/api/auth/change-password/` | Change password |

### Semesters
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/semesters/` | List all semesters |
| POST | `/api/semesters/` | Create semester |
| GET | `/api/semesters/{id}/` | Get semester details |
| PUT/PATCH | `/api/semesters/{id}/` | Update semester |
| DELETE | `/api/semesters/{id}/` | Soft delete semester |
| POST | `/api/semesters/{id}/set_current/` | Set as current semester |
| GET | `/api/semesters/current/` | Get current semester |
| GET | `/api/semesters/{id}/analytics/` | Get semester analytics |

### Subjects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/subjects/` | List subjects (filter by semester) |
| POST | `/api/subjects/` | Create subject |
| GET | `/api/subjects/{id}/` | Get subject details |
| PUT/PATCH | `/api/subjects/{id}/` | Update subject |
| DELETE | `/api/subjects/{id}/` | Soft delete subject |
| GET | `/api/subjects/{id}/analytics/` | Get subject analytics |
| GET | `/api/subjects/{id}/weekly_trends/` | Weekly attendance trends |
| GET | `/api/subjects/{id}/monthly_trends/` | Monthly attendance trends |

### Routines
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/routines/` | List routines |
| POST | `/api/routines/` | Create routine |
| GET | `/api/routines/{id}/` | Get routine with entries by day |
| PUT/PATCH | `/api/routines/{id}/` | Update routine |
| DELETE | `/api/routines/{id}/` | Soft delete routine |
| POST | `/api/routines/{id}/generate_classes/` | Generate classes for date range |
| POST | `/api/routines/{id}/generate_today/` | Generate today's classes |

### Routine Entries
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/routine-entries/` | List entries |
| POST | `/api/routine-entries/` | Create entry |
| GET | `/api/routine-entries/{id}/` | Get entry details |
| PUT/PATCH | `/api/routine-entries/{id}/` | Update entry |
| DELETE | `/api/routine-entries/{id}/` | Soft delete entry |
| POST | `/api/routine-entries/bulk_create/` | Create multiple entries |

### Attendance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/attendance/` | List attendance records (with filters) |
| POST | `/api/attendance/` | Create attendance record |
| GET | `/api/attendance/{id}/` | Get record details |
| PUT/PATCH | `/api/attendance/{id}/` | Update record |
| DELETE | `/api/attendance/{id}/` | Soft delete record |
| POST | `/api/attendance/bulk_update/` | Update multiple records |
| POST | `/api/attendance/mark_day/` | Mark all classes for a day |
| POST | `/api/attendance/add_adhoc/` | Add ad-hoc class |
| GET | `/api/attendance/today/` | Get today's attendance |
| GET | `/api/attendance/calendar/` | Get calendar view (month) |
| POST | `/api/attendance/generate/` | Generate classes from routine |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/dashboard/` | Dashboard with overview |
| GET | `/api/analytics/semester/{id}/` | Semester analytics |
| GET | `/api/analytics/semester/{id}/alerts/` | Attendance alerts |
| GET | `/api/analytics/subject/{id}/` | Subject analytics |
| GET | `/api/analytics/subject/{id}/weekly/` | Weekly trends |
| GET | `/api/analytics/subject/{id}/monthly/` | Monthly trends |
| GET | `/api/analytics/subject/{id}/history/` | Attendance history |

### Exports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/attendance/exports/attendance/` | Export attendance CSV |
| GET | `/api/attendance/exports/subjects/` | Export subject summary CSV |
| GET | `/api/attendance/exports/semester/{id}/` | Export semester report CSV |

### Audit Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit-logs/` | List audit logs |
| GET | `/api/audit-logs/{id}/` | Get log details |
| GET | `/api/audit-logs/my_activity/` | Get user's activity |
| GET | `/api/audit-logs/for_object/` | Get logs for object |

## Authentication

Include the token in the Authorization header:
```
Authorization: Token your-token-here
```

## Query Parameters

### Filtering
- `?semester={id}` - Filter by semester
- `?subject={id}` - Filter by subject
- `?status=present|absent|cancelled` - Filter by status
- `?date={YYYY-MM-DD}` - Filter by date
- `?date__gte={YYYY-MM-DD}` - Filter from date
- `?date__lte={YYYY-MM-DD}` - Filter to date

### Pagination
- `?page={number}` - Page number (default: 1)
- `?page_size={number}` - Items per page (default: 20)

### Ordering
- `?ordering=-date` - Order by date descending
- `?ordering=name` - Order by name ascending

### Search
- `?search={term}` - Search in name, code, notes

## Data Models

### Semester
```json
{
  "id": 1,
  "name": "Fall 2025",
  "start_date": "2025-08-01",
  "end_date": "2025-12-15",
  "status": "active",
  "is_current": true
}
```

### Subject
```json
{
  "id": 1,
  "semester": 1,
  "name": "Data Structures",
  "code": "CS201",
  "credit": 4.0,
  "min_attendance_percentage": 75.00,
  "color": "#3B82F6"
}
```

### Routine Entry
```json
{
  "id": 1,
  "routine": 1,
  "subject": 1,
  "day_of_week": 0,
  "start_time": "09:00:00",
  "end_time": "10:00:00",
  "room": "Room 101"
}
```

### Attendance Record
```json
{
  "id": 1,
  "subject": 1,
  "date": "2025-08-15",
  "status": "present",
  "attendance_type": "routine",
  "start_time": "09:00:00",
  "end_time": "10:00:00",
  "notes": null,
  "is_holiday": false
}
```

## Analytics Response

### Subject Analytics
```json
{
  "subject_id": 1,
  "subject_name": "Data Structures",
  "total_conducted": 45,
  "total_attended": 40,
  "total_absent": 5,
  "total_cancelled": 2,
  "attendance_percentage": "88.89",
  "min_required_percentage": "75.00",
  "status": "safe",
  "classes_can_miss": 6,
  "classes_need_to_attend": 0
}
```

### Status Values
- `safe` - Above minimum + 5%
- `borderline` - Within 5% of minimum
- `shortage` - Below minimum

## Development

```bash
# Run tests
python manage.py test

# Check for issues
python manage.py check

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## Production Deployment

1. Set `DEBUG = False` in settings
2. Configure PostgreSQL database
3. Set `SECRET_KEY` from environment
4. Configure `ALLOWED_HOSTS`
5. Set up static files serving
6. Use gunicorn as WSGI server

```bash
gunicorn attendance_backend.wsgi:application --bind 0.0.0.0:8000
```

## License

MIT License
