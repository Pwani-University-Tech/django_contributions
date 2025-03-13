from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from to_do_app.views import TaskViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),  # Adds login/logout views
]
