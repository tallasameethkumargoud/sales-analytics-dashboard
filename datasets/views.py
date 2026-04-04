import pandas as pd
import traceback
import numpy as np
from datetime import timedelta
import json
import urllib.request
import csv


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.conf import settings
from django.http import HttpResponse


from .models import Dataset, Record, Customer, Product


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
                # Get or create Customer
                customer, _ = Customer.objects.get_or_create(
                    name=row["customer_name"]
                )
                # Get or create Product
                product, _ = Product.objects.get_or_create(
                    name=row["product"]
                )
                # Create Record linked to both
                Record.objects.create(
                    dataset=dataset,
                    customer=customer,
                    product=product,
                    customer_name=row["customer_name"],  # keep for compatibility
                    product_name=row["product"],          # keep for compatibility
                    amount=row["amount"],
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
        records.values("product__name")
        .annotate(total_sales=Sum("amount"))
        .order_by("-total_sales")
        .first()
    )

    return render(request, "analytics.html", {
        "total_revenue": total_revenue,
        "avg_order": avg_order,
        "top_product": top_product["product__name"] if top_product else None,
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
        "top_product": top_product["product__name"] if top_product else None
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
        queryset.values("product__name")
        .annotate(total_sales=Sum("amount"))
        .order_by("-total_sales")
    )
    return JsonResponse({
        "products": [p["product__name"] for p in product_data],
        "sales":    [p["total_sales"]   for p in product_data]
    })


def sales_forecast_api(request):
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
    if len(trend_data) < 2:
        return JsonResponse({
            "forecast_dates": [],
            "forecast_sales": [],
            "explanation": "Not enough data to forecast. Upload more datasets over multiple days."
        })
    dates = [entry["date"] for entry in trend_data]
    sales = [float(entry["total_sales"]) for entry in trend_data]
    x = np.array(range(len(sales)), dtype=float)
    y = np.array(sales)
    m, b = np.polyfit(x, y, 1)
    last_date = dates[-1]
    forecast_dates = []
    forecast_sales = []
    for i in range(1, 8):
        future_x = len(sales) - 1 + i
        predicted = round(m * future_x + b, 2)
        predicted = max(0, predicted)
        forecast_dates.append((last_date + timedelta(days=i)).strftime("%Y-%m-%d"))
        forecast_sales.append(predicted)
    avg_sales = round(sum(sales) / len(sales), 2)
    trend_word = "upward 📈" if m > 0 else "downward 📉"
    change_pct = round(abs(m) / avg_sales * 100, 1) if avg_sales else 0
    if m > 50:
        outlook = "strong growth"
    elif m > 0:
        outlook = "moderate growth"
    elif m > -50:
        outlook = "slight decline"
    else:
        outlook = "significant decline"
    explanation = (
        f"Based on your last {len(sales)} days of data, your sales show a {trend_word} trend. "
        f"Revenue is changing by approximately ${abs(round(m, 2))} per day ({change_pct}% of your average). "
        f"The model forecasts {outlook} over the next 7 days, "
        f"with predicted revenue ranging from ${min(forecast_sales):,.0f} to ${max(forecast_sales):,.0f}."
    )
    return JsonResponse({
        "forecast_dates": forecast_dates,
        "forecast_sales": forecast_sales,
        "explanation": explanation,
        "trend_slope": round(m, 2),
        "avg_sales": avg_sales
    })


def ai_chat_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)

    body = json.loads(request.body)
    question = body.get("question", "").strip()
    if not question:
        return JsonResponse({"error": "No question provided."}, status=400)

    # ── Step 1: Fetch all relevant data from DB ───────────────────
    records = Record.objects.filter(dataset__uploaded_by=request.user)

    # Total metrics
    total_revenue = records.aggregate(Sum("amount"))["amount__sum"] or 0
    avg_order     = records.aggregate(Avg("amount"))["amount__avg"] or 0
    total_orders  = records.count()

    # All products with full stats
    product_data = list(
        records.values("product__name")
        .annotate(
            total_sales=Sum("amount"),
            order_count=Count("id"),
            avg_sale=Avg("amount")
        )
        .order_by("-total_sales")
    )

    # All customers with full stats
    customer_data = list(
        records.values("customer__name")
        .annotate(
            total_spent=Sum("amount"),
            order_count=Count("id"),
            avg_spent=Avg("amount")
        )
        .order_by("-total_spent")
    )

    # Daily revenue trend
    from django.db.models.functions import TruncDate
    trend_data = list(
        records.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(daily_revenue=Sum("amount"))
        .order_by("date")
    )

    # ── Step 2: Build rich data context for AI ────────────────────
    product_lines = "\n".join([
        f"  {i+1}. {p['product__name']}: ${p['total_sales']:,.2f} total | "
        f"{p['order_count']} orders | ${p['avg_sale']:,.2f} avg"
        for i, p in enumerate(product_data)
    ])

    customer_lines = "\n".join([
        f"  {i+1}. {c['customer__name']}: ${c['total_spent']:,.2f} total | "
        f"{c['order_count']} orders | ${c['avg_spent']:,.2f} avg"
        for i, c in enumerate(customer_data)
    ])

    trend_lines = "\n".join([
        f"  {t['date']}: ${t['daily_revenue']:,.2f}"
        for t in trend_data
    ])

    top_3_products = product_lines.split("\n")[:3]
    bottom_3_products = product_lines.split("\n")[-3:]
    top_3_customers = customer_lines.split("\n")[:3]

    # ── Step 3: Smart system prompt ───────────────────────────────
    system_prompt = f"""You are an elite AI data analyst with direct access to a live sales database.
You must answer using ONLY the real data provided below. Be precise, use exact numbers.

═══════════════════════════════════════
📊 LIVE DATABASE SNAPSHOT
═══════════════════════════════════════

OVERALL METRICS:
  • Total Revenue:     ${total_revenue:,.2f}
  • Total Orders:      {total_orders}
  • Avg Order Value:   ${avg_order:,.2f}
  • Total Products:    {len(product_data)}
  • Total Customers:   {len(customer_data)}

ALL PRODUCTS (ranked by revenue):
{product_lines}

ALL CUSTOMERS (ranked by spending):
{customer_lines}

DAILY REVENUE TREND:
{trend_lines}

TOP 3 PRODUCTS:
{chr(10).join(top_3_products)}

BOTTOM 3 PRODUCTS:
{chr(10).join(bottom_3_products)}

TOP 3 CUSTOMERS:
{chr(10).join(top_3_customers)}

═══════════════════════════════════════
INSTRUCTIONS:
- Answer questions using exact numbers from the data above
- For "top N products" → list exactly N products with revenue
- For "bottom N products" → list exactly N products with revenue
- For "best customer" → give name + total spent
- For "revenue trend" → describe the daily pattern
- For "compare products" → show side by side stats
- For "summary" → give executive summary with all key metrics
- Always format money with $ and commas
- Be concise but complete — use bullet points for lists
- If asked something not in the data, say "I don't have that data"
═══════════════════════════════════════"""

    # ── Step 4: Call Groq AI ──────────────────────────────────────
    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": question}
            ],
            max_tokens=500,
            temperature=0.3
        )
        answer = completion.choices[0].message.content.strip()
        return JsonResponse({"answer": answer})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"AI error: {str(e)}"}, status=500)
    
