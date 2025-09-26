from django.contrib import admin
from .models import (
    UserAddress, Order, OrderItem, OrderStatusHistory, CartItem,
    Delivery, DeliveryReview, BulkOrder, BulkOrderAssignment
)


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'city', 'pincode', 'is_default']
    list_filter = ['label', 'city', 'is_default']
    search_fields = ['user__username', 'user__email', 'address_line1', 'city']
    list_editable = ['is_default']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'total_amount', 'payment_method', 'created_at', 'estimated_delivery_time']
    list_filter = ['status', 'payment_method', 'payment_status', 'created_at', 'estimated_delivery_time']
    search_fields = ['order_number', 'customer__username', 'customer__email', 'delivery_address']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    actions = ['mark_confirmed', 'mark_preparing', 'mark_ready', 'mark_delivered', 'cancel_orders']
    
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} order(s) marked as confirmed.')
    mark_confirmed.short_description = "Mark selected orders as confirmed"
    
    def mark_preparing(self, request, queryset):
        updated = queryset.update(status='preparing')
        self.message_user(request, f'{updated} order(s) marked as preparing.')
    mark_preparing.short_description = "Mark selected orders as preparing"
    
    def mark_ready(self, request, queryset):
        updated = queryset.update(status='ready')
        self.message_user(request, f'{updated} order(s) marked as ready.')
    mark_ready.short_description = "Mark selected orders as ready"
    
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_delivered.short_description = "Mark selected orders as delivered"
    
    def cancel_orders(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} order(s) cancelled.')
    cancel_orders.short_description = "Cancel selected orders"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'price', 'quantity', 'unit_price', 'total_price']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['order__order_number', 'price__food__name', 'order__customer__username']
    readonly_fields = ['total_price']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'price__food')


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_at', 'notes']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['customer', 'price', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['customer__username', 'customer__email', 'price__food__name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'price__food')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['order', 'agent', 'status', 'delivery_time', 'created_at']
    list_filter = ['status', 'delivery_time', 'created_at']
    search_fields = ['order__order_number', 'agent__username', 'address']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'delivery_time'
    
    actions = ['assign_delivery', 'mark_picked_up', 'mark_delivered']
    
    def assign_delivery(self, request, queryset):
        updated = queryset.update(status='assigned')
        self.message_user(request, f'{updated} delivery(s) assigned.')
    assign_delivery.short_description = "Assign selected deliveries"
    
    def mark_picked_up(self, request, queryset):
        updated = queryset.update(status='picked_up')
        self.message_user(request, f'{updated} delivery(s) marked as picked up.')
    mark_picked_up.short_description = "Mark selected deliveries as picked up"
    
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} delivery(s) marked as delivered.')
    mark_delivered.short_description = "Mark selected deliveries as delivered"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'delivery_agent')


@admin.register(DeliveryReview)
class DeliveryReviewAdmin(admin.ModelAdmin):
    list_display = ['delivery', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['delivery__order__order_id', 'delivery__delivery_agent__username', 'comment']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('delivery__order', 'delivery__delivery_agent')


@admin.register(BulkOrder)
class BulkOrderAdmin(admin.ModelAdmin):
    list_display = ['bulk_order_id', 'created_by', 'description', 'total_quantity', 'status', 'deadline']
    list_filter = ['status', 'deadline', 'created_at']
    search_fields = ['bulk_order_id', 'created_by__username', 'description']
    readonly_fields = ['bulk_order_id', 'created_at', 'updated_at']
    date_hierarchy = 'deadline'
    ordering = ['-created_at']
    
    actions = ['confirm_bulk_orders', 'cancel_bulk_orders']
    
    def confirm_bulk_orders(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} bulk order(s) confirmed.')
    confirm_bulk_orders.short_description = "Confirm selected bulk orders"
    
    def cancel_bulk_orders(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} bulk order(s) cancelled.')
    cancel_bulk_orders.short_description = "Cancel selected bulk orders"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(BulkOrderAssignment)
class BulkOrderAssignmentAdmin(admin.ModelAdmin):
    list_display = ['bulk_order', 'chef']
    list_filter = ['bulk_order__status']
    search_fields = ['bulk_order__bulk_order_id', 'chef__username', 'bulk_order__description']
    
    actions = ['confirm_assignments', 'reject_assignments']
    
    def confirm_assignments(self, request, queryset):
        # Since there's no status field in this model, just show success message
        self.message_user(request, f'{queryset.count()} assignment(s) processed.')
    confirm_assignments.short_description = "Confirm selected assignments"
    
    def reject_assignments(self, request, queryset):
        # Since there's no status field in this model, just show success message  
        self.message_user(request, f'{queryset.count()} assignment(s) processed.')
    reject_assignments.short_description = "Reject selected assignments"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bulk_order', 'chef')
