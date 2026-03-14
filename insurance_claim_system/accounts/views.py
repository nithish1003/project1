from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from datetime import date, timedelta
from .forms import RegisterForm
from .models import User
from policy.models import Policy
from claims.models import Claim
from premiums.models import PremiumPayment


# REGISTER

def register_view(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            password = form.cleaned_data["password"]

            user.set_password(password)

            user.save()

            messages.success(request,"Account created successfully")

            return redirect("accounts:login")

        else:

            messages.error(request,"Please fix the errors below")

    else:

        form = RegisterForm()

    return render(request,"accounts/register.html",{"form":form})
    

# DASHBOARDS

@login_required
def admin_dashboard(request):

    context = {
        "total_users": User.objects.count(),
        "total_policies": Policy.objects.count(),
        "total_claims": Claim.objects.count(),
        "pending_claims": Claim.objects.filter(status__in=["under_review", "investigation"]).count(),
        "approved_claims": Claim.objects.filter(status="approved").count(),
        "rejected_claims": Claim.objects.filter(status="rejected").count(),
        "total_premium": PremiumPayment.objects.filter(status='success').aggregate(total=Sum('amount'))['total'] or 0,
        "recent_claims": Claim.objects.select_related('policy__holder__user').order_by('-created_at')[:5],
        "recent_policies": Policy.objects.select_related('holder__user').order_by('-created_at')[:5],
    }

    return render(request, "accounts/dashboard_admin.html", context)


@login_required
def staff_dashboard(request):

    context = {}
    try:
        claims = Claim.objects.all()

        total_claims = claims.count()
        submitted = claims.filter(status='submitted').count()
        # Including all positive outcome states under 'approved' for KPI visually
        approved = claims.filter(status__in=['approved', 'partially_approved', 'settled']).count() 
        rejected = claims.filter(status='rejected').count()

        context['kpi'] = {
            'total_claims': total_claims,
            'submitted_claims': submitted,
            'approved_claims': approved,
            'rejected_claims': rejected,
        }

        # Status summary breakdown
        status_counts = claims.values('status').annotate(count=Count('id'))
        summary = []
        for s in status_counts:
            status = s['status']
            count = s['count']
            pct = (count / total_claims * 100) if total_claims > 0 else 0
            
            bar_class = 'bg-secondary'
            if status in ['approved', 'partially_approved', 'settled']:
                bar_class = 'bg-success'
            elif status in ['under_review', 'investigation']:
                bar_class = 'bg-warning'
            elif status == 'submitted':
                bar_class = 'bg-primary'
            elif status == 'rejected':
                bar_class = 'bg-danger'

            summary.append({
                'label': status.replace('_', ' ').title(),
                'count': count,
                'percentage': pct,
                'bar_class': bar_class
            })
        
        context['claim_status_summary'] = summary
        
        context['recent_claims'] = claims.select_related('policy').order_by('-created_at')[:5]
        context['pending_claims'] = claims.filter(
            status__in=['submitted', 'under_review', 'investigation']
        ).select_related('policy__holder').order_by('created_at')[:10]

    except Exception as e:
        context['kpi'] = {'total_claims': 0, 'submitted_claims': 0, 'approved_claims': 0, 'rejected_claims': 0}
        context['claim_status_summary'] = []
        context['recent_claims'] = []
        context['pending_claims'] = []

    return render(request, "accounts/dashboard_staff.html", context)


@login_required
def policyholder_dashboard(request):

    context = {}
    
    try:
        holder = request.user.policyholder
        policies = Policy.objects.filter(holder=holder)
        claims = Claim.objects.filter(policy__holder=holder)
        
        # KPI
        active_policies = policies.filter(status='active')
        open_claims = claims.filter(status__in=['submitted', 'under_review', 'investigation', 'partially_approved'])
        
        total_sum = active_policies.aggregate(total=Sum('sum_insured'))['total'] or 0
        total_settled = claims.filter(status='settled').aggregate(total=Sum('settled_amount'))['total'] or 0
        
        context['kpi'] = {
            'total_policies': policies.count(),
            'active_policies': active_policies.count(),
            'total_claims': claims.count(),
            'open_claims': open_claims.count(),
            'total_sum_insured': total_sum,
            'total_settled': total_settled,
        }
        
        # Expiring policies
        today = date.today()
        expiring = active_policies.filter(end_date__gte=today, end_date__lte=today + timedelta(days=30))
        expiring_policies = []
        for p in expiring:
            p.days_left = (p.end_date - today).days
            expiring_policies.append(p)
            
        context['expiring_policies'] = expiring_policies
        context['policies'] = policies.order_by('-created_at')[:10]
        
        # Claim summary
        total_claims_count = claims.count()
        status_counts = claims.values('status').annotate(count=Count('id'))
        
        claim_status_summary = []
        for s in status_counts:
            status = s['status']
            count = s['count']
            pct = (count / total_claims_count * 100) if total_claims_count > 0 else 0
            
            bar_class = 'bg-secondary'
            if status in ['approved', 'settled']: bar_class = 'bg-success'
            elif status in ['under_review', 'investigation']: bar_class = 'bg-warning'
            elif status == 'submitted': bar_class = 'bg-primary'
            elif status == 'rejected': bar_class = 'bg-danger'
            
            claim_status_summary.append({
                'label': status.replace('_', ' ').title(),
                'count': count,
                'percentage': pct,
                'bar_class': bar_class
            })
            
        context['claim_status_summary'] = claim_status_summary
        
        context['recent_claims'] = claims.order_by('-created_at')[:5]
        context['settled_claims'] = claims.filter(status='settled').select_related('settlement').order_by('-updated_at')[:5]
        
    except Exception as e:
        context['kpi'] = {
            'total_policies': 0, 'active_policies': 0,
            'total_claims': 0, 'open_claims': 0,
            'total_sum_insured': 0, 'total_settled': 0,
        }
        context['policies'] = []
        context['expiring_policies'] = []
        context['claim_status_summary'] = []
        context['recent_claims'] = []
        context['settled_claims'] = []

    return render(request, "accounts/dashboard_policyholder.html", context)


# LOGIN

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,username=username,password=password)

        if user is not None:

            login(request,user)

            if user.role == "admin":
                return redirect("accounts:admin_dashboard")

            elif user.role == "staff":
                return redirect("accounts:staff_dashboard")

            else:
                return redirect("accounts:policyholder_dashboard")

        else:

            messages.error(request,"Invalid username or password")

    return render(request,"accounts/login.html")


# LOGOUT

def logout_view(request):

    logout(request)

    return redirect("accounts:login")


def unauthorized_view(request):

    return render(request,"accounts/unauthorized.html")