def ai_sentiment_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)

    records = Record.objects.filter(dataset__uploaded_by=request.user)

    if not records.exists():
        return JsonResponse({"error": "No data available."}, status=400)

    customer_data = list(
        records.values("customer__name")
        .annotate(
            total_spent=Sum("amount"),
            order_count=Count("id"),
            avg_spent=Avg("amount")
        )
        .order_by("-total_spent")
    )

    customer_lines = "\n".join([
        f"- {c['customer__name']}: ${c['total_spent']:,.2f} total, "
        f"{c['order_count']} orders, ${c['avg_spent']:,.2f} avg"
        for c in customer_data
    ])

    prompt = f"""You are an expert customer analytics AI. Analyze these customers:

{customer_lines}

Provide a structured analysis with:
1. 🌍 Customer name origin patterns
2. 💰 Spending tier breakdown (high/mid/low spenders)
3. 🏆 VIP customers (top 20% by spending)
4. 📊 Customer diversity score (1-10) with reasoning
5. 💡 3 actionable business recommendations

Use exact numbers and be data-driven."""

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert customer analytics AI."},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=600,
            temperature=0.3
        )
        analysis = completion.choices[0].message.content.strip()
        return JsonResponse({"analysis": analysis, "total_customers": len(customer_data)})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"AI error: {str(e)}"}, status=500)
    
