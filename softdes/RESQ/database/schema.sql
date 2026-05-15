-- RESQ Database Schema
-- SQLite Database for Disaster Response Coordination Platform

-- Users table: Stores all user types (citizen, volunteer, admin)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('citizen', 'volunteer', 'admin')),
    full_name TEXT NOT NULL,
    phone TEXT,
    skills TEXT,
    location TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Incidents table: Stores disaster incident reports
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    location TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'verified', 'in_progress', 'resolved')),
    priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'critical')),
    reported_by INTEGER NOT NULL,
    assigned_to INTEGER,
    verified_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (reported_by) REFERENCES users(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id)
);

-- Notifications table: Stores user notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    incident_id INTEGER,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'alert',
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (incident_id) REFERENCES incidents(id)
);

-- Volunteer skills table: Stores volunteer skills for matching
CREATE TABLE IF NOT EXISTS volunteer_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    proficiency_level TEXT DEFAULT 'intermediate',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Push subscriptions table: Stores Web Push subscriptions for notifications
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL UNIQUE,
    auth TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    device_name TEXT DEFAULT 'Unknown Device',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Incident comments table: Stores discussion about incidents
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_reported_by ON incidents(reported_by);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned_to ON incidents(assigned_to);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_incident_id ON notifications(incident_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_skills_user_id ON volunteer_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_endpoint ON push_subscriptions(endpoint);
