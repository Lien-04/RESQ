"""
Database Initialization Script
Creates tables and initializes sample data
"""
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash


def init_database(db_path='resq.db'):
    """Initialize the database with schema and sample data"""
    # Remove existing database if present
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Read and execute schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        schema = f.read()
        cursor.executescript(schema)
    
    print("Database schema created successfully")
    now = datetime.now().isoformat()
    
    # Create sample users
    sample_users = [
        {'username': 'admin', 'email': 'admin@resq.org', 'password': 'admin123', 'role': 'admin', 'full_name': 'System Administrator', 'phone': '555-0100', 'skills': 'management,coordination', 'location': 'Headquarters'},
        {'username': 'john_volunteer', 'email': 'john@resq.org', 'password': 'volunteer123', 'role': 'volunteer', 'full_name': 'John Smith', 'phone': '555-0101', 'skills': 'medical,fire-fighting', 'location': 'Downtown'},
        {'username': 'sarah_volunteer', 'email': 'sarah@resq.org', 'password': 'volunteer123', 'role': 'volunteer', 'full_name': 'Sarah Johnson', 'phone': '555-0102', 'skills': 'search-and-rescue,first-aid', 'location': 'Westside'},
        {'username': 'mike_citizen', 'email': 'mike@resq.org', 'password': 'citizen123', 'role': 'citizen', 'full_name': 'Mike Wilson', 'phone': '555-0103', 'skills': None, 'location': 'Northside'},
        {'username': 'emma_citizen', 'email': 'emma@resq.org', 'password': 'citizen123', 'role': 'citizen', 'full_name': 'Emma Davis', 'phone': '555-0104', 'skills': None, 'location': 'Eastside'}
    ]
    
    for user_data in sample_users:
        password_hash = generate_password_hash(user_data['password'])
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role, full_name, phone, skills, location, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_data['username'], user_data['email'], password_hash, user_data['role'], user_data['full_name'], user_data['phone'], user_data['skills'], user_data['location'], now, now))
    
    print(f"Created {len(sample_users)} sample users")
    
    # Get user IDs for incidents/notifications
    cursor.execute("SELECT id FROM users WHERE role = 'citizen' LIMIT 1")
    citizen_id = cursor.fetchone()['id']
    
    cursor.execute("SELECT id FROM users WHERE role = 'volunteer' LIMIT 1")
    volunteer_id = cursor.fetchone()['id']
    
    # Create sample incidents (only required columns - no defaults)
    sample_incidents = [
        {'title': 'Building Fire Downtown', 'description': 'Multi-story building showing smoke from upper floors.', 'incident_type': 'fire', 'location': '123 Main Street, Downtown', 'reported_by': citizen_id},
        {'title': 'Flash Flooding on Oak Avenue', 'description': 'Street flooding due to heavy rainfall.', 'incident_type': 'flood', 'location': 'Oak Avenue & 5th Street', 'reported_by': citizen_id},
        {'title': 'Traffic Accident at Intersection', 'description': 'Two-vehicle collision. One driver injured.', 'incident_type': 'traffic', 'location': 'Broadway & 42nd Street', 'reported_by': citizen_id},
        {'title': 'Power Lines Down', 'description': 'Storm has knocked down power lines blocking road.', 'incident_type': 'storm', 'location': 'Elm Street near park', 'reported_by': citizen_id},
        {'title': 'Minor Earthquake Rumors', 'description': 'Residents reporting tremors.', 'incident_type': 'earthquake', 'location': 'Various locations', 'reported_by': citizen_id}
    ]
    
    for inc in sample_incidents:
        cursor.execute('''
            INSERT INTO incidents (title, description, incident_type, location, reported_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (inc['title'], inc['description'], inc['incident_type'], inc['location'], inc['reported_by']))
    
    print(f"Created {len(sample_incidents)} sample incidents")
    
    # Create sample notifications
    cursor.execute('INSERT INTO notifications (user_id, incident_id, title, message, notification_type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (citizen_id, 1, 'Incident Update', 'Your reported incident is being responded to.', 'status_update', 0, now))
    cursor.execute('INSERT INTO notifications (user_id, incident_id, title, message, notification_type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (volunteer_id, 1, 'New Assignment', 'You have been assigned to respond.', 'assignment', 0, now))
    
    print("Created sample notifications")
    
    # Commit and verify
    conn.commit()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM incidents')
    incident_count = cursor.fetchone()[0]
    
    print(f"\nDatabase initialized: {user_count} users, {incident_count} incidents")
    conn.close()
    return {'users': user_count, 'incidents': incident_count}


if __name__ == '__main__':
    init_database()
    print("\nRun: python app.py")