def export_csv(request):
    if not request.user.is_authenticated:
        return redirect("/login/")

    records = Record.objects.filter(
        dataset__uploaded_by=request.user
    ).values("customer_name", "product", "amount", "created_at")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Customer Name", "Product", "Amount", "Date"])

    for r in records:
        writer.writerow([
            r["customer_name"],
            r["product"],
            f"${r['amount']:,.2f}",
            r["created_at"].strftime("%Y-%m-%d %H:%M")
        ])

    return response

def ai_recommendations_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)

    records = Record.objects.filter(dataset__uploaded_by=request.user)
    if not records.exists():
        return JsonResponse({"error": "No data available."}, status=400)

    # ── Build product stats ───────────────────────────────────────
    total_revenue = records.aggregate(Sum("amount"))["amount__sum"] or 0
    avg_order     = records.aggregate(Avg("amount"))["amount__avg"] or 0

    product_data = list(
        records.values("product__name")
        .annotate(
            total_sales=Sum("amount"),
            order_count=Count("id"),
            avg_sale=Avg("amount")
        )
        .order_by("-total_sales")
    )

    # ── Compute metrics per product ───────────────────────────────
    for p in product_data:
        p["revenue_share"] = round((p["total_sales"] / total_revenue) * 100, 1) if total_revenue else 0
        p["vs_avg"] = round(((p["avg_sale"] - avg_order) / avg_order) * 100, 1) if avg_order else 0

    product_lines = "\n".join([
        f"- {p['product__name']}: "
        f"${p['total_sales']:,.2f} total | "
        f"{p['order_count']} orders | "
        f"${p['avg_sale']:,.2f} avg | "
        f"{p['revenue_share']}% of revenue | "
        f"{'+' if p['vs_avg'] >= 0 else ''}{p['vs_avg']}% vs store avg"
        for p in product_data
    ])

    prompt = f"""You are an elite e-commerce strategy AI. Analyze these products and give actionable recommendations.

STORE METRICS:
- Total Revenue: ${total_revenue:,.2f}
- Average Order Value: ${avg_order:,.2f}
- Total Products: {len(product_data)}

PRODUCT PERFORMANCE:
{product_lines}

For EACH product, provide exactly this JSON format:
{{
  "recommendations": [
    {{
      "product": "Product Name",
      "revenue": 1234.56,
      "revenue_share": 12.3,
      "order_count": 5,
      "avg_sale": 246.91,
      "status": "star|growth|underperform|risk",
      "badge": "⭐ Top Performer|📈 Growth|⚠️ Needs Attention|🚨 At Risk",
      "actions": [
        {{
          "type": "increase_price|promote|upsell|discount|discontinue|bundle",
          "icon": "💰|📣|🔝|🏷️|❌|📦",
          "title": "Short action title",
          "reason": "One sentence why",
          "impact": "high|medium|low"
        }}
      ],
      "summary": "One sentence overall assessment"
    }}
  ]
}}

Rules:
- Star products (top 30% revenue): recommend increase_price + upsell
- Growth products (above avg orders): recommend promote + bundle  
- Underperform (below avg revenue share): recommend discount + promote
- Risk products (lowest revenue + low orders): recommend discontinue or bundle
- Give 2-3 actions per product
- Return ONLY valid JSON, no extra text"""

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an elite e-commerce strategy AI. Always respond with valid JSON only."},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2
        )
        raw = completion.choices[0].message.content.strip()

        # Clean up JSON if needed
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        import json as json_lib
        data = json_lib.loads(raw)
        return JsonResponse(data)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"AI error: {str(e)}"}, status=500)