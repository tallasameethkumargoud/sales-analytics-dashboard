import pandas as pd

from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Sum, Avg
from django.http import JsonResponse

from .models import Dataset, Record


def upload_dataset(request):
    if request.method == "POST":
        upload_file = request.FILES["file"]
        user = User.objects.first()

        dataset = Dataset.objects.create(
            name=upload_file.name,
            uploaded_by=user,
            file=upload_file
        )

        upload_file.seek(0)

        df = pd.read_csv(upload_file)

        for _, row in df.iterrows():
            Record.objects.create(
                customer_name=row["customer_name"],
                product=row["product"],
                amount=row["amount"],
                dataset=dataset
            )

        return render(request, "success.html")
    return render(request, "upload.html")


def view_records(request):
    records = Record.objects.all()
    return render(request, "records.html", {"records": records})


def analytics(request):
    total_revenue = Record.objects.aggregate(Sum("amount"))["amount__sum"]
    avg_order = Record.objects.aggregate(Avg("amount"))["amount__avg"]

    top_product = (
        Record.objects
        .values("product")
        .annotate(total_sales=Sum("amount"))
        .order_by("-total_sales")
        .first()
    )

    context = {
        "total_revenue": total_revenue,
        "avg_order": avg_order,
        "top_product": top_product["product"] if top_product else None,
    }

    return render(request, "analytics.html", context)


def dataset_history(request):
    datasets = Dataset.objects.all().order_by("-uploaded_at")
    return render(request, "datasets.html", {"datasets": datasets})


def analytics_api(request):
    total_revenue = Record.objects.aggregate(total=Sum("amount"))["total"]
    avg_order = Record.objects.aggregate(avg=Avg("amount"))["avg"] or 0

    top_product = (
        Record.objects
        .values("product")
        .annotate(total_sales=Sum("amount"))
        .order_by("-total_sales")
        .first()
    )

    return JsonResponse({
        "total_revenue": total_revenue,
        "average_order_value": avg_order,
        "top_product": top_product["product"] if top_product else None
    })


def product_sales_api(request):
    product_data = (
        Record.objects
        .values("product")
        .annotate(total_sales=Sum("amount"))
        .order_by("-total_sales")
    )

    products = [p["product"] for p in product_data]
    sales = [p["total_sales"] for p in product_data]

    return JsonResponse({
        "products": products,
        "sales": sales
    })