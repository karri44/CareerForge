from rest_framework import serializers
from .models import Job, Skill
from django.utils import timezone

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']

class JobSerializer(serializers.ModelSerializer):
    skills_required = serializers.SlugRelatedField(
        many=True, slug_field='name', queryset=Skill.objects.all()
    )
    employer_username = serializers.ReadOnlyField(source='employer.username')

    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'employer_username', 'title', 'description',
            'skills_required', 'location', 'job_type', 'salary_min',
            'salary_max', 'deadline', 'created_at', 'is_active',
        ]
        read_only_fields = ['employer', 'created_at']
    def validate(self, attrs):
        low = attrs.get('salary_min', getattr(self.instance, 'salary_min', None))
        high = attrs.get('salary_max', getattr(self.instance, 'salary_max', None))
        if low is not None and high is not None and low > high:
            raise serializers.ValidationError({'salary_max': 'Must be at least the minimum salary.'})
        if attrs.get('deadline') and attrs['deadline'] < timezone.localdate():
            raise serializers.ValidationError({'deadline':'Choose today or a future date.'})
        return attrs
