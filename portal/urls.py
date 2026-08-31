from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.PortalLoginView.as_view(), name="login"),
    path("logout/", views.PortalLogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("requests/", views.request_list, name="requests"),
    path("requests/export/", views.export_requests, name="export_requests"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/received/", views.mark_received, name="mark_received"),
    path("requests/<int:pk>/issue/", views.report_issue, name="report_issue"),
    path("schedule/", views.schedule, name="schedule"),
    path("schedule/assign/", views.assign_shipment, name="assign_shipment"),
    path("setup/departments/", views.department_list, name="departments"),
    path("setup/departments/export/", views.export_departments, name="export_departments"),
    path("setup/departments/<int:pk>/edit/", views.department_edit, name="department_edit"),
    path("setup/departments/<int:pk>/delete/", views.department_delete, name="department_delete"),
    path("setup/warehouses/", views.warehouse_list, name="warehouses"),
    path("setup/warehouses/export/", views.export_warehouses, name="export_warehouses"),
    path("setup/warehouses/<int:pk>/edit/", views.warehouse_edit, name="warehouse_edit"),
    path("setup/warehouses/<int:pk>/delete/", views.warehouse_delete, name="warehouse_delete"),
    path("suppliers/", views.supplier_list, name="suppliers"),
    path("suppliers/export/", views.export_suppliers, name="export_suppliers"),
    path("suppliers/<int:pk>/edit/", views.supplier_edit, name="supplier_edit"),
    path("suppliers/<int:pk>/delete/", views.supplier_delete, name="supplier_delete"),
    path("setup/whatsapp/", views.whatsapp_setup, name="whatsapp_setup"),
    path("users/", views.user_list, name="users"),
    path("users/export/", views.export_users, name="export_users"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("settings/", views.settings_view, name="settings"),
]
