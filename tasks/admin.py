from django.contrib import admin
from django.utils.html import format_html
from .models import Task, Group, GroupMember, Comment, ActivityLog, UserInvitation, TaskReassignment


class SoftDeleteAdmin(admin.ModelAdmin):
    """Base admin class for soft delete models"""
    list_display_base = ('is_deleted', 'deleted_at')
    list_filter_base = ('is_deleted',)
    actions = ['restore_items', 'soft_delete_items']
    
    def get_queryset(self, request):
        # Show all objects including soft-deleted ones in admin
        return self.model.all_objects.get_queryset()
    
    def restore_items(self, request, queryset):
        """Action to restore soft-deleted items"""
        count = 0
        for obj in queryset.filter(is_deleted=True):
            obj.restore()
            count += 1
        self.message_user(request, f'{count} item(s) successfully restored.')
    restore_items.short_description = 'Restore selected items'
    
    def soft_delete_items(self, request, queryset):
        """Action to soft delete items"""
        count = 0
        for obj in queryset.filter(is_deleted=False):
            obj.soft_delete()
            count += 1
        self.message_user(request, f'{count} item(s) successfully soft deleted.')
    soft_delete_items.short_description = 'Soft delete selected items'
    
    def deleted_status(self, obj):
        """Display deleted status with color"""
        if obj.is_deleted:
            return format_html('<span style="color: red;">Deleted</span>')
        return format_html('<span style="color: green;">Active</span>')
    deleted_status.short_description = 'Status'


@admin.register(Group)
class GroupAdmin(SoftDeleteAdmin):
    list_display = ('name', 'created_by', 'created_at', 'deleted_status')
    search_fields = ('name', 'description')
    list_filter = ('is_deleted', 'created_at')


@admin.register(GroupMember)
class GroupMemberAdmin(SoftDeleteAdmin):
    list_display = ('user', 'group', 'role', 'joined_at', 'deleted_status')
    list_filter = ('is_deleted', 'role', 'joined_at')
    search_fields = ('user__username', 'group__name')


@admin.register(Task)
class TaskAdmin(SoftDeleteAdmin):
    list_display = ('title', 'status', 'priority', 'estimated_hours', 'created_by', 'assigned_to', 'assignment_status', 'due_date', 'created_at', 'deleted_status')
    list_filter = ('is_deleted', 'status', 'priority', 'assignment_status', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'category')
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(SoftDeleteAdmin):
    list_display = ('task', 'user', 'created_at', 'deleted_status')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('comment', 'task__title', 'user__username')


@admin.register(ActivityLog)
class ActivityLogAdmin(SoftDeleteAdmin):
    list_display = ('user', 'action', 'task', 'group', 'created_at', 'deleted_status')
    list_filter = ('is_deleted', 'action', 'created_at')
    search_fields = ('user__username', 'details')


@admin.register(UserInvitation)
class UserInvitationAdmin(SoftDeleteAdmin):
    list_display = ('email', 'invited_by', 'is_used', 'created_at', 'expires_at', 'deleted_status')
    list_filter = ('is_deleted', 'is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'invited_by__username')


@admin.register(TaskReassignment)
class TaskReassignmentAdmin(SoftDeleteAdmin):
    list_display = ('task', 'from_user', 'to_user', 'created_at', 'deleted_status')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('task__title', 'from_user__username', 'to_user__username', 'reason')
