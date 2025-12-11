# TaskGPT - Comprehensive Task Management Application

TaskGPT is a fully responsive, feature-rich task management application designed for teams and groups to collaborate effectively. It goes beyond basic task apps like Google Keep by offering comprehensive features for project management, team collaboration, and task tracking.

## Features

### 🎯 Core Features
- **User Authentication**: Secure registration and login system
- **Task Management**: Create, update, delete, and organize tasks
- **Group Collaboration**: Create groups and collaborate with team members
- **Task Assignment**: Assign tasks to specific group members
- **Priority Levels**: Organize tasks by priority (Low, Medium, High, Urgent)
- **Status Tracking**: Track task progress (To Do, In Progress, Done)
- **Due Dates**: Set and track task deadlines
- **Categories/Tags**: Organize tasks with custom categories
- **Comments & Discussions**: Add comments to tasks for team communication
- **Activity Feed**: Track all activities across your groups and tasks
- **Filtering & Sorting**: Filter tasks by status, priority, and group

### 💡 Advanced Features (Beyond Basic Task Apps)
- **Multi-user Collaboration**: Work together with team members in groups
- **Group Management**: Create multiple groups for different projects/teams
- **Member Roles**: Admin and member roles for group management
- **Task Statistics**: Visual overview of task distribution and progress
- **Real-time Updates**: See changes as they happen
- **Comprehensive Activity Log**: Track all actions and changes
- **Task Comments**: Threaded discussions on individual tasks
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## Technology Stack

- **Backend**: Python Flask (REST API)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: SQLite (easily upgradeable to PostgreSQL/MySQL)
- **Styling**: Custom CSS with responsive design
- **Architecture**: RESTful API with session-based authentication

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/mahiti-org/TaskGPT.git
   cd TaskGPT
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables (optional)**
   ```bash
   # On Windows
   set SECRET_KEY=your-secret-key-here
   
   # On macOS/Linux
   export SECRET_KEY=your-secret-key-here
   ```

5. **Run the application**
   ```bash
   python backend/app.py
   ```

6. **Access the application**
   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage Guide

### Getting Started

1. **Register an Account**
   - Click "Register" on the login page
   - Enter your username, email, and password
   - Submit to create your account

2. **Create Your First Task**
   - Click "+ New Task" in the sidebar
   - Fill in task details (title, description, priority, etc.)
   - Click "Create Task"

3. **Create a Group**
   - Click "+ New Group" in the sidebar
   - Enter group name and description
   - Invite members by username

4. **Manage Tasks**
   - View all tasks on the dashboard
   - Filter by status, priority, or group
   - Click on a task to view details, update status, or add comments
   - Update task status: To Do → In Progress → Done

5. **Collaborate with Team**
   - Add members to your groups
   - Assign tasks to group members
   - Use comments for discussions
   - Track activity in the Activity feed

## Project Structure

```
TaskGPT/
├── backend/
│   └── app.py              # Flask application and API endpoints
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css   # Application styles
│   │   └── js/
│   │       ├── auth.js     # Authentication logic
│   │       └── dashboard.js # Dashboard functionality
│   └── templates/
│       ├── index.html      # Login/Register page
│       └── dashboard.html  # Main dashboard
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── LICENSE                # License information
```

## API Endpoints

### Authentication
- `POST /api/register` - Register a new user
- `POST /api/login` - Login user
- `POST /api/logout` - Logout user
- `GET /api/user` - Get current user

### Tasks
- `GET /api/tasks` - Get all tasks (with filters)
- `POST /api/tasks` - Create a new task
- `GET /api/tasks/<id>` - Get task details
- `PUT /api/tasks/<id>` - Update a task
- `DELETE /api/tasks/<id>` - Delete a task
- `GET /api/tasks/<id>/comments` - Get task comments
- `POST /api/tasks/<id>/comments` - Add a comment

### Groups
- `GET /api/groups` - Get all groups
- `POST /api/groups` - Create a new group
- `GET /api/groups/<id>/members` - Get group members
- `POST /api/groups/<id>/members` - Add a member to group

### Activity
- `GET /api/activity` - Get recent activity

## Database Schema

### Users
- id, username, email, password_hash, created_at

### Groups
- id, name, description, created_by, created_at

### Group Members
- id, group_id, user_id, role, joined_at

### Tasks
- id, title, description, status, priority, due_date, group_id, created_by, assigned_to, category, created_at, updated_at

### Comments
- id, task_id, user_id, comment, created_at

### Activity Log
- id, user_id, task_id, group_id, action, details, created_at

## Responsive Design

TaskGPT is fully responsive and works on:
- **Desktop**: Full-featured interface with sidebar navigation
- **Tablet**: Optimized layout with collapsible sidebar
- **Mobile**: Touch-friendly interface with stacked layout

Breakpoints:
- Desktop: > 1024px
- Tablet: 768px - 1024px
- Mobile: < 768px

## Security Features

- Password hashing using Werkzeug security
- Session-based authentication
- CSRF protection through Flask sessions
- SQL injection prevention with parameterized queries
- XSS prevention through HTML escaping

## Future Enhancements

- [ ] Email notifications
- [ ] File attachments for tasks
- [ ] Calendar view
- [ ] Task templates
- [ ] Advanced search
- [ ] Export tasks (CSV, PDF)
- [ ] Integration with external services (Slack, Email)
- [ ] Recurring tasks
- [ ] Time tracking
- [ ] Kanban board view

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please visit:
https://github.com/mahiti-org/TaskGPT

## Comparison with Basic Task Apps

| Feature | TaskGPT | Google Keep Tasks |
|---------|---------|-------------------|
| Multi-user Collaboration | ✅ | ❌ |
| Group Management | ✅ | ❌ |
| Task Assignment | ✅ | ❌ |
| Priority Levels | ✅ (4 levels) | ❌ |
| Status Tracking | ✅ (3 states) | ✅ (2 states) |
| Comments/Discussions | ✅ | ❌ |
| Activity Feed | ✅ | ❌ |
| Categories/Tags | ✅ | ✅ |
| Due Dates | ✅ | ✅ |
| Member Roles | ✅ | ❌ |
| Task Details | ✅ (Rich) | ❌ (Basic) |

TaskGPT provides a comprehensive solution for team collaboration and project management, making it ideal for work teams, study groups, and any collaborative effort that requires more than basic task tracking 
