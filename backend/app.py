"""
TaskGPT - Comprehensive Task Management Application
Main Flask application with REST API endpoints
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

DATABASE = 'taskgpt.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Group members table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(group_id, user_id)
        )
    ''')
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'todo',
            priority TEXT DEFAULT 'medium',
            due_date DATE,
            group_id INTEGER,
            created_by INTEGER NOT NULL,
            assigned_to INTEGER,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (assigned_to) REFERENCES users (id)
        )
    ''')
    
    # Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Activity log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER,
            group_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id),
            FOREIGN KEY (group_id) REFERENCES groups (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Routes

@app.route('/')
def index():
    """Main page"""
    if 'user_id' in session:
        return render_template('dashboard.html')
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

# Authentication API

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        password_hash = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)',
            (user_id, 'register', f'User {username} registered')
        )
        conn.commit()
        
        session['user_id'] = user_id
        session['username'] = username
        
        conn.close()
        return jsonify({'message': 'Registration successful', 'user_id': user_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)',
            (user['id'], 'login', f'User {username} logged in')
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Login successful', 'user_id': user['id'], 'username': username}), 200
    
    conn.close()
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/user', methods=['GET'])
def get_current_user():
    """Get current logged in user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username']
    }), 200

# Groups API

@app.route('/api/groups', methods=['GET', 'POST'])
def groups():
    """Get all groups or create a new group"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        # Get groups where user is a member
        cursor.execute('''
            SELECT g.*, u.username as created_by_username,
                   COUNT(DISTINCT gm.user_id) as member_count
            FROM groups g
            JOIN users u ON g.created_by = u.id
            JOIN group_members gm ON g.id = gm.group_id
            WHERE g.id IN (
                SELECT group_id FROM group_members WHERE user_id = ?
            )
            GROUP BY g.id
            ORDER BY g.created_at DESC
        ''', (session['user_id'],))
        
        groups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(groups), 200
    
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            conn.close()
            return jsonify({'error': 'Group name is required'}), 400
        
        cursor.execute(
            'INSERT INTO groups (name, description, created_by) VALUES (?, ?, ?)',
            (name, description, session['user_id'])
        )
        group_id = cursor.lastrowid
        
        # Add creator as admin member
        cursor.execute(
            'INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, ?)',
            (group_id, session['user_id'], 'admin')
        )
        
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (user_id, group_id, action, details) VALUES (?, ?, ?, ?)',
            (session['user_id'], group_id, 'create_group', f'Group {name} created')
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Group created', 'group_id': group_id}), 201

@app.route('/api/groups/<int:group_id>/members', methods=['GET', 'POST'])
def group_members(group_id):
    """Get group members or add a new member"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT u.id, u.username, u.email, gm.role, gm.joined_at
            FROM group_members gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id = ?
            ORDER BY gm.joined_at DESC
        ''', (group_id,))
        
        members = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(members), 200
    
    elif request.method == 'POST':
        data = request.json
        username = data.get('username')
        
        if not username:
            conn.close()
            return jsonify({'error': 'Username is required'}), 400
        
        # Find user by username
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        try:
            cursor.execute(
                'INSERT INTO group_members (group_id, user_id) VALUES (?, ?)',
                (group_id, user['id'])
            )
            
            # Log activity
            cursor.execute(
                'INSERT INTO activity_log (user_id, group_id, action, details) VALUES (?, ?, ?, ?)',
                (session['user_id'], group_id, 'add_member', f'Added {username} to group')
            )
            
            conn.commit()
            conn.close()
            return jsonify({'message': 'Member added successfully'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'User is already a member'}), 409

# Tasks API

@app.route('/api/tasks', methods=['GET', 'POST'])
def tasks():
    """Get all tasks or create a new task"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        # Get filters from query parameters
        status = request.args.get('status')
        priority = request.args.get('priority')
        group_id = request.args.get('group_id')
        
        query = '''
            SELECT t.*, 
                   u1.username as created_by_username,
                   u2.username as assigned_to_username,
                   g.name as group_name,
                   COUNT(DISTINCT c.id) as comment_count
            FROM tasks t
            JOIN users u1 ON t.created_by = u1.id
            LEFT JOIN users u2 ON t.assigned_to = u2.id
            LEFT JOIN groups g ON t.group_id = g.id
            LEFT JOIN comments c ON t.id = c.task_id
            WHERE (t.created_by = ? OR t.assigned_to = ? OR t.group_id IN (
                SELECT group_id FROM group_members WHERE user_id = ?
            ))
        '''
        params = [session['user_id'], session['user_id'], session['user_id']]
        
        if status:
            query += ' AND t.status = ?'
            params.append(status)
        
        if priority:
            query += ' AND t.priority = ?'
            params.append(priority)
        
        if group_id:
            query += ' AND t.group_id = ?'
            params.append(group_id)
        
        query += ' GROUP BY t.id ORDER BY t.created_at DESC'
        
        cursor.execute(query, params)
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(tasks), 200
    
    elif request.method == 'POST':
        data = request.json
        title = data.get('title')
        description = data.get('description', '')
        status = data.get('status', 'todo')
        priority = data.get('priority', 'medium')
        due_date = data.get('due_date')
        group_id = data.get('group_id')
        assigned_to = data.get('assigned_to')
        category = data.get('category', '')
        
        if not title:
            conn.close()
            return jsonify({'error': 'Task title is required'}), 400
        
        cursor.execute('''
            INSERT INTO tasks 
            (title, description, status, priority, due_date, group_id, created_by, assigned_to, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, status, priority, due_date, group_id, session['user_id'], assigned_to, category))
        
        task_id = cursor.lastrowid
        
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (user_id, task_id, group_id, action, details) VALUES (?, ?, ?, ?, ?)',
            (session['user_id'], task_id, group_id, 'create_task', f'Task "{title}" created')
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Task created', 'task_id': task_id}), 201

