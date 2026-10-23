from rest_framework import permissions

class IsCandidateOwnerOrEmployerReadOnly(permissions.BasePermission):
    """Candidates manage their own applications; employers can view/update status for their jobs."""

    def has_object_permission(self, request, view, obj):
        if request.user == obj.candidate:
            return True
        if request.user == obj.job.employer:
            return request.method in permissions.SAFE_METHODS or request.method == 'PATCH'
        return False