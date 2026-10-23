from rest_framework import serializers
from .models import CandidateProfile, Application
from jobs.models import Skill
from django.utils import timezone
from django.urls import reverse
from core.forms import ProfileForm

class CandidateProfileSerializer(serializers.ModelSerializer):
    skills = serializers.SlugRelatedField(
        many=True, slug_field='name', queryset=Skill.objects.all(), required=False
    )

    def validate_resume(self, value):
        form = ProfileForm()
        form.cleaned_data = {'resume': value}
        from django.core.exceptions import ValidationError
        try:
            return form.clean_resume()
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['resume'] = reverse('resume', args=[instance.user_id]) if instance.resume else None
        return data

    class Meta:
        model = CandidateProfile
        fields = ['id', 'user', 'skills', 'resume', 'bio', 'experience_years']
        read_only_fields = ['user']

class ApplicationSerializer(serializers.ModelSerializer):
    candidate_username = serializers.ReadOnlyField(source='candidate.username')
    job_title = serializers.ReadOnlyField(source='job.title')

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_title', 'candidate', 'candidate_username',
            'status', 'applied_at', 'cover_note',
        ]
        read_only_fields = ['candidate', 'applied_at']
    def validate(self, attrs):
        user = self.context['request'].user
        if self.instance:
            allowed = {'status'} if user.role == 'EMPLOYER' else {'cover_note'}
            if set(self.initial_data) - allowed:
                raise serializers.ValidationError('Only application status (employer) or cover note (candidate) can be changed.')
        else:
            if user.role != 'CANDIDATE':
                raise serializers.ValidationError('Only candidates can apply.')
            job = attrs.get('job')
            if not job or not job.is_active or (job.deadline and job.deadline < timezone.localdate()):
                raise serializers.ValidationError('This opportunity is closed.')
            if Application.objects.filter(job=job, candidate=user).exists():
                raise serializers.ValidationError('You have already applied to this job.')
            if attrs.get('status', 'APPLIED') != 'APPLIED':
                raise serializers.ValidationError('New applications must have Applied status.')
        if len(attrs.get('cover_note','')) > 3000:
            raise serializers.ValidationError('Cover note must be at most 3,000 characters.')
        return attrs
