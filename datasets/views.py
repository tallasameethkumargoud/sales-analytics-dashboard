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
from django.http import JsonResponse, HttpResponse
from django.conf import settings

from .decorators import get_user_role, role_required, api_role_required
from .models import Dataset, Record, Customer, Product, RecommendationInteraction


# ─── Auth ─────────────────────────────────────────────────────────────────────

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


# ─── Upload ───────────────────────────────────────────────────────────────────

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
                customer, _ = Customer.objects.get_or_create(name=row["customer_name"])
                product, _  = Product.objects.get_or_create(name=row["product"])
                Record.objects.create(
                    dataset=dataset,
                    customer=customer,
                    product=product,
                    customer_name=row["customer_name"],
                    product_name=row["product"],
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


# ─── Pages ────────────────────────────────────────────────────────────────────

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
        **get_role_context(request),
        "total_revenue": total_revenue,
        "avg_order": avg_order,
        "top_product": top_product["product__name"] if top_product else None,
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


# ─── Data APIs ────────────────────────────────────────────────────────────────

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
    forecast_dates, forecast_sales = [], []
    for i in range(1, 8):
        future_x = len(sales) - 1 + i
        predicted = max(0, round(m * future_x + b, 2))
        forecast_dates.append((last_date + timedelta(days=i)).strftime("%Y-%m-%d"))
        forecast_sales.append(predicted)
    avg_sales  = round(sum(sales) / len(sales), 2)
    trend_word = "upward 📈" if m > 0 else "downward 📉"
    change_pct = round(abs(m) / avg_sales * 100, 1) if avg_sales else 0
    if m > 50:       outlook = "strong growth"
    elif m > 0:      outlook = "moderate growth"
    elif m > -50:    outlook = "slight decline"
    else:            outlook = "significant decline"
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


# ─── AI APIs ──────────────────────────────────────────────────────────────────

def ai_chat_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)

    body = json.loads(request.body)
    question = body.get("question", "").strip()
    if not question:
        return JsonResponse({"error": "No question provided."}, status=400)

    records       = Record.objects.filter(dataset__uploaded_by=request.user)
    total_revenue = records.aggregate(Sum("amount"))["amount__sum"] or 0
    avg_order     = records.aggregate(Avg("amount"))["amount__avg"] or 0
    total_orders  = records.count()

    product_data = list(
        records.values("product__name")
        .annotate(total_sales=Sum("amount"), order_count=Count("id"), avg_sale=Avg("amount"))
        .order_by("-total_sales")
    )
    customer_data = list(
        records.values("customer__name")
        .annotate(total_spent=Sum("amount"), order_count=Count("id"), avg_spent=Avg("amount"))
        .order_by("-total_spent")
    )
    trend_data = list(
        records.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(daily_revenue=Sum("amount"))
        .order_by("date")
    )

    product_lines  = "\n".join([f"  {i+1}. {p['product__name']}: ${p['total_sales']:,.2f} | {p['order_count']} orders | ${p['avg_sale']:,.2f} avg" for i, p in enumerate(product_data)])
    customer_lines = "\n".join([f"  {i+1}. {c['customer__name']}: ${c['total_spent']:,.2f} | {c['order_count']} orders | ${c['avg_spent']:,.2f} avg" for i, c in enumerate(customer_data)])
    trend_lines    = "\n".join([f"  {t['date']}: ${t['daily_revenue']:,.2f}" for t in trend_data])

    system_prompt = f"""You are an elite AI data analyst with direct access to a live sales database.
Answer using ONLY the real data below. Be precise, use exact numbers.

OVERALL METRICS:
  • Total Revenue: ${total_revenue:,.2f} | Orders: {total_orders} | AOV: ${avg_order:,.2f}
  • Products: {len(product_data)} | Customers: {len(customer_data)}

ALL PRODUCTS (ranked by revenue):
{product_lines}

ALL CUSTOMERS (ranked by spending):
{customer_lines}

DAILY REVENUE TREND:
{trend_lines}

INSTRUCTIONS:
- Use exact numbers, format money with $ and commas
- Use bullet points for lists
- Keep answers concise but complete
- If asked something not in the data, say so clearly"""

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
        return JsonResponse({"answer": completion.choices[0].message.content.strip()})
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
        .annotate(total_spent=Sum("amount"), order_count=Count("id"), avg_spent=Avg("amount"))
        .order_by("-total_spent")
    )
    customer_lines = "\n".join([
        f"- {c['customer__name']}: ${c['total_spent']:,.2f} total, {c['order_count']} orders, ${c['avg_spent']:,.2f} avg"
        for c in customer_data
    ])
    prompt = f"""You are an expert customer analytics AI. Analyze these customers:

{customer_lines}

Provide:
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
        return JsonResponse({"analysis": completion.choices[0].message.content.strip(), "total_customers": len(customer_data)})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"AI error: {str(e)}"}, status=500)


def track_recommendation(request):
    """Track when user clicks/applies/dismisses a recommendation."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)

    body         = json.loads(request.body)
    product_name = body.get("product")
    action_type  = body.get("action_type")
    interaction  = body.get("interaction", "clicked")
    impact       = body.get("impact", "medium")

    try:
        product = Product.objects.get(name=product_name)
        RecommendationInteraction.objects.create(
            user=request.user,
            product=product,
            action_type=action_type,
            interaction=interaction,
            impact=impact
        )
        return JsonResponse({"status": "tracked"})
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def ai_recommendations_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated."}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)

    records = Record.objects.filter(dataset__uploaded_by=request.user)
    if not records.exists():
        return JsonResponse({"error": "No data available."}, status=400)

    total_revenue = records.aggregate(Sum("amount"))["amount__sum"] or 0
    avg_order     = records.aggregate(Avg("amount"))["amount__avg"] or 0

    product_data = list(
        records.values("product__name")
        .annotate(total_sales=Sum("amount"), order_count=Count("id"), avg_sale=Avg("amount"))
        .order_by("-total_sales")
    )
    for p in product_data:
        p["revenue_share"] = round((p["total_sales"] / total_revenue) * 100, 1) if total_revenue else 0
        p["vs_avg"] = round(((p["avg_sale"] - avg_order) / avg_order) * 100, 1) if avg_order else 0

    # ── User interaction history ──────────────────────────────────
    interactions = RecommendationInteraction.objects.filter(
        user=request.user
    ).order_by("-created_at")
    interactions_list = list(interactions[:50])
    interactions = interactions.filter(pk__in=[i.pk for i in interactions_list])



    if interactions.exists():
        top_actions = list(
            interactions.filter(interaction="applied")
            .values("action_type").annotate(cnt=Count("id")).order_by("-cnt")[:3]
        )
        dismissed_actions = list(
            interactions.filter(interaction="dismissed")
            .values("action_type").annotate(cnt=Count("id")).order_by("-cnt")[:3]
        )
        top_products = list(
            interactions.filter(interaction__in=["clicked", "applied"])
            .values("product__name").annotate(cnt=Count("id")).order_by("-cnt")[:3]
        )
        top_action_names    = [a["action_type"] for a in top_actions]
        dismissed_names     = [a["action_type"] for a in dismissed_actions]
        top_product_names   = [p["product__name"] for p in top_products]

        interaction_summary = f"""
USER BEHAVIOR HISTORY (last {interactions.count()} interactions):
- Clicks: {interactions.filter(interaction="clicked").count()}
- Applied: {interactions.filter(interaction="applied").count()}
- Dismissed: {interactions.filter(interaction="dismissed").count()}
- Preferred actions: {', '.join(top_action_names) or 'none yet'}
- Ignored actions: {', '.join(dismissed_names) or 'none yet'}
- Focus products: {', '.join(top_product_names) or 'none yet'}

PERSONALIZATION: Prioritize {', '.join(top_action_names) or 'all equally'}. Avoid {', '.join(dismissed_names) or 'nothing'}."""
    else:
        interaction_summary = "USER BEHAVIOR: No interactions yet — give balanced recommendations."

    product_lines = "\n".join([
        f"- {p['product__name']}: ${p['total_sales']:,.2f} | {p['order_count']} orders | "
        f"${p['avg_sale']:,.2f} avg | {p['revenue_share']}% revenue | "
        f"{'+' if p['vs_avg'] >= 0 else ''}{p['vs_avg']}% vs avg"
        for p in product_data
    ])

    prompt = f"""You are an elite personalized e-commerce AI like Amazon's recommendation engine.

STORE: Revenue ${total_revenue:,.2f} | AOV ${avg_order:,.2f} | {len(product_data)} products

PRODUCTS:
{product_lines}

{interaction_summary}

Return ONLY this JSON for EACH product:
{{
  "recommendations": [
    {{
      "product": "Name",
      "revenue": 0.0,
      "revenue_share": 0.0,
      "order_count": 0,
      "avg_sale": 0.0,
      "status": "star|growth|underperform|risk",
      "badge": "⭐ Top Performer|📈 Growth|⚠️ Needs Attention|🚨 At Risk",
      "personalized": true,
      "actions": [
        {{
          "type": "increase_price|promote|upsell|discount|discontinue|bundle",
          "icon": "💰|📣|🔝|🏷️|❌|📦",
          "title": "Action title",
          "reason": "Why, personalized to user behavior",
          "impact": "high|medium|low"
        }}
      ],
      "summary": "One sentence assessment"
    }}
  ]
}}

Rules: star=top 30% revenue, growth=above avg orders, underperform=below avg share, risk=lowest revenue+orders.
Prioritize user's preferred actions. Avoid dismissed actions. 2-3 actions per product. JSON only."""

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an elite personalized e-commerce AI. Respond with valid JSON only."},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.2
        )
        raw = completion.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        import json as json_lib
        data = json_lib.loads(raw)
        data["interaction_stats"] = {
            "total": interactions.count(),
            "personalized": interactions.exists()
        }
        return JsonResponse(data)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"AI error: {str(e)}"}, status=500)
    

