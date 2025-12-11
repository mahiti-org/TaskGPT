from django.urls import path
from . import views

urlpatterns = [
    # Template views
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    
    # Authentication API
    path('api/register', views.register_api, name='register_api'),
    path('api/login', views.login_api, name='login_api'),
    path('api/logout', views.logout_api, name='logout_api'),
    path('api/user', views.current_user_api, name='current_user_api'),
    
    # Groups API
    path('api/groups', views.groups_api, name='groups_api'),
    path('api/groups/<int:group_id>/members', views.group_members_api, name='group_members_api'),
    
    # Tasks API
    path('api/tasks', views.tasks_api, name='tasks_api'),
    path('api/tasks/<int:task_id>', views.task_detail_api, name='task_detail_api'),
    path('api/tasks/<int:task_id>/comments', views.task_comments_api, name='task_comments_api'),
    
    # Activity API
    path('api/activity', views.activity_api, name='activity_api'),
]
