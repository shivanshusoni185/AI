from django.urls import path
from .views import get_student

urlpatterns = [
    path('', get_student, name='student_details'),
]
