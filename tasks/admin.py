from django.contrib import admin
from .models import Task, Group, GroupMember, Comment, ActivityLog, UserInvitation, TaskReassignment


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'group__name')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'estimated_hours', 'created_by', 'assigned_to', 'assignment_status', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'assignment_status', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'category')
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment', 'task__title', 'user__username')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'task', 'group', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'details')


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'invited_by', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'invited_by__username')


@admin.register(TaskReassignment)
class TaskReassignmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'from_user', 'to_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('task__title', 'from_user__username', 'to_user__username', 'reason')
