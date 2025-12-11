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
                'estimated_hours': float(task.estimated_hours),
                'estimated_minutes': task.estimated_minutes,
                'assignment_status': task.assignment_status,
                'completion_notes': task.completion_notes,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'age_days': task.get_age_days(),
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
            estimated_hours = data.get('estimated_hours')
            estimated_minutes = data.get('estimated_minutes', 0)
            
            if not title:
                return JsonResponse({'error': 'Task title is required'}, status=400)
            
            if not estimated_hours:
                return JsonResponse({'error': 'Estimated effort (hours) is required'}, status=400)
            
            # Set assignment status based on whether task is assigned
            assigned_to_id = data.get('assigned_to')
            assignment_status = 'pending' if assigned_to_id and assigned_to_id != request.user.id else 'accepted'
            
            task = Task.objects.create(
                title=title,
                description=data.get('description', ''),
                status=data.get('status', 'todo'),
                priority=data.get('priority', 'medium'),
                due_date=data.get('due_date'),
                category=data.get('category', ''),
                estimated_hours=estimated_hours,
                estimated_minutes=estimated_minutes,
                assignment_status=assignment_status,
                group_id=data.get('group_id'),
                created_by=request.user,
                assigned_to_id=assigned_to_id
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
            logger.error(f"Error creating task: {str(e)}")
            return JsonResponse({'error': 'An error occurred while creating the task'}, status=500)


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
        # Soft delete the task
        task.soft_delete()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            task=task,
            action='delete_task',
            details=f'Task "{task.title}" soft deleted'
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


# New API endpoints for enhanced functionality

@require_http_methods(["GET"])
def dashboard_metrics_api(request):
    """Get dashboard metrics for the user"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    from django.db.models import Avg, F
    from datetime import timedelta
    
    # Get user's tasks
    user_tasks = Task.objects.filter(
        Q(assigned_to=request.user) | Q(created_by=request.user)
    ).distinct()
    
    # Tasks at hand (pending and in progress)
    tasks_at_hand = user_tasks.filter(status__in=['todo', 'in_progress']).count()
    
    # Overdue tasks
    from django.utils import timezone as tz
    overdue_tasks = user_tasks.filter(
        status__in=['todo', 'in_progress'],
        due_date__lt=tz.now().date()
    ).count()
    
    # Task aging (average age of open tasks in days)
    open_tasks = user_tasks.filter(status__in=['todo', 'in_progress'])
    if open_tasks.exists():
        avg_age = sum([task.get_age_days() for task in open_tasks]) / open_tasks.count()
    else:
        avg_age = 0
    
    # Completion speed (average days to complete tasks)
    completed_tasks = user_tasks.filter(status='done', completed_at__isnull=False)
    if completed_tasks.exists():
        completion_times = [task.get_completion_time_days() for task in completed_tasks if task.get_completion_time_days() is not None]
        avg_completion_speed = sum(completion_times) / len(completion_times) if completion_times else 0
    else:
        avg_completion_speed = 0
    
    # Tasks completed in last 7 days
    seven_days_ago = tz.now() - timedelta(days=7)
    recent_completions = completed_tasks.filter(completed_at__gte=seven_days_ago).count()
    
    # Pending assignments (tasks assigned to user that are pending acceptance)
    pending_assignments = user_tasks.filter(
        assigned_to=request.user,
        assignment_status='pending'
    ).count()
    
    return JsonResponse({
        'tasks_at_hand': tasks_at_hand,
        'overdue_tasks': overdue_tasks,
        'avg_age_days': round(avg_age, 1),
        'avg_completion_days': round(avg_completion_speed, 1),
        'recent_completions': recent_completions,
        'pending_assignments': pending_assignments,
        'total_tasks': user_tasks.count(),
        'completed_tasks': completed_tasks.count()
    })


@csrf_exempt
@require_http_methods(["POST"])
def complete_task_api(request, task_id):
    """Complete a task with notes"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions: only assigned user or task owner can mark as done
    if task.assigned_to:
        if request.user != task.assigned_to and request.user != task.created_by:
            return JsonResponse({'error': 'Only the assigned person or task owner can mark this task as done'}, status=403)
    elif request.user != task.created_by:
        return JsonResponse({'error': 'Only the task owner can mark this task as done'}, status=403)
    
    try:
        data = json.loads(request.body)
        completion_notes = data.get('completion_notes', '')
        
        task.status = 'done'
        task.completion_notes = completion_notes
        task.completed_at = timezone.now()
        task.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            task=task,
            group=task.group,
            action='complete_task',
            details=f'Task "{task.title}" marked as done'
        )
        
        return JsonResponse({'message': 'Task completed successfully'})
    
    except Exception as e:
        logger.error(f"Error completing task {task_id}: {str(e)}")
        return JsonResponse({'error': 'An error occurred while completing the task'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reassign_task_api(request, task_id):
    """Reassign a task to another user"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    task = get_object_or_404(Task, id=task_id)
    
    # Only assigned user can reassign (if task was assigned by someone else)
    if task.assigned_to != request.user:
        return JsonResponse({'error': 'Only the assigned person can reassign this task'}, status=403)
    
    if task.created_by == request.user:
        return JsonResponse({'error': 'You cannot reassign tasks you created yourself'}, status=400)
    
    try:
        data = json.loads(request.body)
        to_username = data.get('to_username')
        reason = data.get('reason', '')
        
        if not to_username:
            return JsonResponse({'error': 'Target username is required'}, status=400)
        
        try:
            to_user = User.objects.get(username=to_username)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Create reassignment record
        from .models import TaskReassignment
        TaskReassignment.objects.create(
            task=task,
            from_user=request.user,
            to_user=to_user,
            reason=reason
        )
        
        # Update task
        task.assigned_to = to_user
        task.assignment_status = 'pending'
        task.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            task=task,
            group=task.group,
            action='reassign_task',
            details=f'Task "{task.title}" reassigned from {request.user.username} to {to_username}'
        )
        
        return JsonResponse({'message': 'Task reassigned successfully'})
    
    except Exception as e:
        logger.error(f"Error reassigning task {task_id}: {str(e)}")
        return JsonResponse({'error': 'An error occurred while reassigning the task'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def accept_task_api(request, task_id):
    """Accept a task assignment"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    task = get_object_or_404(Task, id=task_id)
    
    if task.assigned_to != request.user:
        return JsonResponse({'error': 'This task is not assigned to you'}, status=403)
    
    if task.assignment_status != 'pending':
        return JsonResponse({'error': 'This task is not pending acceptance'}, status=400)
    
    task.assignment_status = 'accepted'
    task.save()
    
    # Log activity
    ActivityLog.objects.create(
        user=request.user,
        task=task,
        group=task.group,
        action='accept_task',
        details=f'Task "{task.title}" accepted by {request.user.username}'
    )
    
    return JsonResponse({'message': 'Task accepted successfully'})


@csrf_exempt
@require_http_methods(["POST"])
def reject_task_api(request, task_id):
    """Reject a task assignment with reason"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    task = get_object_or_404(Task, id=task_id)
    
    if task.assigned_to != request.user:
        return JsonResponse({'error': 'This task is not assigned to you'}, status=403)
    
    if task.assignment_status != 'pending':
        return JsonResponse({'error': 'This task is not pending acceptance'}, status=400)
    
    try:
        data = json.loads(request.body)
        rejection_reason = data.get('reason', '')
        
        if not rejection_reason:
            return JsonResponse({'error': 'Rejection reason is required'}, status=400)
        
        task.assignment_status = 'rejected'
        task.rejection_reason = rejection_reason
        task.assigned_to = None  # Unassign the task
        task.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            task=task,
            group=task.group,
            action='reject_task',
            details=f'Task "{task.title}" rejected by {request.user.username}: {rejection_reason}'
        )
        
        return JsonResponse({'message': 'Task rejected successfully'})
    
    except Exception as e:
        logger.error(f"Error rejecting task {task_id}: {str(e)}")
        return JsonResponse({'error': 'An error occurred while rejecting the task'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_invitation_api(request):
    """Send invitation to a user via email"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User with this email already exists'}, status=409)
        
        # Check if invitation already sent
        from .models import UserInvitation
        if UserInvitation.objects.filter(email=email, is_used=False).exists():
            return JsonResponse({'error': 'Invitation already sent to this email'}, status=409)
        
        # Generate token
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Create invitation
        from datetime import timedelta
        expires_at = timezone.now() + timedelta(days=7)
        
        invitation = UserInvitation.objects.create(
            email=email,
            invited_by=request.user,
            token=token,
            expires_at=expires_at
        )
        
        # In a real application, send email here
        # For now, return the invitation link
        invitation_link = f"/register-invite?token={token}"
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='send_invitation',
            details=f'Invitation sent to {email}'
        )
        
        return JsonResponse({
            'message': 'Invitation sent successfully',
            'invitation_link': invitation_link
        }, status=201)
    
    except Exception as e:
        logger.error(f"Error sending invitation: {str(e)}")
        return JsonResponse({'error': 'An error occurred while sending the invitation'}, status=500)


def register_invite_page(request):
    """Registration page for invited users"""
    token = request.GET.get('token')
    
    if not token:
        return render(request, 'index.html')
    
    from .models import UserInvitation
    try:
        invitation = UserInvitation.objects.get(token=token, is_used=False)
        
        if invitation.is_expired():
            return render(request, 'index.html', {'error': 'Invitation has expired'})
        
        return render(request, 'register_invite.html', {
            'token': token,
            'email': invitation.email
        })
    except UserInvitation.DoesNotExist:
        return render(request, 'index.html', {'error': 'Invalid invitation'})


@csrf_exempt
@require_http_methods(["POST"])
def register_invite_api(request):
    """Complete registration via invitation"""
    try:
        data = json.loads(request.body)
        token = data.get('token')
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([token, username, email, password]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        from .models import UserInvitation
        try:
            invitation = UserInvitation.objects.get(token=token, is_used=False)
        except UserInvitation.DoesNotExist:
            return JsonResponse({'error': 'Invalid or expired invitation'}, status=404)
        
        if invitation.is_expired():
            return JsonResponse({'error': 'Invitation has expired'}, status=400)
        
        if invitation.email != email:
            return JsonResponse({'error': 'Email does not match invitation'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=409)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already registered'}, status=409)
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Mark invitation as used
        invitation.is_used = True
        invitation.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=user,
            action='register_via_invitation',
            details=f'User {username} registered via invitation from {invitation.invited_by.username}'
        )
        
        # Log the user in
        login(request, user)
        
        return JsonResponse({
            'message': 'Registration successful',
            'user_id': user.id
        }, status=201)
    
    except Exception as e:
        logger.error(f"Error in invitation registration: {str(e)}")
        return JsonResponse({'error': 'An error occurred during registration'}, status=500)
