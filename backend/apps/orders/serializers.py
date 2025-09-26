from rest_framework import serializers
from django.db.models import Sum, Count
from .models import Order, OrderItem, OrderStatusHistory, CartItem, BulkOrder, BulkOrderAssignment, UserAddress
from apps.food.models import Food, FoodPrice
from django.contrib.auth import get_user_model
from apps.users.models import ChefProfile

User = get_user_model()


class UserAddressSerializer(serializers.ModelSerializer):
    """Serializer for user saved addresses"""
    
    class Meta:
        model = UserAddress
        fields = [
            'id', 'label', 'address_line1', 'address_line2', 
            'city', 'pincode', 'latitude', 'longitude', 
            'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FoodPriceSerializer(serializers.ModelSerializer):
    """Nested serializer for food price information"""
    food_name = serializers.CharField(source='food.name', read_only=True)
    food_description = serializers.CharField(source='food.description', read_only=True)
    food_category = serializers.CharField(source='food.category', read_only=True)
    food_image = serializers.CharField(source='food.image', read_only=True)
    
    class Meta:
        model = FoodPrice
        fields = ['price_id', 'price', 'size', 'food_name', 'food_description', 'food_category', 'food_image']


class CustomerSerializer(serializers.ModelSerializer):
    """Nested serializer for customer information"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'phone_no', 'name']
        
    def get_full_name(self, obj):
        if obj.name:
            return obj.name
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class ChefSerializer(serializers.ModelSerializer):
    """Serializer for chef user information with kitchen location"""
    full_name = serializers.SerializerMethodField()
    kitchen_location = serializers.SerializerMethodField()
    specialty = serializers.SerializerMethodField()
    availability_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'phone_no', 'name', 
                 'kitchen_location', 'specialty', 'availability_hours']
        
    def get_full_name(self, obj):
        if obj.name:
            return obj.name
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    
    def get_kitchen_location(self, obj):
        """Get kitchen location from Cook profile for pickup by delivery partners"""
        try:
            from apps.authentication.models import Cook
            cook_profile = Cook.objects.get(user=obj)
            return cook_profile.kitchen_location
        except Cook.DoesNotExist:
            return None
    
    def get_specialty(self, obj):
        """Get specialty from Cook profile"""
        try:
            from apps.authentication.models import Cook
            cook_profile = Cook.objects.get(user=obj)
            return cook_profile.specialty
        except Cook.DoesNotExist:
            return None
    
    def get_availability_hours(self, obj):
        """Get availability hours from Cook profile"""
        try:
            from apps.authentication.models import Cook
            cook_profile = Cook.objects.get(user=obj)
            return cook_profile.availability_hours
        except Cook.DoesNotExist:
            return None


class ChefProfileSerializer(serializers.ModelSerializer):
    """Nested serializer for chef information"""
    chef_name = serializers.CharField(source='user.get_full_name', read_only=True)
    chef_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = ChefProfile
        fields = ['id', 'chef_name', 'chef_email', 'specialties', 'bio', 'profile_image']


class OrderItemDetailSerializer(serializers.ModelSerializer):
    """Enhanced OrderItem serializer with nested food details"""
    price_details = FoodPriceSerializer(source='price', read_only=True)
    item_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['order_item_id', 'quantity', 'special_instructions', 'price_details', 'item_total']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['item_total'] = instance.total_price
        return data


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Enhanced status history with user details"""
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'status_display', 'changed_by', 'changed_by_name', 'notes', 'created_at']


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order lists and dashboard"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    chef_name = serializers.CharField(source='chef.get_full_name', read_only=True)
    total_items = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_since_order = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display', 'total_amount', 
            'customer_name', 'chef_name', 'total_items', 'created_at', 
            'time_since_order', 'delivery_address'
        ]
    
    def get_total_items(self, obj):
        return obj.items.aggregate(total=Sum('quantity'))['total'] or 0
    
    def get_time_since_order(self, obj):
        from django.utils import timezone
        diff = timezone.now() - obj.created_at
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return f"{int(diff.total_seconds() / 60)}m ago"
        elif hours < 24:
            return f"{int(hours)}h ago"
        else:
            return f"{int(hours / 24)}d ago"


class OrderDetailSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for order details"""
    customer = CustomerSerializer(read_only=True)
    chef = ChefSerializer(read_only=True)
    items = OrderItemDetailSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Fields expected by frontend
    customer_name = serializers.SerializerMethodField()
    chef_name = serializers.SerializerMethodField()
    time_since_order = serializers.SerializerMethodField()
    pickup_location = serializers.SerializerMethodField()  # For delivery partners
    
    # Computed fields
    total_items = serializers.SerializerMethodField()
    estimated_prep_time = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    time_in_current_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'total_amount', 'delivery_fee', 'tax_amount', 'discount_amount',
            'delivery_address', 'delivery_instructions', 'customer_notes', 'payment_method',
            'payment_status', 'estimated_delivery_time', 'actual_delivery_time',
            'created_at', 'updated_at', 'customer', 'chef', 'items',
            'status_history', 'total_items', 'estimated_prep_time',
            'can_edit', 'time_in_current_status', 'customer_name', 'chef_name', 
            'time_since_order', 'customer_notes', 'chef_notes', 'pickup_location'
        ]
    
    def get_customer_name(self, obj):
        if obj.customer:
            return obj.customer.name or f"{obj.customer.first_name} {obj.customer.last_name}".strip() or obj.customer.username
        return "Unknown Customer"
    
    def get_chef_name(self, obj):
        if obj.chef:
            return obj.chef.name or f"{obj.chef.first_name} {obj.chef.last_name}".strip() or obj.chef.username
        return "Unknown Chef"
    
    def get_time_since_order(self, obj):
        from django.utils import timezone
        diff = timezone.now() - obj.created_at
        minutes = int(diff.total_seconds() / 60)
        if minutes < 60:
            return f"{minutes} minutes ago"
        elif minutes < 1440:  # Less than 24 hours
            hours = int(minutes / 60)
            return f"{hours} hours ago"
        else:
            days = int(minutes / 1440)
            return f"{days} days ago"
    
    def get_total_items(self, obj):
        return obj.items.aggregate(total=Sum('quantity'))['total'] or 0
    
    def get_estimated_prep_time(self, obj):
        # Calculate based on number of items and complexity
        total_items = self.get_total_items(obj)
        base_time = 15  # 15 minutes base
        return base_time + (total_items * 5)  # 5 minutes per item
    
    def get_can_edit(self, obj):
        # Orders can be edited if they're in cart, pending, or confirmed status
        return obj.status in ['cart', 'pending', 'confirmed']
    
    def get_time_in_current_status(self, obj):
        from django.utils import timezone
        # Get the latest status change or order creation time
        latest_status = obj.status_history.first()
        if latest_status:
            status_time = latest_status.created_at
        else:
            status_time = obj.created_at
        
        diff = timezone.now() - status_time
        minutes = int(diff.total_seconds() / 60)
        if minutes < 60:
            return f"{minutes}m"
        else:
            hours = int(minutes / 60)
            return f"{hours}h {minutes % 60}m"
    
    def get_pickup_location(self, obj):
        """Get chef's kitchen location for delivery partner pickup"""
        if obj.chef:
            try:
                from apps.authentication.models import Cook
                cook_profile = Cook.objects.get(user=obj.chef)
                return cook_profile.kitchen_location
            except Cook.DoesNotExist:
                return None
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """Enhanced cart item serializer with all required fields for frontend"""
    food_name = serializers.CharField(source='price.food.name', read_only=True)
    cook_name = serializers.CharField(source='price.cook.get_full_name', read_only=True)
    chef_id = serializers.SerializerMethodField()
    size = serializers.CharField(source='price.size', read_only=True)
    unit_price = serializers.DecimalField(source='price.price', max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.SerializerMethodField()
    food_image = serializers.CharField(source='price.food.image', read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'quantity', 'special_instructions', 'food_name', 'cook_name', 'chef_id',
            'size', 'unit_price', 'total_price', 'food_image', 'created_at', 'updated_at'
        ]
        
    def get_chef_id(self, obj):
        """Get chef ID from the price's cook"""
        try:
            # Custom User model uses user_id as primary key
            return obj.price.cook.user_id
        except:
            return None
        
    def get_total_price(self, obj):
        return obj.total_price


class OrderStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    preparing_orders = serializers.IntegerField()
    ready_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_prep_time = serializers.FloatField()
    total_customers = serializers.IntegerField()


class BulkOrderActionSerializer(serializers.Serializer):
    """Serializer for bulk order operations"""
    order_ids = serializers.ListField(child=serializers.IntegerField())
    action = serializers.ChoiceField(choices=[
        ('assign_chef', 'Assign Chef'),
        ('update_status', 'Update Status'),
        ('delete', 'Delete Orders'),
        ('export', 'Export Orders')
    ])
    chef_id = serializers.IntegerField(required=False)
    new_status = serializers.CharField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)




