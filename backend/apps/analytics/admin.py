from django.contrib import admin
from .models import SystemSettings, UserRole, SystemMaintenance, SystemNotification


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'setting_type', 'is_active', 'updated_at']
    list_filter = ['setting_type', 'is_active', 'updated_at']
    search_fields = ['key', 'value', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['setting_type', 'key']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'role_type', 'is_active', 'created_at']
    list_filter = ['role_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


@admin.register(SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['title', 'maintenance_type', 'status', 'scheduled_start', 'scheduled_end', 'actual_start']
    list_filter = ['maintenance_type', 'status', 'scheduled_start', 'scheduled_end']
    search_fields = ['title', 'description']
    readonly_fields = ['actual_start', 'actual_end', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_start'
    ordering = ['-scheduled_start']
    
    actions = ['mark_in_progress', 'mark_completed', 'mark_cancelled']
    
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} maintenance(s) marked as in progress.')
    mark_in_progress.short_description = "Mark selected maintenance as in progress"
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} maintenance(s) marked as completed.')
    mark_completed.short_description = "Mark selected maintenance as completed"
    
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} maintenance(s) cancelled.')
    mark_cancelled.short_description = "Cancel selected maintenance"


@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'priority', 'is_active', 'start_date', 'end_date']
    list_filter = ['notification_type', 'priority', 'is_active', 'start_date', 'end_date']
    search_fields = ['title', 'message']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    ordering = ['-created_at']
    
    actions = ['activate_notifications', 'deactivate_notifications']
    
    def activate_notifications(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} notification(s) activated.')
    activate_notifications.short_description = "Activate selected notifications"
    
    def deactivate_notifications(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} notification(s) deactivated.')
    deactivate_notifications.short_description = "Deactivate selected notifications"
