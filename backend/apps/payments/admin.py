from django.contrib import admin
from .models import Payment, Refund, PaymentMethod, Transaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'order', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['payment_id', 'order__order_id', 'order__customer__username', 'transaction_id']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'processed_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    actions = ['mark_completed', 'mark_failed', 'mark_refunded']
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} payment(s) marked as completed.')
    mark_completed.short_description = "Mark selected payments as completed"
    
    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payment(s) marked as failed.')
    mark_failed.short_description = "Mark selected payments as failed"
    
    def mark_refunded(self, request, queryset):
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} payment(s) marked as refunded.')
    mark_refunded.short_description = "Mark selected payments as refunded"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['refund_id', 'payment', 'amount', 'status', 'reason', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['refund_id', 'payment__payment_id', 'payment__order__order_number', 'reason']
    readonly_fields = ['refund_id', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    actions = ['approve_refunds', 'reject_refunds', 'process_refunds']
    
    def approve_refunds(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} refund(s) approved.')
    approve_refunds.short_description = "Approve selected refunds"
    
    def reject_refunds(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} refund(s) rejected.')
    reject_refunds.short_description = "Reject selected refunds"
    
    def process_refunds(self, request, queryset):
        updated = queryset.update(status='processed')
        self.message_user(request, f'{updated} refund(s) processed.')
    process_refunds.short_description = "Process selected refunds"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment__order')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'method_type', 'card_brand', 'card_last_four', 'is_default', 'is_active', 'created_at']
    list_filter = ['method_type', 'card_brand', 'is_default', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'card_last_four', 'card_brand']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-is_default', '-created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'payment', 'transaction_type', 'amount', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['transaction_id', 'payment__payment_id', 'payment__order__order_number', 'description']
    readonly_fields = ['transaction_id', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    actions = ['mark_completed', 'mark_failed']
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} transaction(s) marked as completed.')
    mark_completed.short_description = "Mark selected transactions as completed"
    
    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} transaction(s) marked as failed.')
    mark_failed.short_description = "Mark selected transactions as failed"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment')
