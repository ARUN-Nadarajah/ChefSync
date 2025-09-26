from django.contrib import admin
from .models import (
    UserAddress, Order, OrderItem, OrderStatusHistory, CartItem,
    Delivery, DeliveryReview, BulkOrder, BulkOrderAssignment
)


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address_type', 'city', 'state', 'postal_code', 'is_default']
    list_filter = ['address_type', 'city', 'state', 'is_default']
    search_fields = ['user__username', 'user__email', 'street_address', 'city', 'state']
    list_editable = ['is_default']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer', 'status', 'total_amount', 'order_type', 'created_at', 'delivery_time']
    list_filter = ['status', 'order_type', 'payment_status', 'created_at', 'delivery_time']
    search_fields = ['order_id', 'customer__username', 'customer__email', 'delivery_address']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
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
    list_display = ['order', 'food_price', 'quantity', 'unit_price', 'total_price']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['order__order_id', 'food_price__food__name', 'order__customer__username']
    readonly_fields = ['total_price']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'food_price__food')


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'changed_at', 'notes']
    list_filter = ['status', 'changed_at']
    search_fields = ['order__order_id', 'notes']
    readonly_fields = ['changed_at']
    date_hierarchy = 'changed_at'
    ordering = ['-changed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'food_price', 'quantity', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'user__email', 'food_price__food__name']
    date_hierarchy = 'added_at'
    ordering = ['-added_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'food_price__food')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['order', 'delivery_agent', 'status', 'estimated_delivery_time', 'actual_delivery_time']
    list_filter = ['status', 'estimated_delivery_time', 'actual_delivery_time']
    search_fields = ['order__order_id', 'delivery_agent__username', 'pickup_location', 'delivery_location']
    readonly_fields = ['assigned_at', 'picked_up_at', 'delivered_at']
    date_hierarchy = 'estimated_delivery_time'
    
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
    list_display = ['bulk_order_id', 'organizer', 'event_name', 'total_quantity', 'status', 'event_date']
    list_filter = ['status', 'event_date', 'created_at']
    search_fields = ['bulk_order_id', 'organizer__username', 'event_name', 'event_location']
    readonly_fields = ['bulk_order_id', 'created_at', 'updated_at']
    date_hierarchy = 'event_date'
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
        return super().get_queryset(request).select_related('organizer')


@admin.register(BulkOrderAssignment)
class BulkOrderAssignmentAdmin(admin.ModelAdmin):
    list_display = ['bulk_order', 'chef', 'assigned_quantity', 'confirmed_quantity', 'status']
    list_filter = ['status', 'assigned_at']
    search_fields = ['bulk_order__bulk_order_id', 'chef__username', 'bulk_order__event_name']
    readonly_fields = ['assigned_at']
    date_hierarchy = 'assigned_at'
    
    actions = ['confirm_assignments', 'reject_assignments']
    
    def confirm_assignments(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} assignment(s) confirmed.')
    confirm_assignments.short_description = "Confirm selected assignments"
    
    def reject_assignments(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} assignment(s) rejected.')
    reject_assignments.short_description = "Reject selected assignments"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bulk_order', 'chef')
