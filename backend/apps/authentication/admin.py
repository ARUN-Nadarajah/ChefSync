from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.utils.safestring import mark_safe
from .models import User, Admin, Customer, Cook, DeliveryAgent, EmailOTP, JWTToken
from django.apps import apps

# Get models from Django's app registry to avoid import issues
DocumentType = apps.get_model('authentication', 'DocumentType')
UserDocument = apps.get_model('authentication', 'UserDocument')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin configuration for User model
    """
    list_display = ('user_id', 'name', 'email', 'phone_no', 'role', 'address', 'created_at', 'is_active', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active', 'created_at', 'groups')
    search_fields = ('name', 'email', 'phone_no', 'address')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'phone_no', 'address', 'role', 'profile_image')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'address', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('user_id', 'created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Admin configuration for Customer model
    """
    list_display = ('user_id', 'user_name', 'user_email', 'user_phone')
    search_fields = ('user__name', 'user__email', 'user__phone_no')
    ordering = ('user_id',)
    
    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = 'Name'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_phone(self, obj):
        return obj.user.phone_no
    user_phone.short_description = 'Phone'


@admin.register(Cook)
class CookAdmin(admin.ModelAdmin):
    """
    Admin configuration for Cook model
    """
    list_display = ('user_id', 'user_name', 'specialty', 'kitchen_location', 'experience_years', 'rating_avg', 'availability_hours')
    list_filter = ('specialty', 'experience_years', 'rating_avg')
    search_fields = ('user__name', 'specialty', 'kitchen_location')
    ordering = ('user_id',)
    
    fieldsets = (
        ('User Info', {'fields': ('user',)}),
        ('Cook Details', {'fields': ('specialty', 'kitchen_location', 'experience_years', 'rating_avg', 'availability_hours')}),
    )
    
    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = 'Name'


@admin.register(DeliveryAgent)
class DeliveryAgentAdmin(admin.ModelAdmin):
    """
    Admin configuration for DeliveryAgent model
    """
    list_display = ('user_id', 'user_name', 'vehicle_type', 'vehicle_number', 'current_location', 'is_available')
    list_filter = ('vehicle_type', 'is_available')
    search_fields = ('user__name', 'vehicle_number', 'current_location')
    ordering = ('user_id',)
    
    fieldsets = (
        ('User Info', {'fields': ('user',)}),
        ('Delivery Details', {'fields': ('vehicle_type', 'vehicle_number', 'current_location', 'is_available')}),
    )
    
    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = 'Name'


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """
    Admin configuration for DocumentType model
    """
    list_display = ('name', 'category', 'is_required', 'max_file_size_mb', 'allowed_file_types')
    list_filter = ('category', 'is_required')
    search_fields = ('name', 'category', 'description')
    ordering = ('category', 'name')
    
    fieldsets = (
        ('Document Type Info', {'fields': ('name', 'category', 'description')}),
        ('Requirements', {'fields': ('is_required', 'allowed_file_types', 'max_file_size_mb')}),
    )


