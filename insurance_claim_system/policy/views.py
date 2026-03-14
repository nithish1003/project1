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

    # Allow both Django superusers and users with admin role
    if not (request.user.is_superuser or request.user.is_admin):
        return render(request, "policy/admin_only.html", {
            "message": "Admin only can create the policy"
        })

    # Get all policyholders for selection
    policyholders = PolicyHolder.objects.select_related('user').all()

    if not policyholders.exists():
        messages.error(request, "No policyholders found. Please create policyholder accounts first.")
        return redirect("policy:list")

    if request.method == "POST":

        # Get the selected policyholder
        holder_id = request.POST.get("policyholder_id")
        try:
            holder = PolicyHolder.objects.get(id=holder_id)
        except PolicyHolder.DoesNotExist:
            messages.error(request, "Selected policyholder does not exist.")
            return redirect("policy_create")

        policy_number = "POL-" + get_random_string(6).upper()

        policy = Policy.objects.create(
            policy_number=policy_number,
            holder=holder,
            policy_type=request.POST.get("policy_type"),
            insurer_name=request.POST.get("insurer"),
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
            sum_insured=request.POST.get("sum_insured"),
            premium=request.POST.get("premium", 0),
            deductible_amount=request.POST.get("deductible_amount", 0),
            status="draft"
        )

        PolicyAuditLog.objects.create(
            policy=policy,
            performed_by=request.user,
            action="Policy Created",
            description="New policy created"
        )

        messages.success(request, "Policy created successfully")

        return redirect("policy:detail", id=policy.id)

    return render(request, "policy/policy_create.html", {
        "policyholders": policyholders
    })


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

    if not (request.user.is_superuser or getattr(request.user, 'role', '') in ['admin', 'staff'] or getattr(request.user, 'is_admin', False)):
        return render(request, "policy/admin_only.html", {
            "message": "Only admins and staff can edit the policy"
        })

    if request.method == "POST":

        policy.insurer_name = request.POST.get("insurer_name")
        policy.start_date = request.POST.get("start_date")
        policy.end_date = request.POST.get("end_date")
        policy.sum_insured = request.POST.get("sum_insured")
        policy.premium = request.POST.get("premium")
        policy.deductible_amount = request.POST.get("deductible_amount")
        policy.status = request.POST.get("status")

        policy.save()

        PolicyAuditLog.objects.create(
            policy=policy,
            performed_by=request.user,
            action="Policy Updated",
            description="Policy information updated"
        )

        messages.success(request, "Policy updated successfully")

        return redirect("policy:detail", id=policy.id)

    return render(request, "policy/policy_edit.html", {
        "policy": policy
    })


@login_required
def update_policy_status(request, id):

    policy = get_object_or_404(Policy, id=id)

    if request.method == "POST":

        status = request.POST.get("status")

        policy.status = status
        policy.save()

        PolicyAuditLog.objects.create(
            policy=policy,
            performed_by=request.user,
            action=f"Status updated to {status}",
            description="Policy status updated"
        )

        messages.success(request, "Policy status updated")

    return redirect("policy:detail", id=policy.id)


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