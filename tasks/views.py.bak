from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
import json
import logging

from .models import Task, Group, GroupMember, Comment, ActivityLog

# Get logger
logger = logging.getLogger(__name__)

# Note: @csrf_exempt is used for API endpoints to allow cross-origin requests
# In production, consider using Django REST Framework with proper token-based authentication


# Template views
def index(request):
    """Main landing page"""
    if request.user.is_authenticated:
        return render(request, 'dashboard.html')
    return render(request, 'index.html')


@login_required
def dashboard(request):
    """Dashboard page"""
    return render(request, 'dashboard.html')


# Authentication API
@csrf_exempt
@require_http_methods(["POST"])
def register_api(request):
    """Register a new user"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=409)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=409)
        
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Log activity
        ActivityLog.objects.create(
            user=user,
            action='register',
            details=f'User {username} registered'
        )
        
        # Log the user in
        login(request, user)
        
        return JsonResponse({
            'message': 'Registration successful',
            'user_id': user.id
        }, status=201)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_api(request):
    """Login user"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='login',
                details=f'User {username} logged in'
            )
            
            return JsonResponse({
                'message': 'Login successful',
                'user_id': user.id,
                'username': username
            })
        else:
            return JsonResponse({'error': 'Invalid username or password'}, status=401)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_api(request):
    """Logout user"""
    logout(request)
    return JsonResponse({'message': 'Logout successful'})


