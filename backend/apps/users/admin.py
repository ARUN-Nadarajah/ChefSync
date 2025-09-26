from django.contrib import admin
from .models import UserProfile, ChefProfile, DeliveryProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'gender', 'date_of_birth', 'address']
    list_filter = ['gender', 'date_of_birth']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'address']
    readonly_fields = ['user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ChefProfile)
class ChefProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'approval_status', 'experience_years', 'rating_average', 'total_orders', 'is_featured']
    list_filter = ['approval_status', 'experience_years', 'is_featured', 'rating_average']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'bio']
    readonly_fields = ['user', 'rating_average', 'total_orders', 'total_reviews']
    list_editable = ['approval_status', 'is_featured']
    
    actions = ['approve_chefs', 'reject_chefs', 'suspend_chefs']
    
    def approve_chefs(self, request, queryset):
        updated = queryset.update(approval_status='approved')
        self.message_user(request, f'{updated} chef(s) approved successfully.')
    approve_chefs.short_description = "Approve selected chefs"
    
    def reject_chefs(self, request, queryset):
        updated = queryset.update(approval_status='rejected')
        self.message_user(request, f'{updated} chef(s) rejected.')
    reject_chefs.short_description = "Reject selected chefs"
    
    def suspend_chefs(self, request, queryset):
        updated = queryset.update(approval_status='suspended')
        self.message_user(request, f'{updated} chef(s) suspended.')
    suspend_chefs.short_description = "Suspend selected chefs"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(DeliveryProfile)
class DeliveryProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'approval_status', 'vehicle_type', 'is_available', 'rating_average', 'total_deliveries']
    list_filter = ['approval_status', 'vehicle_type', 'is_available', 'rating_average']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'license_number']
    readonly_fields = ['user', 'rating_average', 'total_deliveries']
    list_editable = ['approval_status', 'is_available']
    
    actions = ['approve_delivery_partners', 'reject_delivery_partners', 'suspend_delivery_partners']
    
    def approve_delivery_partners(self, request, queryset):
        updated = queryset.update(approval_status='approved')
        self.message_user(request, f'{updated} delivery partner(s) approved successfully.')
    approve_delivery_partners.short_description = "Approve selected delivery partners"
    
    def reject_delivery_partners(self, request, queryset):
        updated = queryset.update(approval_status='rejected')
        self.message_user(request, f'{updated} delivery partner(s) rejected.')
    reject_delivery_partners.short_description = "Reject selected delivery partners"
    
    def suspend_delivery_partners(self, request, queryset):
        updated = queryset.update(approval_status='suspended')
        self.message_user(request, f'{updated} delivery partner(s) suspended.')
    suspend_delivery_partners.short_description = "Suspend selected delivery partners"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
