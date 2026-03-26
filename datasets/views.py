import pandas as pd
import traceback

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum, Avg
from django.db.models.functions import TruncDate
from django.http import JsonResponse

from .models import Dataset, Record


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        errors = []
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number.")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character.")
        if errors:
            return render(request, "signup.html", {"errors": errors, "username": username})
        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {"errors": ["Username already taken."], "username": username})
        User.objects.create_user(username=username, password=password)
        return redirect("/login/?registered=1")
    return render(request, "signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            request.session.save()
            has_data = Record.objects.filter(dataset__uploaded_by=user).exists()
            if has_data:
                return redirect("/analytics/")
            return redirect("/upload/")
        return render(request, "login.html", {"error": "Invalid username or password."})
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("/login/")


def upload_dataset(request):
    if not request.user.is_authenticated:
        return redirect("/login/")
    if request.method == "GET":
        has_data = Record.objects.filter(dataset__uploaded_by=request.user).exists()
        if has_data:
            return redirect("/analytics/")
        return render(request, "upload.html", {"user": request.user})
    if request.method == "POST":
        try:
            upload_file = request.FILES.get("file")
            if not upload_file:
                return JsonResponse({"error": "No file provided."}, status=400)
            if not upload_file.name.endswith(".csv"):
                return JsonResponse({"error": "Only CSV files are allowed."}, status=400)
            if upload_file.size > 5 * 1024 * 1024:
                return JsonResponse({"error": "File too large. Max 5MB."}, status=400)
            dataset = Dataset.objects.create(
                name=upload_file.name,
                uploaded_by=request.user,
                file=upload_file
            )
            upload_file.seek(0)
            try:
                df = pd.read_csv(upload_file)
            except Exception as e:
                dataset.delete()
                return JsonResponse({"error": f"Could not parse CSV: {str(e)}"}, status=400)
            required_cols = {"customer_name", "product", "amount"}
            if not required_cols.issubset(df.columns):
                dataset.delete()
                missing = required_cols - set(df.columns)
                return JsonResponse({"error": f"Missing columns: {missing}"}, status=400)
            for _, row in df.iterrows():
                Record.objects.create(
                    customer_name=row["customer_name"],
                    product=row["product"],
                    amount=row["amount"],
                    dataset=dataset
                )
            return JsonResponse({
                "success": True,
                "dataset_id": dataset.id,
                "rows_processed": len(df),
                "redirect": "/analytics/"
            })
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)


def preview_dataset(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    if request.method == "POST":
        upload_file = request.FILES.get("file")
        if not upload_file:
            return JsonResponse({"error": "No file provided."}, status=400)
        if not upload_file.name.endswith(".csv"):
            return JsonResponse({"error": "Only CSV files are allowed."}, status=400)
        try:
            df = pd.read_csv(upload_file)
        except Exception as e:
            return JsonResponse({"error": f"Could not parse CSV: {str(e)}"}, status=400)
        required_cols = {"customer_name", "product", "amount"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            return JsonResponse({"error": f"Missing columns: {missing}"}, status=400)
        return JsonResponse({
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(orient="records"),
            "total_rows": len(df)
        })
    return JsonResponse({"error": "POST required."}, status=405)


def analytics(request):
    if not request.user.is_authenticated:
        return redirect("/login/")
    records = Record.objects.filter(dataset__uploaded_by=request.user)
    if not records.exists():
        return redirect("/upload/")
    total_revenue = records.aggregate(Sum("amount"))["amount__sum"] or 0
    avg_order = records.aggregate(Avg("amount"))["amount__avg"] or 0
    top_product = (
        records.values("product")
        .annotate(total_sales=Sum("amount"))
        .order_by("-total_sales")
        .first()
    )
    return render(request, "analytics.html", {
        "total_revenue": total_revenue,
        "avg_order": avg_order,
        "top_product": top_product["product"] if top_product else None,
        "user": request.user,
    })


def view_records(request):
    if not request.user.is_authenticated:
        return redirect("/login/")
    records = Record.objects.all()
    return render(request, "records.html", {"records": records, "user": request.user})


def dataset_history(request):
    if not request.user.is_authenticated:
        return redirect("/login/")
    datasets = Dataset.objects.all().order_by("-uploaded_at")
    return render(request, "datasets.html", {"datasets": datasets, "user": request.user})


def analytics_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    records = Record.objects.filter(dataset__uploaded_by=request.user)
    total_revenue = records.aggregate(total=Sum("amount"))["total"] or 0
    avg_order = records.aggregate(avg=Avg("amount"))["avg"] or 0
    top_product = (
        records.values("product")
        .annotate(total_sales=Sum("amount"))
        .order_by("-total_sales")
        .first()
    )
    return JsonResponse({
        "total_revenue": total_revenue,
        "average_order_value": avg_order,
        "top_product": top_product["product"] if top_product else None
    })


def sales_trend_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    trend_data = (
        Record.objects
        .filter(dataset__uploaded_by=request.user)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(total_sales=Sum("amount"))
        .order_by("date")
    )
    return JsonResponse({
        "dates": [e["date"].strftime("%Y-%m-%d") for e in trend_data],
        "sales": [e["total_sales"] for e in trend_data]
    })


def product_sales_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    min_amount = request.GET.get("min")
    max_amount = request.GET.get("max")
    queryset = Record.objects.filter(dataset__uploaded_by=request.user)
    if min_amount:
        queryset = queryset.filter(amount__gte=float(min_amount))
    if max_amount:
        queryset = queryset.filter(amount__lte=float(max_amount))
    product_data = (
        queryset.values("product")
        .annotate(total_sales=Sum("amount"))
        .order_by("-total_sales")
    )
    return JsonResponse({
        "products": [p["product"] for p in product_data],
        "sales": [p["total_sales"] for p in product_data]
    })
