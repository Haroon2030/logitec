from django.contrib import admin

from .models import (
    Alert,
    DailyVolume,
    Department,
    InventoryItem,
    Product,
    RequestFile,
    RequestItem,
    Shipment,
    Supplier,
    SupplyRequest,
    UserProfile,
    Warehouse,
)


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 0


class RequestFileInline(admin.TabularInline):
    model = RequestFile
    extra = 0


@admin.register(SupplyRequest)
class SupplyRequestAdmin(admin.ModelAdmin):
    list_display = ("number", "supplier", "warehouse", "priority", "status", "created_at")
    list_filter = ("status", "priority", "supplier", "warehouse")
    search_fields = ("number",)
    inlines = [RequestFileInline, RequestItemInline]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "contact_name", "email")
    search_fields = ("name", "code")


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "capacity_percent")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "unit_price")
    search_fields = ("name", "sku")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "warehouse", "scheduled_hour", "status")
    list_filter = ("status", "warehouse")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "created_at")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "quantity", "min_quantity")


@admin.register(DailyVolume)
class DailyVolumeAdmin(admin.ModelAdmin):
    list_display = ("weekday", "volume", "highlight")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "branch", "phone")