@require_http_methods(["GET"])
def current_user_api(request):
    """Get current logged in user"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    return JsonResponse({
        'user_id': request.user.id,
        'username': request.user.username
    })


# Groups API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def groups_api(request):
    """Get all groups or create a new group"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'GET':
        # Get groups where user is a member
        groups = Group.objects.filter(
            members__user=request.user
        ).annotate(
            member_count=Count('members')
        ).values(
            'id', 'name', 'description', 'created_at',
            'created_by__username', 'member_count'
        )
        
        groups_list = list(groups)
        for group in groups_list:
            group['created_by_username'] = group.pop('created_by__username')
            group['created_at'] = group['created_at'].isoformat()
        
        return JsonResponse(groups_list, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description', '')
            
            if not name:
                return JsonResponse({'error': 'Group name is required'}, status=400)
            
            group = Group.objects.create(
                name=name,
                description=description,
                created_by=request.user
            )
            
            # Add creator as admin member
            GroupMember.objects.create(
                group=group,
                user=request.user,
                role='admin'
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                group=group,
                action='create_group',
                details=f'Group {name} created'
            )
            
            return JsonResponse({
                'message': 'Group created',
                'group_id': group.id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def group_members_api(request, group_id):
    """Get group members or add a new member"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    group = get_object_or_404(Group, id=group_id)
    
    if request.method == 'GET':
        members = GroupMember.objects.filter(group=group).select_related('user').values(
            'id', 'user__id', 'user__username', 'user__email', 'role', 'joined_at'
        )
        
        members_list = list(members)
        for member in members_list:
            member['id'] = member.pop('user__id')
            member['username'] = member.pop('user__username')
            member['email'] = member.pop('user__email')
            member['joined_at'] = member['joined_at'].isoformat()
        
        return JsonResponse(members_list, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            
            if not username:
                return JsonResponse({'error': 'Username is required'}, status=400)
            
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            # Check if user is already a member
            if GroupMember.objects.filter(group=group, user=user).exists():
                return JsonResponse({'error': 'User is already a member'}, status=409)
            
            GroupMember.objects.create(group=group, user=user)
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                group=group,
                action='add_member',
                details=f'Added {username} to group'
            )
            
            return JsonResponse({'message': 'Member added successfully'}, status=201)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Tasks API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def tasks_api(request):
    """Get all tasks or create a new task"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'GET':
        # Get filters from query parameters
        status = request.GET.get('status')
        priority = request.GET.get('priority')
        group_id = request.GET.get('group_id')
        
        # Get tasks user has access to
        tasks = Task.objects.filter(
            Q(created_by=request.user) |
            Q(assigned_to=request.user) |
            Q(group__members__user=request.user)
        ).distinct().select_related(
            'created_by', 'assigned_to', 'group'
        ).annotate(
            comment_count=Count('comments')
        )
        
        if status:
            tasks = tasks.filter(status=status)
        if priority:
            tasks = tasks.filter(priority=priority)
        if group_id:
            tasks = tasks.filter(group_id=group_id)
        
        tasks_list = []
        for task in tasks:
            tasks_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'category': task.category,
                'group_id': task.group_id,
                'group_name': task.group.name if task.group else None,
                'created_by': task.created_by_id,
                'created_by_username': task.created_by.username,
                'assigned_to': task.assigned_to_id,
                'assigned_to_username': task.assigned_to.username if task.assigned_to else None,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat(),
                'comment_count': task.comment_count
            })
        
        return JsonResponse(tasks_list, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            
            if not title:
                return JsonResponse({'error': 'Task title is required'}, status=400)
            
            task = Task.objects.create(
                title=title,
                description=data.get('description', ''),
                status=data.get('status', 'todo'),
                priority=data.get('priority', 'medium'),
                due_date=data.get('due_date'),
                category=data.get('category', ''),
                group_id=data.get('group_id'),
                created_by=request.user,
                assigned_to_id=data.get('assigned_to')
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                task=task,
                group=task.group,
                action='create_task',
                details=f'Task "{title}" created'
            )
            
            return JsonResponse({
                'message': 'Task created',
                'task_id': task.id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def task_detail_api(request, task_id):
    """Get, update or delete a specific task"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'category': task.category,
            'group_id': task.group_id,
            'group_name': task.group.name if task.group else None,
            'created_by': task.created_by_id,
            'created_by_username': task.created_by.username,
            'assigned_to': task.assigned_to_id,
            'assigned_to_username': task.assigned_to.username if task.assigned_to else None,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            for field in ['title', 'description', 'status', 'priority', 'due_date', 'assigned_to', 'category']:
                if field in data:
                    if field == 'assigned_to':
                        setattr(task, f'{field}_id', data[field])
                    else:
                        setattr(task, field, data[field])
            
            task.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                task=task,
                action='update_task',
                details='Task updated'
            )
            
            return JsonResponse({'message': 'Task updated'})
        
        except Exception as e:
            # Log error for debugging, return generic message
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating task {task_id}: {str(e)}")
            return JsonResponse({'error': 'An error occurred while updating the task'}, status=500)
    
    elif request.method == 'DELETE':
        # Store task info before deleting
        task_title = task.title
        task_id_ref = task.id
        
        # Delete the task first
        task.delete()
        
        # Log activity after deleting (without task reference)
        ActivityLog.objects.create(
            user=request.user,
            task=None,
            action='delete_task',
            details=f'Task "{task_title}" (ID: {task_id_ref}) deleted'
        )
        
        return JsonResponse({'message': 'Task deleted'})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def task_comments_api(request, task_id):
    """Get comments for a task or add a new comment"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'GET':
        comments = Comment.objects.filter(task=task).select_related('user').values(
            'id', 'comment', 'created_at', 'user__username'
        )
        
        comments_list = list(comments)
        for comment in comments_list:
            comment['username'] = comment.pop('user__username')
            comment['created_at'] = comment['created_at'].isoformat()
        
        return JsonResponse(comments_list, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            comment_text = data.get('comment')
            
            if not comment_text:
                return JsonResponse({'error': 'Comment text is required'}, status=400)
            
            comment = Comment.objects.create(
                task=task,
                user=request.user,
                comment=comment_text
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                task=task,
                action='add_comment',
                details='Comment added'
            )
            
            return JsonResponse({
                'message': 'Comment added',
                'comment_id': comment.id
            }, status=201)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def activity_api(request):
    """Get recent activity"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    # Get activity for user's groups and tasks
    activities = ActivityLog.objects.filter(
        Q(group__members__user=request.user) | Q(user=request.user)
    ).distinct().select_related('user')[:50]
    
    activities_list = []
    for activity in activities:
        activities_list.append({
            'id': activity.id,
            'user_id': activity.user_id,
            'username': activity.user.username,
            'task_id': activity.task_id,
            'group_id': activity.group_id,
            'action': activity.action,
            'details': activity.details,
            'created_at': activity.created_at.isoformat()
        })
    
    return JsonResponse(activities_list, safe=False)
