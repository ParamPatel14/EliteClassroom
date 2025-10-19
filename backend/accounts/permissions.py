from rest_framework import permissions


class IsStudent(permissions.BasePermission):
    """Permission class to check if user is a student"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'STUDENT'


class IsTeacher(permissions.BasePermission):
    """Permission class to check if user is a teacher"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'TEACHER'


class IsAdmin(permissions.BasePermission):
    """Permission class to check if user is an admin"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsStudentOrTeacher(permissions.BasePermission):
    """Permission class to check if user is either student or teacher"""
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['STUDENT', 'TEACHER'])


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission class to check if user is owner of object or admin"""
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.role == 'ADMIN':
            return True
        
        # Check if obj has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if obj is user itself
        return obj == request.user


class IsVerifiedTeacher(permissions.BasePermission):
    """Permission class to check if user is a verified teacher"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role != 'TEACHER':
            return False
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        return request.user.teacher_profile.is_verified