class CheckoutValidationSerializer(serializers.Serializer):
    """Comprehensive validation for checkout process"""
    
    # Required fields
    chef_id = serializers.IntegerField(required=True, help_text="Chef ID for the order")
    delivery_latitude = serializers.DecimalField(
        max_digits=10, 
        decimal_places=8, 
        required=True,
        help_text="Delivery latitude coordinate"
    )
    delivery_longitude = serializers.DecimalField(
        max_digits=11, 
        decimal_places=8, 
        required=True,
        help_text="Delivery longitude coordinate"
    )
    
    # Optional fields
    delivery_address_id = serializers.IntegerField(required=False, allow_null=True)
    promo_code = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    customer_notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_chef_id(self, value):
        """Validate chef exists and is active"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            chef = User.objects.get(user_id=value)
            # Check if user is a chef/cook
            if not hasattr(chef, 'cook') and not hasattr(chef, 'chefprofile'):
                raise serializers.ValidationError("User is not a chef")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Chef not found")
    
    def validate_delivery_latitude(self, value):
        """Validate latitude is within valid range"""
        if not (-90 <= float(value) <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90 degrees")
        return value
    
    def validate_delivery_longitude(self, value):
        """Validate longitude is within valid range"""
        if not (-180 <= float(value) <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180 degrees")
        return value
    
    def validate_delivery_address_id(self, value):
        """Validate delivery address exists and belongs to user"""
        if value is not None:
            try:
                from .models import UserAddress
                address = UserAddress.objects.get(id=value)
                # Note: We can't validate user ownership here since we don't have request context
                # This will be validated in the view
                return value
            except UserAddress.DoesNotExist:
                raise serializers.ValidationError("Delivery address not found")
        return value
    
    def validate_promo_code(self, value):
        """Validate promo code format and existence"""
        if value and value.strip():
            # Basic format validation
            if len(value.strip()) < 3:
                raise serializers.ValidationError("Promo code must be at least 3 characters")
            # Additional validation can be added here for promo code existence
        return value
    
    def validate_customer_notes(self, value):
        """Validate customer notes length and content"""
        if value and len(value.strip()) > 500:
            raise serializers.ValidationError("Customer notes cannot exceed 500 characters")
        return value


class PlaceOrderValidationSerializer(CheckoutValidationSerializer):
    """Extended validation for place order endpoint"""
    
    # Additional validation for order placement
    payment_method = serializers.ChoiceField(
        choices=[('cash', 'Cash on Delivery')],
        required=False,
        default='cash'
    )
    
    def validate_payment_method(self, value):
        """Validate payment method is supported"""
        if value not in ['cash']:
            raise serializers.ValidationError("Only cash on delivery is currently supported")
        return value


class CartValidationMixin:
    """Mixin for cart-related validations"""
    
    def validate_cart_not_empty(self, user):
        """Validate cart is not empty"""
        from .models import CartItem
        cart_items = CartItem.objects.filter(customer=user)
        if not cart_items.exists():
            raise serializers.ValidationError("Cart is empty")
        return cart_items
    
    def validate_cart_consistency(self, cart_items, chef_id):
        """Validate all cart items belong to the same chef"""
        for item in cart_items:
            if not hasattr(item.price, 'cook') or not item.price.cook:
                raise serializers.ValidationError(f"Cart item {item.id} has no associated chef")
            if item.price.cook.user_id != chef_id:
                raise serializers.ValidationError("All cart items must be from the same chef")
        return True
    
    def validate_cart_item_availability(self, cart_items):
        """Validate all cart items are still available"""
        unavailable_items = []
        for item in cart_items:
            if not item.price.is_available:
                unavailable_items.append(f"{item.price.food.name} ({item.price.size})")
        
        if unavailable_items:
            raise serializers.ValidationError(
                f"Some items are no longer available: {', '.join(unavailable_items)}"
            )
        return True


class BusinessRuleValidationMixin:
    """Mixin for business rule validations"""
    
    def validate_delivery_distance(self, chef_lat, chef_lng, delivery_lat, delivery_lng):
        """Validate delivery distance is within service range"""
        import math
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth's radius in kilometers
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        distance_km = haversine_distance(
            float(chef_lat), float(chef_lng), 
            float(delivery_lat), float(delivery_lng)
        )
        
        MAX_DELIVERY_KM = 50.0
        if math.isnan(distance_km) or distance_km <= 0:
            raise serializers.ValidationError("Invalid distance calculation. Please verify addresses.")
        if distance_km > MAX_DELIVERY_KM:
            raise serializers.ValidationError(
                f"Delivery distance {round(distance_km, 2)} km is out of service range (max {int(MAX_DELIVERY_KM)} km)."
            )
        return distance_km
    
    def validate_chef_availability(self, chef):
        """Validate chef is available for orders"""
        # Check if chef profile exists and is active
        try:
            from apps.authentication.models import Cook
            cook_profile = Cook.objects.get(user=chef)
            if not cook_profile.is_active:
                raise serializers.ValidationError("Chef is currently not accepting orders")
        except Cook.DoesNotExist:
            raise serializers.ValidationError("Chef profile not found")
        
        # Additional availability checks can be added here
        return True
    
    def validate_order_timing(self):
        """Validate order timing (e.g., not too late at night)"""
        from django.utils import timezone
        import datetime
        
        current_time = timezone.now().time()
        # Example: No orders between 11 PM and 6 AM
        if datetime.time(23, 0) <= current_time or current_time <= datetime.time(6, 0):
            raise serializers.ValidationError("Orders are not accepted between 11 PM and 6 AM")
        return True


class DataIntegrityValidationMixin:
    """Mixin for data integrity validations"""
    
    def validate_pricing_consistency(self, cart_items):
        """Validate pricing is consistent and not tampered with"""
        for item in cart_items:
            # Check if price has changed since item was added to cart
            current_price = item.price.price
            if item.unit_price and item.unit_price != current_price:
                raise serializers.ValidationError(
                    f"Price for {item.price.food.name} has changed. Please refresh your cart."
                )
        return True
    
    def validate_minimum_order_amount(self, subtotal):
        """Validate minimum order amount"""
        MINIMUM_ORDER = 250.00  # Minimum order amount in LKR
        if float(subtotal) < MINIMUM_ORDER:
            raise serializers.ValidationError(
                f"Minimum order amount is LKR {MINIMUM_ORDER}. Current subtotal: LKR {subtotal}"
            )
        return True
    
    def validate_maximum_order_amount(self, total_amount):
        """Validate maximum order amount"""
        MAXIMUM_ORDER = 50000.00  # Maximum order amount in LKR
        if float(total_amount) > MAXIMUM_ORDER:
            raise serializers.ValidationError(
                f"Maximum order amount is LKR {MAXIMUM_ORDER}. Please contact support for large orders."
            )
        return True


# Legacy serializers for backward compatibility
class OrderSerializer(OrderDetailSerializer):
    """Legacy serializer - use OrderDetailSerializer instead"""
    pass


class OrderItemSerializer(OrderItemDetailSerializer):
    """Legacy serializer - use OrderItemDetailSerializer instead"""
    pass


# ===== BULK ORDER SERIALIZERS =====

class BulkOrderAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for bulk order assignments"""
    chef_name = serializers.SerializerMethodField()
    chef_username = serializers.CharField(source='chef.username', read_only=True)
    chef_email = serializers.CharField(source='chef.email', read_only=True)
    
    class Meta:
        model = BulkOrderAssignment
        fields = ['id', 'chef', 'chef_name', 'chef_username', 'chef_email']
    
    def get_chef_name(self, obj):
        return obj.chef.name if obj.chef and obj.chef.name else obj.chef.username if obj.chef else 'Unknown Chef'