@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserDocument model
    """
    list_display = ('id', 'user_name', 'user_email', 'document_type', 'file_name', 'file_download_link', 'status', 'is_visible_to_admin', 'uploaded_at')
    list_filter = ('status', 'is_visible_to_admin', 'document_type__category', 'uploaded_at')
    search_fields = ('user__name', 'user__email', 'file_name', 'document_type__name')
    ordering = ('-uploaded_at',)
    readonly_fields = ('id', 'file_download_link', 'file_name', 'file_size', 'file_type', 'uploaded_at', 'updated_at', 'cloudinary_public_id')
    
    fieldsets = (
        ('Document Info', {'fields': ('user', 'document_type', 'file_download_link', 'file_name', 'file_size', 'file_type')}),
        ('Status & Visibility', {'fields': ('status', 'is_visible_to_admin', 'admin_notes')}),
        ('Review Info', {'fields': ('reviewed_by', 'reviewed_at')}),
        ('Technical Info', {'fields': ('cloudinary_public_id', 'uploaded_at', 'updated_at')}),
    )
    
    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = 'User Name'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def file_download_link(self, obj):
        """Create a clickable download link for the document"""
        if obj.file:
            return mark_safe(f'<a href="{obj.file}" target="_blank" style="color: #007cba; text-decoration: none;">📄 Download {obj.file_name}</a>')
        return "No file"
    file_download_link.short_description = 'Download'
    
    def get_queryset(self, request):
        """Filter documents based on visibility and user permissions"""
        queryset = super().get_queryset(request).select_related('user', 'document_type', 'reviewed_by')
        
        # If user is not superuser, show documents based on user approval status
        if not request.user.is_superuser:
            # Show all documents for pending users (so admin can review them)
            # Show only visible documents for approved/rejected users
            queryset = queryset.filter(
                models.Q(user__approval_status='pending') | 
                models.Q(is_visible_to_admin=True)
            )
        
        return queryset
    
    def has_change_permission(self, request, obj=None):
        """Allow changes to documents for pending users or visible documents"""
        if obj and not request.user.is_superuser:
            # Allow changes for pending users or visible documents
            if not (obj.user.approval_status == 'pending' or obj.is_visible_to_admin):
                return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of documents for pending users or visible documents"""
        if obj and not request.user.is_superuser:
            # Allow deletion for pending users or visible documents
            if not (obj.user.approval_status == 'pending' or obj.is_visible_to_admin):
                return False
        return super().has_delete_permission(request, obj)


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    """
    Admin configuration for Admin model
    """
    list_display = ('admin_id', 'user_name', 'user_email', 'user_phone')
    search_fields = ('user__name', 'user__email', 'user__phone_no')
    ordering = ('admin_id',)
    
    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = 'Name'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_phone(self, obj):
        return obj.user.phone_no
    user_phone.short_description = 'Phone'


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """
    Admin configuration for EmailOTP model
    """
    list_display = ('email', 'purpose', 'otp', 'is_used', 'attempts', 'created_at', 'expires_at')
    list_filter = ('purpose', 'is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'otp')
    readonly_fields = ('otp', 'created_at', 'expires_at')
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    actions = ['mark_as_used', 'regenerate_otp']
    
    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f'{updated} OTP(s) marked as used.')
    mark_as_used.short_description = "Mark selected OTPs as used"
    
    def regenerate_otp(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        for otp_obj in queryset:
            otp_obj.otp = otp_obj.generate_otp()
            otp_obj.expires_at = timezone.now() + timedelta(minutes=10)
            otp_obj.is_used = False
            otp_obj.attempts = 0
            otp_obj.save()
        
        self.message_user(request, f'{queryset.count()} OTP(s) regenerated.')
    regenerate_otp.short_description = "Regenerate selected OTPs"
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(JWTToken)
class JWTTokenAdmin(admin.ModelAdmin):
    """
    Admin configuration for JWTToken model
    """
    list_display = ('user', 'token_type', 'is_revoked', 'is_blacklisted', 'issued_at', 'expires_at', 'last_used_at')
    list_filter = ('token_type', 'is_revoked', 'is_blacklisted', 'issued_at', 'expires_at')
    search_fields = ('user__name', 'user__email', 'jti', 'ip_address')
    readonly_fields = ('token_hash', 'jti', 'issued_at', 'last_used_at', 'usage_count')
    date_hierarchy = 'issued_at'
    ordering = ['-issued_at']
    
    fieldsets = (
        ('Token Info', {'fields': ('user', 'token_type', 'token_hash', 'jti')}),
        ('Status', {'fields': ('is_revoked', 'is_blacklisted', 'revoked_at', 'blacklisted_at')}),
        ('Timing', {'fields': ('issued_at', 'expires_at', 'last_used_at', 'usage_count')}),
        ('Security', {'fields': ('ip_address', 'user_agent', 'device_info')}),
        ('Referral Info', {'fields': ('max_uses', 'used_by', 'referrer_reward', 'referee_reward', 'campaign_name'), 'classes': ('collapse',)}),
    )
    
    actions = ['revoke_tokens', 'blacklist_tokens', 'cleanup_expired']
    
    def revoke_tokens(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_revoked=True, revoked_at=timezone.now())
        self.message_user(request, f'{updated} token(s) revoked.')
    revoke_tokens.short_description = "Revoke selected tokens"
    
    def blacklist_tokens(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_blacklisted=True, blacklisted_at=timezone.now())
        self.message_user(request, f'{updated} token(s) blacklisted.')
    blacklist_tokens.short_description = "Blacklist selected tokens"
    
    def cleanup_expired(self, request, queryset):
        from django.utils import timezone
        expired_tokens = queryset.filter(expires_at__lt=timezone.now())
        count = expired_tokens.count()
        expired_tokens.delete()
        self.message_user(request, f'{count} expired token(s) cleaned up.')
    cleanup_expired.short_description = "Clean up expired tokens"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'used_by')