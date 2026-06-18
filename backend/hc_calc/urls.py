"""hc_calc API 라우팅 (전역 IsAuthenticated 보호)."""

from django.urls import path

from . import views

urlpatterns = [
    path("calculate_costs/", views.calculate_costs_view, name="calculate_costs"),
    path("amazon-categories/", views.get_amazon_categories, name="amazon_categories"),
    path(
        "walmart-categories/", views.get_walmart_categories, name="walmart_categories"
    ),
    path(
        "calculation-logs/",
        views.CalculationLogListView.as_view(),
        name="calculation_logs",
    ),
    path(
        "calculation-logs/<int:pk>/",
        views.CalculationLogDetailView.as_view(),
        name="calculation_log_detail",
    ),
]