class BulkOrderListSerializer(serializers.ModelSerializer):
    """Serializer for bulk order list view - matches frontend BulkOrder interface"""
    # Map bulk order fields to frontend expected fields
    id = serializers.IntegerField(source='bulk_order_id', read_only=True)
    order_number = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    event_type = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    event_date = serializers.DateTimeField(source='deadline', read_only=True)
    
    # Menu items as expected by frontend
    items = serializers.SerializerMethodField()
    
    # Collaborators from assignments
    collaborators = serializers.SerializerMethodField()
    
    class Meta:
        model = BulkOrder
        fields = [
            'id', 'order_number', 'customer_name', 'event_type', 'event_date',
            'status', 'total_amount', 'total_quantity', 'description',
            'items', 'collaborators', 'created_at', 'updated_at'
        ]
    
    def get_customer_name(self, obj):
        return obj.created_by.name if obj.created_by and obj.created_by.name else obj.created_by.username if obj.created_by else 'Unknown User'
    
    def get_order_number(self, obj):
        return f"BULK-{obj.bulk_order_id:06d}"
    
    def get_event_type(self, obj):
        # Extract event type from description or default
        if obj.description:
            # Try to extract event type from description
            description_lower = obj.description.lower()
            if 'wedding' in description_lower:
                return 'wedding'
            elif 'corporate' in description_lower:
                return 'corporate'
            elif 'party' in description_lower:
                return 'party'
            elif 'birthday' in description_lower:
                return 'birthday'
        return 'other'
    
    def get_total_amount(self, obj):
        # Calculate from related order or return default
        if obj.order:
            return str(obj.order.total_amount)
        return "0.00"
    
    def get_items(self, obj):
        # Get items from the related order
        if obj.order:
            order_items = obj.order.items.all()[:3]  # Limit to first 3
            return [
                {
                    'id': item.order_item_id,
                    'food_name': item.food_name or 'Unknown Item',
                    'quantity': item.quantity,
                    'special_instructions': item.special_instructions or None
                }
                for item in order_items
            ]
        return []
    
    def get_collaborators(self, obj):
        # Get assigned chefs
        assignments = obj.assignments.select_related('chef')
        return [
            {
                'id': assignment.chef.user_id,
                'name': assignment.chef.name if assignment.chef.name else assignment.chef.username,
                'email': assignment.chef.email,
                'role': 'chef'
            }
            for assignment in assignments
        ]


class BulkOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for bulk order with all related data"""
    id = serializers.IntegerField(source='bulk_order_id', read_only=True)
    order_number = serializers.SerializerMethodField()
    customer = CustomerSerializer(source='created_by', read_only=True)
    event_type = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    event_date = serializers.DateTimeField(source='deadline', read_only=True)
    assignments = BulkOrderAssignmentSerializer(many=True, read_only=True)
    order_details = OrderDetailSerializer(source='order', read_only=True)
    
    class Meta:
        model = BulkOrder
        fields = [
            'id', 'order_number', 'customer', 'event_type', 'event_date',
            'status', 'total_amount', 'total_quantity', 'description',
            'assignments', 'order_details', 'created_at', 'updated_at'
        ]
    
    def get_order_number(self, obj):
        return f"BULK-{obj.bulk_order_id:06d}"
    
    def get_event_type(self, obj):
        # Extract event type from description or default
        if obj.description:
            description_lower = obj.description.lower()
            if 'wedding' in description_lower:
                return 'wedding'
            elif 'corporate' in description_lower:
                return 'corporate'
            elif 'party' in description_lower:
                return 'party'
            elif 'birthday' in description_lower:
                return 'birthday'
        return 'other'
    
    def get_total_amount(self, obj):
        if obj.order:
            return str(obj.order.total_amount)
        return "0.00"
