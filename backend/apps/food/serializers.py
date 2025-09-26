from rest_framework import serializers
from .models import Cuisine, FoodCategory, Food, FoodReview, FoodPrice, Offer
from utils.cloudinary_utils import get_optimized_url, upload_image_to_cloudinary
import base64
import uuid


class CuisineSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Cuisine
        fields = ['id', 'name', 'description', 'image', 'image_url', 'thumbnail_url', 'is_active', 'sort_order']
    
    def get_image_url(self, obj):
        """Return optimized Cloudinary URL"""
        if obj.image:
            return get_optimized_url(str(obj.image))
        return None
    
    def get_thumbnail_url(self, obj):
        """Get thumbnail version of the image"""
        if obj.image:
            return get_optimized_url(str(obj.image), width=200, height=200)
        return None


class FoodCategorySerializer(serializers.ModelSerializer):
    cuisine_name = serializers.CharField(source='cuisine.name', read_only=True)
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'cuisine', 'cuisine_name', 'description', 'image', 'image_url', 'thumbnail_url', 'is_active', 'sort_order']
    
    def get_image_url(self, obj):
        """Return optimized Cloudinary URL"""
        if obj.image:
            return get_optimized_url(str(obj.image))
        return None
    
    def get_thumbnail_url(self, obj):
        """Get thumbnail version of the image"""
        if obj.image:
            return get_optimized_url(str(obj.image), width=200, height=200)
        return None


class FoodPriceSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name', read_only=True)
    cook_name = serializers.CharField(source='cook.name', read_only=True)
    cook_rating = serializers.SerializerMethodField()
    image_data_url = serializers.SerializerMethodField()
    cook = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodPrice
        fields = [
            'price_id', 'size', 'price', 'preparation_time', 'image_url', 'image_data_url', 'food', 'food_name', 'cook', 'cook_name',
            'cook_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['price_id', 'created_at', 'updated_at']
    
    def get_cook_rating(self, obj):
        # You might want to calculate this from reviews
        return getattr(obj.cook, 'rating', 4.5)
    
    def get_cook(self, obj):
        """Return cook information in the expected format"""
        profile_image_url = None
        if obj.cook.profile_image:
            # Convert binary image to base64 data URL
            import base64
            try:
                encoded_image = base64.b64encode(obj.cook.profile_image).decode('utf-8')
                profile_image_url = f"data:image/jpeg;base64,{encoded_image}"
            except Exception:
                profile_image_url = None
        
        return {
            'id': obj.cook.pk,  # Use pk instead of id
            'name': obj.cook.name,
            'rating': getattr(obj.cook, 'rating', 4.5),
            'is_active': getattr(obj.cook, 'is_active', True),
            'profile_image': profile_image_url
        }
    
    def get_image_data_url(self, obj):
        """Return optimized Cloudinary URL"""
        if obj.image_url:
            return get_optimized_url(str(obj.image_url))
        return None


class FoodSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='food_category.name', read_only=True)
    cuisine_name = serializers.CharField(source='food_category.cuisine.name', read_only=True)
    available_cooks_count = serializers.SerializerMethodField()
    chef_name = serializers.CharField(source="chef.username", read_only=True)
    chef_rating = serializers.DecimalField(source="chef.chef_profile.rating_average", max_digits=3, decimal_places=2, read_only=True)
    prices = FoodPriceSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    optimized_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Food
        fields = [
            'food_id', 'name', 'description', 'category', 'food_category', 'category_name', 'cuisine_name',
            'is_available', 'is_featured', 'preparation_time', 'calories_per_serving', 'ingredients',
            'allergens', 'nutritional_info', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'spice_level',
            'rating_average', 'total_reviews', 'total_orders', 'primary_image', 'available_cooks_count',
            'image_url', 'thumbnail_url', 'optimized_image_url', 'image',
            'status', 'chef', 'chef_name', 'chef_rating', 'prices', 'created_at', 'updated_at'
        ]
        read_only_fields = ['food_id', 'chef', 'chef_name', 'chef_rating', 'prices', 'created_at', 'updated_at']
    
    def get_primary_image(self, obj):
        """Return the primary image URL from the Food model"""
        return obj.optimized_image_url
    
    def get_image_url(self, obj):
        """Get primary image URL for compatibility"""
        return obj.image_url
    
    def get_optimized_image_url(self, obj):
        """Get optimized Cloudinary URL"""
        return obj.optimized_image_url
    
    def get_thumbnail_url(self, obj):
        """Get thumbnail URL"""
        return obj.thumbnail_url
    
    def get_available_cooks_count(self, obj):
        """Get count of cooks who have prices for this food"""
        return obj.prices.values('cook').distinct().count()

    def create(self, validated_data):
        # Handle image upload if provided
        image_data = validated_data.get('image')
        if image_data:
            validated_data['image'] = self._handle_image_upload(image_data, validated_data.get('name', 'food'))
        
        # Set status to pending and assign current user as chef
        validated_data['status'] = 'Pending'
        validated_data['chef'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Handle image upload if provided
        image_data = validated_data.get('image')
        if image_data:
            validated_data['image'] = self._handle_image_upload(image_data, instance.name)
        
        return super().update(instance, validated_data)

    def _handle_image_upload(self, image_data, food_name):
        """
        Handle image upload to Cloudinary
        Supports: file upload, base64 string, or existing URL
        """
        # If it's already a Cloudinary URL, return as is
        if isinstance(image_data, str) and ('cloudinary.com' in image_data or image_data.startswith('http')):
            return image_data
            
        # If it's a file upload or base64 data
        try:
            # Generate a unique folder and public_id based on food name
            import re
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', food_name.lower())
            folder = 'chefsync/foods'
            
            # Upload to Cloudinary
            result = upload_image_to_cloudinary(
                image_data=image_data,
                folder=folder,
                public_id=f"food_{clean_name}_{uuid.uuid4().hex[:8]}",
                tags=['food', 'chefsync']
            )
            
            if result and result.get('secure_url'):
                return result['secure_url']
            else:
                # If upload fails, return the original data
                return image_data
                
        except Exception as e:
            print(f"Error uploading food image: {e}")
            # Return original data if upload fails
            return image_data


class ChefFoodPriceSerializer(serializers.ModelSerializer):
    """Serializer for chefs to create prices for existing foods"""
    class Meta:
        model = FoodPrice
        fields = ['price', 'size', 'preparation_time', 'food']
    
    def validate(self, data):
        """Check for duplicate price entries"""
        user = self.context['request'].user
        food = data.get('food')
        size = data.get('size')
        
        # Check if a price already exists for this combination
        existing_price = FoodPrice.objects.filter(
            food=food,
            size=size,
            cook=user
        ).first()
        
        if existing_price:
            raise serializers.ValidationError({
                'non_field_errors': [f'You already have a {size} price for this food item. Please update the existing price instead.']
            })
        
        return data
        
    def create(self, validated_data):
        validated_data['cook'] = self.context['request'].user
        return super().create(validated_data)


# ===== FOOD VALIDATION SERIALIZERS =====

class FoodValidationMixin:
    """Mixin for food-related validations"""
    
    def validate_food_name(self, name):
        """Validate food name format and uniqueness"""
        if not name or not name.strip():
            raise serializers.ValidationError("Food name is required")
        
        name = name.strip()
        if len(name) < 3:
            raise serializers.ValidationError("Food name must be at least 3 characters long")
        
        if len(name) > 100:
            raise serializers.ValidationError("Food name cannot exceed 100 characters")
        
        # Check for duplicate names by the same chef
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            existing_food = Food.objects.filter(
                name__iexact=name, 
                chef=user
            ).exclude(
                pk=getattr(self.instance, 'pk', None)
            ).first()
            
            if existing_food:
                raise serializers.ValidationError(
                    f"You already have a food item named '{name}'. Please choose a different name."
                )
        
        return name
    
    def validate_ingredients(self, ingredients):
        """Validate ingredients list"""
        if ingredients is None:
            return []
        
        if isinstance(ingredients, str):
            ingredients = ingredients.strip()
            if ingredients:
                try:
                    import json
                    parsed = json.loads(ingredients)
                    if isinstance(parsed, list):
                        ingredients = [str(item).strip() for item in parsed if str(item).strip()]
                    else:
                        ingredients = [str(parsed).strip()] if str(parsed).strip() else []
                except (json.JSONDecodeError, ValueError):
                    ingredients = [item.strip() for item in ingredients.split(',') if item.strip()]
            else:
                ingredients = []
        
        if not isinstance(ingredients, list):
            ingredients = []
        
        # Validate each ingredient
        validated_ingredients = []
        for ingredient in ingredients:
            if isinstance(ingredient, str) and ingredient.strip():
                ingredient = ingredient.strip()
                if len(ingredient) > 100:
                    raise serializers.ValidationError(f"Ingredient '{ingredient[:50]}...' is too long (max 100 characters)")
                validated_ingredients.append(ingredient)
        
        if len(validated_ingredients) > 20:
            raise serializers.ValidationError("Maximum 20 ingredients allowed")
        
        return validated_ingredients
    
    def validate_allergens(self, allergens):
        """Validate allergens list"""
        if allergens is None:
            return []
        
        if isinstance(allergens, str):
            allergens = allergens.strip()
            if allergens:
                allergens = [item.strip() for item in allergens.split(',') if item.strip()]
            else:
                allergens = []
        
        if not isinstance(allergens, list):
            allergens = []
        
        # Validate each allergen
        validated_allergens = []
        for allergen in allergens:
            if isinstance(allergen, str) and allergen.strip():
                allergen = allergen.strip()
                if len(allergen) > 50:
                    raise serializers.ValidationError(f"Allergen '{allergen[:30]}...' is too long (max 50 characters)")
                validated_allergens.append(allergen)
        
        if len(validated_allergens) > 10:
            raise serializers.ValidationError("Maximum 10 allergens allowed")
        
        return validated_allergens
    
    def validate_price(self, price):
        """Validate price range in LKR (Sri Lankan Rupees)"""
        if price is None:
            raise serializers.ValidationError("Price is required")
        
        try:
            price = float(price)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Price must be a valid number")
        
        if price <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        
        if price < 50.00:
            raise serializers.ValidationError("Minimum price is LKR 50.00")
        
        if price > 50000.00:
            raise serializers.ValidationError("Maximum price is LKR 50,000.00")
        
        return price
    
    def validate_preparation_time(self, time):
        """Validate preparation time"""
        if time is None:
            return 15  # Default
        
        try:
            time = int(time)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Preparation time must be a valid integer")
        
        if time < 5:
            raise serializers.ValidationError("Minimum preparation time is 5 minutes")
        
        if time > 180:
            raise serializers.ValidationError("Maximum preparation time is 180 minutes (3 hours)")
        
        return time
    
    def validate_spice_level(self, level):
        """Validate spice level"""
        if level is None or level == '':
            return None
        
        valid_levels = ['mild', 'medium', 'hot', 'very_hot']
        if level not in valid_levels:
            raise serializers.ValidationError(f"Spice level must be one of: {', '.join(valid_levels)}")
        
        return level
    
    def validate_dietary_restrictions(self, data):
        """Validate dietary restriction combinations"""
        is_vegetarian = data.get('is_vegetarian', False)
        is_vegan = data.get('is_vegan', False)
        
        # Vegan implies vegetarian
        if is_vegan and not is_vegetarian:
            data['is_vegetarian'] = True
        
        return data


class ImageValidationMixin:
    """Mixin for image validation"""
    
    def validate_image(self, image):
        """Validate image file"""
        if image is None:
            return None
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if hasattr(image, 'size') and image.size > max_size:
            raise serializers.ValidationError("Image file size cannot exceed 10MB")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if hasattr(image, 'content_type') and image.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Image must be one of: {', '.join(allowed_types)}. Got: {image.content_type}"
            )
        
        # Check file extension
        if hasattr(image, 'name'):
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            file_extension = '.' + image.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Image must have one of these extensions: {', '.join(allowed_extensions)}"
                )
        
        return image