# ─── Role-based access helpers ────────────────────────────────────────────────

def get_role_context(request):
    """Add role info to every template context."""
    role = get_user_role(request.user)
    return {
        "user": request.user,
        "user_role": role,
        "is_admin":   role == "admin",
        "is_analyst": role == "analyst",
        "is_viewer":  role == "viewer",
    }


# ─── Admin Panel ──────────────────────────────────────────────────────────────

@role_required('admin')
def admin_panel(request):
    """Admin-only user management panel."""
    users = User.objects.all().order_by("date_joined")
    user_list = []
    for u in users:
        role = get_user_role(u)
        record_count = Record.objects.filter(dataset__uploaded_by=u).count()
        dataset_count = Dataset.objects.filter(uploaded_by=u).count()
        user_list.append({
            "id":            u.id,
            "username":      u.username,
            "email":         u.email,
            "role":          role,
            "record_count":  record_count,
            "dataset_count": dataset_count,
            "date_joined":   u.date_joined,
            "last_login":    u.last_login,
        })
    return render(request, "admin_panel.html", {
        **get_role_context(request),
        "user_list": user_list,
        "total_users":    users.count(),
        "total_records":  Record.objects.count(),
        "total_datasets": Dataset.objects.count(),
    })


@api_role_required('admin')
def update_user_role(request):
    """Admin API: change a user's role."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)
    body     = json.loads(request.body)
    user_id  = body.get("user_id")
    new_role = body.get("role")
    if new_role not in ["admin", "analyst", "viewer"]:
        return JsonResponse({"error": "Invalid role."}, status=400)
    try:
        target_user = User.objects.get(id=user_id)
        if target_user == request.user:
            return JsonResponse({"error": "You cannot change your own role."}, status=400)
        profile, _ = UserProfile.objects.get_or_create(user=target_user)
        profile.role = new_role
        profile.save()
        return JsonResponse({"status": "updated", "username": target_user.username, "role": new_role})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)


@api_role_required('admin')
def delete_user_api(request):
    """Admin API: delete a user."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required."}, status=405)
    body    = json.loads(request.body)
    user_id = body.get("user_id")
    try:
        target_user = User.objects.get(id=user_id)
        if target_user == request.user:
            return JsonResponse({"error": "You cannot delete yourself."}, status=400)
        target_user.delete()
        return JsonResponse({"status": "deleted"})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=404)