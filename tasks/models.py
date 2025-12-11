from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Group(models.Model):
    """Team/Group model for collaboration"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class GroupMember(models.Model):
    """Group membership model"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('group', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


class Task(models.Model):
    """Task model"""
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    ASSIGNMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    
    # New fields for enhanced task management
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Estimated effort in hours")
    estimated_minutes = models.IntegerField(default=0, help_text="Additional minutes (0-59)")
    completion_notes = models.TextField(blank=True, help_text="Notes added when marking task as done")
    completed_at = models.DateTimeField(null=True, blank=True)
    assignment_status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS_CHOICES, default='accepted')
    rejection_reason = models.TextField(blank=True)
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_estimated_effort_hours(self):
        """Get total estimated effort in hours"""
        return float(self.estimated_hours) + (self.estimated_minutes / 60.0)
    
    def get_age_days(self):
        """Get task age in days"""
        return (timezone.now() - self.created_at).days
    
    def get_completion_time_days(self):
        """Get time taken to complete task in days"""
        if self.completed_at:
            return (self.completed_at - self.created_at).days
        return None

    class Meta:
        ordering = ['-created_at']


class Comment(models.Model):
    """Comment model for task discussions"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"

    class Meta:
        ordering = ['-created_at']


class ActivityLog(models.Model):
    """Activity log model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.action}"

    class Meta:
        ordering = ['-created_at']


class UserInvitation(models.Model):
    """User invitation model for email-based registration"""
    email = models.EmailField(unique=True)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    token = models.CharField(max_length=100, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"Invitation for {self.email}"
    
    def is_expired(self):
        """Check if invitation is expired"""
        return timezone.now() > self.expires_at
    
    class Meta:
        ordering = ['-created_at']


class TaskReassignment(models.Model):
    """Track task reassignments"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='reassignments')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reassignments_from')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reassignments_to')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.task.title} reassigned from {self.from_user.username} to {self.to_user.username}"
    
    class Meta:
        ordering = ['-created_at']
