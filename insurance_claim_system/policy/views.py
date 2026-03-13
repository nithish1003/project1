from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string

from .models import (
    PolicyHolder,
    Policy,
    Coverage,
    Beneficiary,
    Premium,
    PolicyDocument,
    PolicyAuditLog
)


# -----------------------------
# POLICY LIST
# -----------------------------
@login_required
def policy_list(request):

    policies = Policy.objects.select_related("holder").all()

    return render(request, "policy/policy_list.html", {
        "policies": policies
    })


# -----------------------------
# CREATE POLICY
# -----------------------------
@login_required
def create_policy(request):

    holder = get_object_or_404(PolicyHolder, user=request.user)

    if request.method == "POST":

        policy_number = "POL-" + get_random_string(6).upper()

        policy = Policy.objects.create(
            policy_number=policy_number,
            holder=holder,
            policy_type=request.POST.get("policy_type"),
            insurer_name=request.POST.get("insurer_name"),
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
            sum_insured=request.POST.get("sum_insured"),
            premium=request.POST.get("premium"),
            status="draft"
        )

        PolicyAuditLog.objects.create(
            policy=policy,
            performed_by=request.user,
            action="Policy Created",
            description="New policy created"
        )

        messages.success(request, "Policy created successfully")

        return redirect("policy_detail", id=policy.id)

    return render(request, "policy/policy_create.html")


# -----------------------------
# POLICY DETAIL
# -----------------------------
@login_required
def policy_detail(request, id):

    policy = get_object_or_404(Policy, id=id)

    coverages = policy.coverages.all()
    beneficiaries = policy.beneficiaries.all()
    premiums = policy.premiums.all()
    documents = policy.documents.all()
    logs = policy.logs.all()

    return render(request, "policy/policy_detail.html", {
        "policy": policy,
        "coverages": coverages,
        "beneficiaries": beneficiaries,
        "premiums": premiums,
        "documents": documents,
        "logs": logs
    })


# -----------------------------
# EDIT POLICY
# -----------------------------
@login_required
def edit_policy(request, id):

    policy = get_object_or_404(Policy, id=id)

    if request.method == "POST":

        policy.insurer_name = request.POST.get("insurer_name")
        policy.start_date = request.POST.get("start_date")
        policy.end_date = request.POST.get("end_date")
        policy.sum_insured = request.POST.get("sum_insured")
        policy.premium = request.POST.get("premium")
        policy.status = request.POST.get("status")

        policy.save()

        PolicyAuditLog.objects.create(
            policy=policy,
            performed_by=request.user,
            action="Policy Updated",
            description="Policy information updated"
        )

        messages.success(request, "Policy updated successfully")

        return redirect("policy_detail", id=policy.id)

    return render(request, "policy/policy_edit.html", {
        "policy": policy
    })


# -----------------------------
# DELETE POLICY
# -----------------------------
@login_required
def delete_policy(request, id):

    policy = get_object_or_404(Policy, id=id)

    if request.method == "POST":

        PolicyAuditLog.objects.create(
            policy=policy,
            performed_by=request.user,
            action="Policy Deleted",
            description="Policy removed from system"
        )

        policy.delete()

        messages.success(request, "Policy deleted successfully")

        return redirect("policy_list")

    return render(request, "policys/policy_delete.html", {
        "policy": policy
    })