@app.route('/api/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
def task_detail(task_id):
    """Get, update or delete a specific task"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT t.*, 
                   u1.username as created_by_username,
                   u2.username as assigned_to_username,
                   g.name as group_name
            FROM tasks t
            JOIN users u1 ON t.created_by = u1.id
            LEFT JOIN users u2 ON t.assigned_to = u2.id
            LEFT JOIN groups g ON t.group_id = g.id
            WHERE t.id = ?
        ''', (task_id,))
        
        task = cursor.fetchone()
        if not task:
            conn.close()
            return jsonify({'error': 'Task not found'}), 404
        
        conn.close()
        return jsonify(dict(task)), 200
    
    elif request.method == 'PUT':
        data = request.json
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        for field in ['title', 'description', 'status', 'priority', 'due_date', 'assigned_to', 'category']:
            if field in data:
                update_fields.append(f'{field} = ?')
                params.append(data[field])
        
        if not update_fields:
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(task_id)
        
        query = f'UPDATE tasks SET {", ".join(update_fields)} WHERE id = ?'
        cursor.execute(query, params)
        
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (user_id, task_id, action, details) VALUES (?, ?, ?, ?)',
            (session['user_id'], task_id, 'update_task', 'Task updated')
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Task updated'}), 200
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (user_id, task_id, action, details) VALUES (?, ?, ?, ?)',
            (session['user_id'], task_id, 'delete_task', 'Task deleted')
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Task deleted'}), 200

@app.route('/api/tasks/<int:task_id>/comments', methods=['GET', 'POST'])
def task_comments(task_id):
    """Get comments for a task or add a new comment"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT c.*, u.username
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.task_id = ?
            ORDER BY c.created_at DESC
        ''', (task_id,))
        
        comments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(comments), 200
    
    elif request.method == 'POST':
        data = request.json
        comment = data.get('comment')
        
        if not comment:
            conn.close()
            return jsonify({'error': 'Comment text is required'}), 400
        
        cursor.execute(
            'INSERT INTO comments (task_id, user_id, comment) VALUES (?, ?, ?)',
            (task_id, session['user_id'], comment)
        )
        
        comment_id = cursor.lastrowid
        
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (user_id, task_id, action, details) VALUES (?, ?, ?, ?)',
            (session['user_id'], task_id, 'add_comment', 'Comment added')
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Comment added', 'comment_id': comment_id}), 201

@app.route('/api/activity', methods=['GET'])
def activity():
    """Get recent activity"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get activity for user's groups and tasks
    cursor.execute('''
        SELECT a.*, u.username
        FROM activity_log a
        JOIN users u ON a.user_id = u.id
        WHERE a.group_id IN (
            SELECT group_id FROM group_members WHERE user_id = ?
        ) OR a.user_id = ?
        ORDER BY a.created_at DESC
        LIMIT 50
    ''', (session['user_id'], session['user_id']))
    
    activities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(activities), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
