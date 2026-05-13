# RESQ - Disaster Response Coordination Platform

## Project Overview
- **Project Name**: RESQ (Report, Engage, Support, Quick Response)
- **Type**: Web-based disaster response coordination platform
- **Core Functionality**: Connect citizens, volunteers, and admins for disaster response coordination
- **Target Users**: Citizens (reporters), Volunteers (responders), Admins (coordinators)

## Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **API**: RESTful

## Folder Structure
```
RESQ/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Dependencies
├── database/
│   ├── init_db.py       # Database initialization
│   └── schema.sql      # SQL schema definitions
├── models/
│   ├── __init__.py
│   ├── user.py         # User models (User, Citizen, Volunteer, Admin)
│   ├── incident.py    # Incident models
│   ├── assignment.py # Assignment models
│   └── notification.py # Notification models
├── routes/
│   ├── __init__.py
│   ├── auth.py       # Authentication routes
│   ├── incidents.py # Incident routes
│   ├── alerts.py    # Alert routes
│   └── admin.py     # Admin routes
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── incident_service.py
│   ├── volunteer_service.py
│   └── notification_service.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── auth.js
│       ├── incidents.js
│       └── dashboard.js
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── report_incident.html
│   ├── view_reports.html
│   └── admin_panel.html
└── README.md
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('citizen', 'volunteer', 'admin')),
    full_name TEXT NOT NULL,
    phone TEXT,
    skills TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Incidents Table
```sql
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    location TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'verified', 'in_progress', 'resolved')),
    reported_by INTEGER NOT NULL,
    assigned_to INTEGER,
    verified_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reported_by) REFERENCES users(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id)
);
```

### Notifications Table
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    incident_id INTEGER,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (incident_id) REFERENCES incidents(id)
);
```

## API Endpoints

### Authentication
- POST /api/register - Register new user
- POST /api/login - Login user
- GET /api/logout - Logout user
- GET /api/me - Get current user info

### Incidents
- POST /api/reports - Create incident report
- GET /api/reports - Get all incidents
- GET /api/reports/{id} - Get specific incident
- PUT /api/reports/{id} - Update incident
- DELETE /api/reports/{id} - Delete incident
- PUT /api/reports/{id}/status - Update incident status
- POST /api/reports/{id}/verify - Verify incident

### Volunteer
- GET /api/volunteers - Get available volunteers
- GET /api/volunteers/matching - Get matching volunteers for incident

### Admin
- GET /api/admin/users - Get all users
- PUT /api/admin/users/{id} - Update user
- DELETE /api/admin/users/{id} - Delete user
- GET /api/admin/stats - Get system statistics

## User Roles & Permissions

### Citizen
- Can report incidents
- Can view own reported incidents
- Can receive notifications

### Volunteer
- All Citizen permissions
- Can view all incidents
- Can accept assignments
- Can update incident status (if assigned)

### Admin
- All permissions
- Can verify incidents
- Can assign volunteers
- Can manage users
- Can view dashboard statistics

## Implementation Phases

### Phase 1: Database & Models
- Create schema.sql
- Implement User, Incident, Notification models
- Initialize database

### Phase 2: Backend API
- Implement authentication routes
- Implement incident CRUD routes
- Implement admin routes
- Add basic business logic

### Phase 3: Frontend
- Create login/register pages
- Create incident reporting page
- Create dashboard view
- Create admin panel
