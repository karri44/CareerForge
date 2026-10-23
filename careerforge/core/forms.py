from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from accounts.models import User
from applications.models import CandidateProfile
from jobs.models import Job
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username','first_name','email','role','company_name']
    def clean(self):
        data = super().clean()
        if data.get('role') == 'EMPLOYER' and not data.get('company_name'):
            self.add_error('company_name','Enter your company name.')
        return data
class ProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['bio','skills','experience_years','resume']
        widgets = {'bio': forms.Textarea(attrs={'rows':4}), 'resume': forms.FileInput(attrs={'accept':'application/pdf'})}
    def clean_resume(self):
        f = self.cleaned_data.get('resume')
        if f and hasattr(f, 'content_type'):
            if f.size > 5 * 1024 * 1024: raise forms.ValidationError('Maximum file size is 5 MB.')
            if not f.name.lower().endswith('.pdf') or f.read(5) != b'%PDF-':
                raise forms.ValidationError('Please upload a valid PDF resume.')
            f.seek(0)
        return f
class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title','description','location','job_type','skills_required','salary_min','salary_max','deadline','is_active']
        widgets = {'deadline':forms.DateInput(attrs={'type':'date'}),'description':forms.Textarea(attrs={'rows':8})}
    def clean(self):
        d=super().clean()
        if d.get('salary_min') is not None and d.get('salary_max') is not None and d['salary_min']>d['salary_max']:
            self.add_error('salary_max','Maximum salary must be at least the minimum.')
        if d.get('deadline') and d['deadline'] < timezone.localdate():
            self.add_error('deadline','Choose today or a future date.')
        return d
