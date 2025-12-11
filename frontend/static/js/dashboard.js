// Dashboard JavaScript

let currentUser = null;
let allTasks = [];
let allGroups = [];

// Initialize dashboard
async function init() {
    try {
        const response = await fetch('/api/user');
        if (!response.ok) {
            window.location.href = '/';
            return;
        }
        
        const user = await response.json();
        currentUser = user;
        document.getElementById('username-display').textContent = user.username;
        
        // Load initial data
        await Promise.all([
            loadTasks(),
            loadGroups(),
            loadActivity()
        ]);
        
        // Populate group filter
        populateGroupFilter();
    } catch (error) {
        console.error('Initialization error:', error);
        window.location.href = '/';
    }
}

// Logout function
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Show different sections
function showSection(section) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(s => {
        s.style.display = 'none';
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.sidebar-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(`${section}-section`).style.display = 'block';
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// Load Tasks
async function loadTasks() {
    try {
        const status = document.getElementById('status-filter').value;
        const priority = document.getElementById('priority-filter').value;
        const groupId = document.getElementById('group-filter').value;
        
        let url = '/api/tasks?';
        if (status) url += `status=${status}&`;
        if (priority) url += `priority=${priority}&`;
        if (groupId) url += `group_id=${groupId}&`;
        
        const response = await fetch(url);
        const tasks = await response.json();
        allTasks = tasks;
        
        displayTasks(tasks);
        updateTaskStats(tasks);
    } catch (error) {
        console.error('Error loading tasks:', error);
        showToast('Error loading tasks', 'error');
    }
}

function displayTasks(tasks) {
    const container = document.getElementById('tasks-container');
    
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <h3>No tasks found</h3>
                <p>Create your first task to get started!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tasks.map(task => `
        <div class="task-card priority-${task.priority}" onclick="showTaskDetails(${task.id})">
            <div class="task-header">
                <div>
                    <div class="task-title">${escapeHtml(task.title)}</div>
                    <span class="task-status status-${task.status}">${formatStatus(task.status)}</span>
                </div>
            </div>
            
            ${task.description ? `<div class="task-description">${escapeHtml(task.description.substring(0, 100))}${task.description.length > 100 ? '...' : ''}</div>` : ''}
            
            <div class="task-meta">
                <div class="task-meta-item">
                    <span>🔥 ${formatPriority(task.priority)}</span>
                </div>
                ${task.due_date ? `
                    <div class="task-meta-item">
                        <span>📅 ${formatDate(task.due_date)}</span>
                    </div>
                ` : ''}
                ${task.group_name ? `
                    <div class="task-meta-item">
                        <span class="task-badge">👥 ${escapeHtml(task.group_name)}</span>
                    </div>
                ` : ''}
                ${task.category ? `
                    <div class="task-meta-item">
                        <span class="task-badge">🏷️ ${escapeHtml(task.category)}</span>
                    </div>
                ` : ''}
                ${task.assigned_to_username ? `
                    <div class="task-meta-item">
                        <span class="task-badge">👤 ${escapeHtml(task.assigned_to_username)}</span>
                    </div>
                ` : ''}
                ${task.comment_count > 0 ? `
                    <div class="task-meta-item">
                        <span>💬 ${task.comment_count}</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function updateTaskStats(tasks) {
    const todoCount = tasks.filter(t => t.status === 'todo').length;
    const inProgressCount = tasks.filter(t => t.status === 'in_progress').length;
    const doneCount = tasks.filter(t => t.status === 'done').length;
    
    document.getElementById('todo-count').textContent = todoCount;
    document.getElementById('in-progress-count').textContent = inProgressCount;
    document.getElementById('done-count').textContent = doneCount;
}

// Load Groups
async function loadGroups() {
    try {
        const response = await fetch('/api/groups');
        const groups = await response.json();
        allGroups = groups;
        
        displayGroups(groups);
    } catch (error) {
        console.error('Error loading groups:', error);
        showToast('Error loading groups', 'error');
    }
}

function displayGroups(groups) {
    const container = document.getElementById('groups-container');
    
    if (groups.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">👥</div>
                <h3>No groups found</h3>
                <p>Create a group to collaborate with others!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = groups.map(group => `
        <div class="group-card" onclick="showGroupDetails(${group.id})">
            <div class="group-header">
                <div class="group-icon">👥</div>
                <div class="group-name">${escapeHtml(group.name)}</div>
            </div>
            
            ${group.description ? `<div class="group-description">${escapeHtml(group.description)}</div>` : ''}
            
            <div class="group-stats">
                <span>👤 ${group.member_count} member${group.member_count !== 1 ? 's' : ''}</span>
                <span>📅 ${formatDate(group.created_at)}</span>
            </div>
        </div>
    `).join('');
}

function populateGroupFilter() {
    const select = document.getElementById('group-filter');
    const taskGroupSelect = document.getElementById('task-group');
    
    const groupOptions = allGroups.map(group => 
        `<option value="${group.id}">${escapeHtml(group.name)}</option>`
    ).join('');
    
    select.innerHTML = '<option value="">All Groups</option>' + groupOptions;
    taskGroupSelect.innerHTML = '<option value="">Personal Task</option>' + groupOptions;
}

// Load Activity
async function loadActivity() {
    try {
        const response = await fetch('/api/activity');
        const activities = await response.json();
        
        displayActivity(activities);
    } catch (error) {
        console.error('Error loading activity:', error);
        showToast('Error loading activity', 'error');
    }
}

function displayActivity(activities) {
    const container = document.getElementById('activity-container');
    
    if (activities.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <h3>No activity yet</h3>
                <p>Start creating tasks and groups to see activity!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-icon">${getActivityIcon(activity.action)}</div>
            <div class="activity-content">
                <div class="activity-text">
                    <strong>${escapeHtml(activity.username)}</strong> ${activity.details}
                </div>
                <div class="activity-time">${formatDateTime(activity.created_at)}</div>
            </div>
        </div>
    `).join('');
}

function getActivityIcon(action) {
    const icons = {
        'create_task': '✓',
        'update_task': '✏️',
        'delete_task': '🗑️',
        'create_group': '👥',
        'add_member': '➕',
        'add_comment': '💬',
        'register': '👋',
        'login': '🔑'
    };
    return icons[action] || '📌';
}

// Modal functions
function showCreateTask() {
    document.getElementById('create-task-modal').style.display = 'block';
}

function showCreateGroup() {
    document.getElementById('create-group-modal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Create Task Form Handler
document.getElementById('create-task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value,
        due_date: document.getElementById('task-due-date').value || null,
        category: document.getElementById('task-category').value,
        group_id: document.getElementById('task-group').value || null
    };
    
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        if (response.ok) {
            showToast('Task created successfully!', 'success');
            closeModal('create-task-modal');
            document.getElementById('create-task-form').reset();
            await loadTasks();
            await loadActivity();
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to create task', 'error');
        }
    } catch (error) {
        console.error('Error creating task:', error);
        showToast('Error creating task', 'error');
    }
});

// Create Group Form Handler
document.getElementById('create-group-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const groupData = {
        name: document.getElementById('group-name').value,
        description: document.getElementById('group-description').value
    };
    
    try {
        const response = await fetch('/api/groups', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(groupData)
        });
        
        if (response.ok) {
            showToast('Group created successfully!', 'success');
            closeModal('create-group-modal');
            document.getElementById('create-group-form').reset();
            await loadGroups();
            populateGroupFilter();
            await loadActivity();
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to create group', 'error');
        }
    } catch (error) {
        console.error('Error creating group:', error);
        showToast('Error creating group', 'error');
    }
});

// Show Task Details
async function showTaskDetails(taskId) {
    try {
        const [taskResponse, commentsResponse] = await Promise.all([
            fetch(`/api/tasks/${taskId}`),
            fetch(`/api/tasks/${taskId}/comments`)
        ]);
        
        const task = await taskResponse.json();
        const comments = await commentsResponse.json();
        
        const content = document.getElementById('task-details-content');
        content.innerHTML = `
            <div style="padding: 30px;">
                <div style="margin-bottom: 20px;">
                    <h3 style="font-size: 1.5rem; margin-bottom: 10px;">${escapeHtml(task.title)}</h3>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;">
                        <span class="task-status status-${task.status}">${formatStatus(task.status)}</span>
                        <span class="task-badge">🔥 ${formatPriority(task.priority)}</span>
                        ${task.category ? `<span class="task-badge">🏷️ ${escapeHtml(task.category)}</span>` : ''}
                        ${task.group_name ? `<span class="task-badge">👥 ${escapeHtml(task.group_name)}</span>` : ''}
                    </div>
                </div>
                
                ${task.description ? `
                    <div style="margin-bottom: 20px;">
                        <h4 style="margin-bottom: 10px;">Description</h4>
                        <p style="color: #666; line-height: 1.6;">${escapeHtml(task.description)}</p>
                    </div>
                ` : ''}
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 10px;">Details</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div>
                            <strong>Created by:</strong> ${escapeHtml(task.created_by_username)}
                        </div>
                        ${task.assigned_to_username ? `
                            <div>
                                <strong>Assigned to:</strong> ${escapeHtml(task.assigned_to_username)}
                            </div>
                        ` : ''}
                        ${task.due_date ? `
                            <div>
                                <strong>Due date:</strong> ${formatDate(task.due_date)}
                            </div>
                        ` : ''}
                        <div>
                            <strong>Created:</strong> ${formatDateTime(task.created_at)}
                        </div>
                        <div>
                            <strong>Updated:</strong> ${formatDateTime(task.updated_at)}
                        </div>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 10px;">Update Status</h4>
                    <select id="task-status-update" class="filter-select" style="max-width: 200px;">
                        <option value="todo" ${task.status === 'todo' ? 'selected' : ''}>To Do</option>
                        <option value="in_progress" ${task.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                        <option value="done" ${task.status === 'done' ? 'selected' : ''}>Done</option>
                    </select>
                    <button onclick="updateTaskStatus(${taskId})" class="btn btn-primary" style="margin-left: 10px;">Update</button>
                    <button onclick="deleteTask(${taskId})" class="btn btn-danger" style="margin-left: 10px;">Delete Task</button>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 10px;">Comments (${comments.length})</h4>
                    <div id="comments-list" style="max-height: 300px; overflow-y: auto; margin-bottom: 15px;">
                        ${comments.length > 0 ? comments.map(comment => `
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <strong>${escapeHtml(comment.username)}</strong>
                                    <span style="color: #888; font-size: 0.85rem;">${formatDateTime(comment.created_at)}</span>
                                </div>
                                <p style="color: #555;">${escapeHtml(comment.comment)}</p>
                            </div>
                        `).join('') : '<p style="color: #888;">No comments yet</p>'}
                    </div>
                    
                    <div>
                        <textarea id="new-comment" placeholder="Add a comment..." rows="3" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-family: inherit;"></textarea>
                        <button onclick="addComment(${taskId})" class="btn btn-primary" style="margin-top: 10px;">Add Comment</button>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('task-details-modal').style.display = 'block';
    } catch (error) {
        console.error('Error loading task details:', error);
        showToast('Error loading task details', 'error');
    }
}

async function updateTaskStatus(taskId) {
    const newStatus = document.getElementById('task-status-update').value;
    
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        });
        
        if (response.ok) {
            showToast('Task updated successfully!', 'success');
            await loadTasks();
            await loadActivity();
            closeModal('task-details-modal');
        } else {
            showToast('Failed to update task', 'error');
        }
    } catch (error) {
        console.error('Error updating task:', error);
        showToast('Error updating task', 'error');
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Task deleted successfully!', 'success');
            await loadTasks();
            await loadActivity();
            closeModal('task-details-modal');
        } else {
            showToast('Failed to delete task', 'error');
        }
    } catch (error) {
        console.error('Error deleting task:', error);
        showToast('Error deleting task', 'error');
    }
}

async function addComment(taskId) {
    const commentText = document.getElementById('new-comment').value.trim();
    
    if (!commentText) {
        showToast('Please enter a comment', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ comment: commentText })
        });
        
        if (response.ok) {
            showToast('Comment added successfully!', 'success');
            showTaskDetails(taskId); // Reload task details
            await loadActivity();
        } else {
            showToast('Failed to add comment', 'error');
        }
    } catch (error) {
        console.error('Error adding comment:', error);
        showToast('Error adding comment', 'error');
    }
}