class ChefFoodCreateSerializer(serializers.ModelSerializer, FoodValidationMixin, ImageValidationMixin):
    """Enhanced serializer for chefs to create new food items with comprehensive validation"""
    
    # Price fields for the initial price entry
    price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        write_only=True,
        help_text="Price must be between LKR 50.00 and LKR 50,000.00"
    )
    size = serializers.ChoiceField(
        choices=[('Small', 'Small'), ('Medium', 'Medium'), ('Large', 'Large')],
        write_only=True, 
        default='Medium',
        help_text="Size of the food item"
    )
    preparation_time = serializers.IntegerField(
        write_only=True, 
        default=15,
        help_text="Preparation time in minutes (5-180)"
    )
    # Custom image field that accepts files
    image = serializers.FileField(
        required=False, 
        allow_null=True, 
        write_only=True,
        help_text="Food image (max 10MB, formats: JPG, PNG, WebP)"
    )
    
    class Meta:
        model = Food
        fields = [
            'name', 'description', 'category', 'image', 'ingredients', 
            'is_vegetarian', 'is_vegan', 'is_gluten_free', 'spice_level', 'is_available',
            'price', 'size', 'preparation_time'
        ]
    
    def validate_name(self, value):
        """Validate food name with comprehensive checks"""
        return self.validate_food_name(value)
    
    def validate_price(self, value):
        """Validate price with comprehensive checks"""
        return self.validate_price(value)
    
    def validate_preparation_time(self, value):
        """Validate preparation time with comprehensive checks"""
        return self.validate_preparation_time(value)
    
    def validate_spice_level(self, value):
        """Validate spice level with comprehensive checks"""
        return self.validate_spice_level(value)
    
    def validate_ingredients(self, value):
        """Validate ingredients with comprehensive checks"""
        return self.validate_ingredients(value)
    
    def validate_image(self, value):
        """Validate and process image upload with comprehensive checks"""
        if value:
            # Apply image validation from mixin
            validated_image = super().validate_image(value)
            if validated_image:
                print(f"DEBUG: Image file validated: {validated_image.name}, size: {validated_image.size}")
                # Use the same image upload handler
                return self._handle_image_upload(validated_image, "new_food")
        return None

    def _handle_image_upload(self, image_data, food_name):
        """
        Handle image upload to Cloudinary
        Supports: file upload, base64 string, or existing URL
        """
        # If it's already a Cloudinary URL, return as is
        if isinstance(image_data, str) and ('cloudinary.com' in image_data or image_data.startswith('http')):
            return image_data
            
        # If it's a file upload or base64 data
        try:
            # Generate a unique folder and public_id based on food name
            import re
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', food_name.lower())
            folder = 'chefsync/foods'
            
            # Upload to Cloudinary
            result = upload_image_to_cloudinary(
                image_data=image_data,
                folder=folder,
                public_id=f"food_{clean_name}_{uuid.uuid4().hex[:8]}",
                tags=['food', 'chefsync']
            )
            
            if result and result.get('secure_url'):
                return result['secure_url']
            else:
                # If upload fails, return None
                return None
                
        except Exception as e:
            print(f"Error uploading food image: {e}")
            # Return None if upload fails
            return None
    
    def validate(self, data):
        """Comprehensive validation for food creation"""
        print(f"DEBUG: Full validation data received: {data}")
        print(f"DEBUG: Data types: {[(k, type(v)) for k, v in data.items()]}")
        
        # Validate dietary restrictions
        data = self.validate_dietary_restrictions(data)
        
        # Validate description length
        if 'description' in data and data['description']:
            description = data['description'].strip()
            if len(description) > 1000:
                raise serializers.ValidationError("Description cannot exceed 1000 characters")
            data['description'] = description
        
        # Validate category
        if 'category' in data and data['category']:
            category = data['category'].strip()
            if len(category) > 50:
                raise serializers.ValidationError("Category cannot exceed 50 characters")
            data['category'] = category
        
        # Ensure ingredients is properly processed
        if 'ingredients' in data:
            ingredients = data['ingredients']
            print(f"DEBUG: Raw ingredients: {ingredients} (type: {type(ingredients)})")
            
            # Force proper conversion to list for JSONField
            if isinstance(ingredients, str):
                ingredients = ingredients.strip()
                if ingredients:
                    try:
                        import json
                        # Try parsing as JSON first
                        parsed = json.loads(ingredients)
                        if isinstance(parsed, list):
                            data['ingredients'] = [str(item).strip() for item in parsed if str(item).strip()]
                        else:
                            data['ingredients'] = [str(parsed).strip()] if str(parsed).strip() else []
                    except (json.JSONDecodeError, ValueError):
                        # Fall back to comma-separated parsing
                        data['ingredients'] = [item.strip() for item in ingredients.split(',') if item.strip()]
                else:
                    data['ingredients'] = []
            elif not isinstance(ingredients, list):
                data['ingredients'] = []
            
            print(f"DEBUG: Final processed ingredients: {data['ingredients']} (type: {type(data['ingredients'])})")
        
        # Validate business rules
        self._validate_business_rules(data)
        
        return data
    
    def _validate_business_rules(self, data):
        """Validate business rules for food creation"""
        # Check if chef has reached maximum food items limit
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            MAX_FOOD_ITEMS = 50  # Business rule: max 50 food items per chef
            
            existing_count = Food.objects.filter(chef=user).count()
            if existing_count >= MAX_FOOD_ITEMS:
                raise serializers.ValidationError(
                    f"You have reached the maximum limit of {MAX_FOOD_ITEMS} food items. "
                    "Please contact support to increase your limit."
                )
        
        # Validate price consistency with preparation time
        price = data.get('price')
        prep_time = data.get('preparation_time', 15)
        
        if price and prep_time:
            # Basic validation: higher price should generally have longer prep time
            if price > 2500 and prep_time < 10:
                raise serializers.ValidationError(
                    "High-priced items should have adequate preparation time (minimum 10 minutes for items over LKR 2,500)"
                )
        
        # Validate dietary restriction combinations
        is_vegetarian = data.get('is_vegetarian', False)
        is_vegan = data.get('is_vegan', False)
        is_gluten_free = data.get('is_gluten_free', False)
        
        # If vegan, must be vegetarian
        if is_vegan and not is_vegetarian:
            data['is_vegetarian'] = True
        
        # Validate spice level with dietary restrictions
        spice_level = data.get('spice_level')
        if spice_level == 'very_hot' and is_vegan:
            # Warning: very hot vegan food might be unusual
            pass  # Allow but could add warning
    
    def create(self, validated_data):
        """Create food item with comprehensive validation and error handling"""
        # Debug logging to see what ingredients we received
        print(f"DEBUG: Creating food with validated_data ingredients: {validated_data.get('ingredients')}")
        print(f"DEBUG: Ingredients type: {type(validated_data.get('ingredients'))}")
        print(f"DEBUG: Image in validated_data: {validated_data.get('image')}")
        
        try:
            # Extract price data
            price = validated_data.pop('price')
            size = validated_data.pop('size', 'Medium')
            prep_time = validated_data.pop('preparation_time', 15)
            
            # Handle image - it should be a Cloudinary URL now from validate_image
            image_url = validated_data.pop('image', None)
            
            # Set status to pending and assign chef
            validated_data['status'] = 'Pending'
            validated_data['chef'] = self.context['request'].user
            
            # Set the image URL if we have one
            if image_url:
                validated_data['image'] = image_url
            
            # Ensure ingredients is properly formatted
            if 'ingredients' not in validated_data:
                validated_data['ingredients'] = []
            
            # Final validation before creation
            self._final_validation_before_create(validated_data, price, size, prep_time)
            
            # Create food item
            food = super().create(validated_data)
            
            # Create initial price entry
            FoodPrice.objects.create(
                food=food,
                size=size,
                price=price,
                preparation_time=prep_time,
                cook=self.context['request'].user
            )
            
            print(f"DEBUG: Successfully created food item: {food.name} (ID: {food.food_id})")
            return food
            
        except Exception as e:
            print(f"ERROR: Failed to create food item: {str(e)}")
            raise serializers.ValidationError(f"Failed to create food item: {str(e)}")
    
    def _final_validation_before_create(self, validated_data, price, size, prep_time):
        """Final validation before creating the food item"""
        # Validate that all required fields are present
        required_fields = ['name', 'description', 'category']
        for field in required_fields:
            if not validated_data.get(field):
                raise serializers.ValidationError(f"{field.title()} is required")
        
        # Validate price and size combination
        if price < 250 and size == 'Large':
            raise serializers.ValidationError(
                "Large size items should have a minimum price of LKR 250.00"
            )
        
        # Validate preparation time consistency
        if prep_time < 5:
            raise serializers.ValidationError(
                "Preparation time must be at least 5 minutes"
            )
        
        # Validate ingredients are not empty for certain categories
        category = validated_data.get('category', '').lower()
        ingredients = validated_data.get('ingredients', [])
        
        if category in ['main course', 'entree', 'dinner'] and not ingredients:
            raise serializers.ValidationError(
                "Main course items should include ingredients list"
            )


class FoodReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = FoodReview
        fields = [
            'review_id', 'rating', 'comment', 'customer', 'customer_name', 'taste_rating',
            'presentation_rating', 'value_rating', 'is_verified_purchase', 'helpful_votes',
            'created_at', 'updated_at'
        ]


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'