from django.contrib import admin
from .models import (
    Contact, Notification, Communication,
    CommunicationResponse,
    CommunicationAttachment,
    CommunicationTemplate,
    CommunicationCategory,
    CommunicationTag,
    CommunicationCategoryRelation,
    CommunicationTagRelation
)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('contact_id', 'name', 'email', 'user', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('name', 'email', 'message', 'user__username', 'user__email')
    readonly_fields = ('contact_id', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_id', 'subject', 'user', 'status', 'time')
    list_filter = ('status', 'time')
    search_fields = ('subject', 'message', 'user__username', 'user__email')
    readonly_fields = ('notification_id', 'time')
    list_editable = ('status',)
    date_hierarchy = 'time'
    ordering = ['-time']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(status='Read')
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(status='Unread')
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'subject', 'user', 'communication_type', 'status', 'priority', 'created_at')
    list_filter = ('communication_type', 'status', 'priority', 'is_read', 'is_archived')
    search_fields = ('reference_number', 'subject', 'user__email', 'user__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('reference_number', 'created_at', 'updated_at', 'read_at', 'resolved_at')

@admin.register(CommunicationResponse)
class CommunicationResponseAdmin(admin.ModelAdmin):
    list_display = ('communication', 'responder', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('communication__reference_number', 'responder__email', 'message')
    date_hierarchy = 'created_at'

@admin.register(CommunicationAttachment)
class CommunicationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'communication', 'file_type', 'file_size', 'uploaded_by', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('filename', 'communication__reference_number', 'uploaded_by__email')
    date_hierarchy = 'created_at'

@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active', 'created_by', 'updated_at')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'subject', 'content')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CommunicationCategory)
class CommunicationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CommunicationTag)
class CommunicationTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

@admin.register(CommunicationCategoryRelation)
class CommunicationCategoryRelationAdmin(admin.ModelAdmin):
    list_display = ('communication', 'category', 'added_by', 'added_at')
    list_filter = ('category', 'added_at')
    search_fields = ('communication__reference_number', 'category__name', 'added_by__email')
    date_hierarchy = 'added_at'

@admin.register(CommunicationTagRelation)
class CommunicationTagRelationAdmin(admin.ModelAdmin):
    list_display = ('communication', 'tag', 'added_by', 'added_at')
    list_filter = ('tag', 'added_at')
    search_fields = ('communication__reference_number', 'tag__name', 'added_by__email')
    date_hierarchy = 'added_at'