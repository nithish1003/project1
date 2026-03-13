from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import User


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
        "staff_count": User.objects.filter(role="staff").count(),
        "policyholder_count": User.objects.filter(role="policyholder").count(),
    }

    return render(request, "accounts/dashboard_admin.html", context)


@login_required
def staff_dashboard(request):

    return render(request, "accounts/dashboard_staff.html")


@login_required
def policyholder_dashboard(request):

    return render(request, "accounts/dashboard_policyholder.html")


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