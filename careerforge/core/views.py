from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden, FileResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from jobs.models import Job
from applications.models import Application, CandidateProfile
from .models import SavedJob, Notification
from .forms import RegisterForm, ProfileForm, JobForm

def available():
    return Job.objects.filter(is_active=True).filter(Q(deadline__isnull=True)|Q(deadline__gte=timezone.localdate())).select_related('employer').prefetch_related('skills_required')
def jobs(request):
    qs=available()
    q=request.GET.get('q','').strip(); location=request.GET.get('location','').strip(); kind=request.GET.get('type','')
    if q: qs=qs.filter(Q(title__icontains=q)|Q(description__icontains=q)|Q(employer__company_name__icontains=q)|Q(skills_required__name__icontains=q)).distinct()
    if location: qs=qs.filter(location__icontains=location)
    if kind: qs=qs.filter(job_type=kind)
    saved=list(SavedJob.objects.filter(user=request.user).values_list('job_id',flat=True)) if request.user.is_authenticated else []
    saved_only=request.GET.get('saved')=='1'
    if saved_only: qs=qs.filter(pk__in=saved)
    order='-salary_max' if request.GET.get('sort')=='salary' else '-created_at'
    page=Paginator(qs.order_by(order,'-id'),9).get_page(request.GET.get('page'))
    params=request.GET.copy();params.pop('page',None)
    return render(request,'core/jobs.html',{'page':page,'q':q,'location':location,'kind':kind,'types':Job.JobType.choices,'saved_ids':saved,'saved_only':saved_only,'querystring':params.urlencode(),'total':available().count()})
def detail(request,pk):
    job=get_object_or_404(Job.objects.select_related('employer').prefetch_related('skills_required'),pk=pk)
    is_open=job.is_active and (not job.deadline or job.deadline>=timezone.localdate())
    applied=request.user.is_authenticated and Application.objects.filter(job=job,candidate=request.user).exists()
    saved=request.user.is_authenticated and SavedJob.objects.filter(job=job,user=request.user).exists()
    return render(request,'core/detail.html',{'job':job,'is_open':is_open,'applied':applied,'saved':saved})
def register(request):
    form=RegisterForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save();login(request,user);return redirect('dashboard')
    return render(request,'core/form.html',{'form':form,'title':'Your next chapter starts here.','subtitle':'Create your free CareerForge account.','button':'Create account'})
@login_required
@require_POST
def save(request,pk):
    job=get_object_or_404(Job,pk=pk)
    obj,created=SavedJob.objects.get_or_create(user=request.user,job=job)
    if not created: obj.delete()
    messages.success(request,'Job saved.' if created else 'Job removed from saved jobs.')
    return redirect('job-detail',pk=pk)
@login_required
@require_POST
def apply(request,pk):
    if request.user.role!='CANDIDATE': return HttpResponseForbidden('Only candidates may apply.')
    job=get_object_or_404(available(),pk=pk)
    note=request.POST.get('cover_note','').strip()
    if len(note)>3000:
        messages.error(request,'Keep your cover note under 3,000 characters.');return redirect('job-detail',pk=pk)
    obj,created=Application.objects.get_or_create(job=job,candidate=request.user,defaults={'cover_note':note})
    if created:
        Notification.objects.create(user=job.employer,message=f'New application for {job.title}.')
        messages.success(request,'Application sent. Track its progress in your dashboard.')
    else: messages.info(request,'You have already applied for this job.')
    return redirect('dashboard')
@login_required
def dashboard(request):
    employer=request.user.role=='EMPLOYER'
    apps=Application.objects.filter(job__employer=request.user) if employer else Application.objects.filter(candidate=request.user)
    apps=apps.select_related('job__employer','candidate').order_by('-applied_at')
    postings=Job.objects.filter(employer=request.user).order_by('-created_at') if employer else None
    return render(request,'core/dashboard.html',{'applications':apps,'postings':postings,'employer':employer,'count':apps.count(),'shortlisted':apps.filter(status='SHORTLISTED').count(),'saved_count':SavedJob.objects.filter(user=request.user).count(),'statuses':Application.Status.choices})
@login_required
@require_POST
def status(request,pk):
    application=get_object_or_404(Application,pk=pk,job__employer=request.user)
    value=request.POST.get('status')
    if value in Application.Status.values and value!=application.status:
        application.status=value;application.save(update_fields=['status'])
        Notification.objects.create(user=application.candidate,message=f'{application.job.title}: your application is now {application.get_status_display().lower()}.')
        messages.success(request,'Application status updated.')
    return redirect('dashboard')
@login_required
@require_POST
def withdraw(request,pk):
    application=get_object_or_404(Application,pk=pk,candidate=request.user)
    application.delete();messages.success(request,'Application withdrawn.');return redirect('dashboard')
@login_required
def profile(request):
    obj,_=CandidateProfile.objects.get_or_create(user=request.user)
    form=ProfileForm(request.POST or None,request.FILES or None,instance=obj)
    if request.method=='POST' and form.is_valid():
        form.save();messages.success(request,'Profile updated.');return redirect('profile')
    return render(request,'core/form.html',{'form':form,'title':'Make your experience stand out.','subtitle':'Add your skills and a PDF resume (up to 5 MB). Employers reviewing your applications can access it.','button':'Save profile','has_resume':bool(obj.resume)})
@login_required
def job_edit(request,pk=None):
    if request.user.role!='EMPLOYER':return HttpResponseForbidden('Employer account required.')
    obj=get_object_or_404(Job,pk=pk,employer=request.user) if pk else None
    form=JobForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid():
        job=form.save(commit=False);job.employer=request.user;job.save();form.save_m2m();messages.success(request,'Job saved.');return redirect('dashboard')
    return render(request,'core/form.html',{'form':form,'title':'Edit your opportunity.' if pk else 'Find your next great teammate.','subtitle':'Clear responsibilities and salary details help candidates make better decisions. Salaries are annual INR.','button':'Save job'})
@login_required
def notifications(request):
    items=Notification.objects.filter(user=request.user)
    return render(request,'core/notifications.html',{'notifications':items[:100]})
@login_required
@require_POST
def mark_read(request):
    Notification.objects.filter(user=request.user,is_read=False).update(is_read=True);return redirect('notifications')
@login_required
def updates(request):
    return JsonResponse({'unread':Notification.objects.filter(user=request.user,is_read=False).count()})
@login_required
def resume(request,pk):
    profile=get_object_or_404(CandidateProfile,user_id=pk)
    if request.user.pk!=pk and not Application.objects.filter(candidate_id=pk,job__employer=request.user).exists():
        return HttpResponseForbidden('This resume is private.')
    if not profile.resume: return HttpResponseForbidden('No resume uploaded.')
    response=FileResponse(profile.resume.open('rb'),as_attachment=True,filename='resume.pdf',content_type='application/pdf')
    response['Cache-Control']='private, no-store'
    return response