// Show Group Details
async function showGroupDetails(groupId) {
    try {
        const response = await fetch(`/api/groups/${groupId}/members`);
        const members = await response.json();
        
        const group = allGroups.find(g => g.id === groupId);
        
        const content = document.getElementById('group-details-content');
        content.innerHTML = `
            <div style="padding: 30px;">
                <div style="margin-bottom: 20px;">
                    <h3 style="font-size: 1.5rem; margin-bottom: 10px;">${escapeHtml(group.name)}</h3>
                    ${group.description ? `<p style="color: #666;">${escapeHtml(group.description)}</p>` : ''}
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 10px;">Members (${members.length})</h4>
                    <div style="max-height: 300px; overflow-y: auto;">
                        ${members.map(member => `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px; background: #f8f9fa; border-radius: 8px; margin-bottom: 10px;">
                                <div>
                                    <div style="font-weight: 600;">${escapeHtml(member.username)}</div>
                                    <div style="color: #888; font-size: 0.85rem;">${escapeHtml(member.email)}</div>
                                </div>
                                <span class="task-badge">${member.role}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 10px;">Add Member</h4>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="new-member-username" placeholder="Enter username" style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 8px;">
                        <button onclick="addGroupMember(${groupId})" class="btn btn-primary">Add Member</button>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('group-details-modal').style.display = 'block';
    } catch (error) {
        console.error('Error loading group details:', error);
        showToast('Error loading group details', 'error');
    }
}

async function addGroupMember(groupId) {
    const username = document.getElementById('new-member-username').value.trim();
    
    if (!username) {
        showToast('Please enter a username', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/groups/${groupId}/members`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username })
        });
        
        if (response.ok) {
            showToast('Member added successfully!', 'success');
            showGroupDetails(groupId); // Reload group details
            await loadActivity();
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to add member', 'error');
        }
    } catch (error) {
        console.error('Error adding member:', error);
        showToast('Error adding member', 'error');
    }
}

// Utility functions
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatStatus(status) {
    return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatPriority(priority) {
    return priority.charAt(0).toUpperCase() + priority.slice(1);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
