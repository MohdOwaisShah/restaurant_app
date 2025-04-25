from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class AddOn(models.Model):
    food_item = models.ForeignKey('FoodItem', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} - {self.food_item.name}"

class Category(models.Model):
    name = models.CharField(max_length=255)
    #image = models.ImageField(upload_to='categories/', blank=True, null=True)  # ✅ Add this if missing
    image = models.ImageField(upload_to='categories/', default='categories/default.jpg')

    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class FoodItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_vegetarian = models.BooleanField(default=False)
    image = models.ImageField(upload_to='food_items/', null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
class CustomizationGroup(models.Model):
    name = models.CharField(max_length=100)
    max_choices = models.IntegerField(default=1)

    def __str__(self):
        return self.name

class CustomizationOption(models.Model):
    group = models.ForeignKey(CustomizationGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.group.name} - {self.name}"

class CartItem(models.Model):
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    session_id = models.CharField(max_length=100)  # To track anonymous users
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return self.food_item.price * self.quantity
    

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    cart_id = models.CharField(max_length=100, blank=True, null=True)
    food_item = models.ForeignKey('FoodItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return self.food_item.price * self.quantity

    def __str__(self):
        return f"Cart {self.cart_id} - {self.food_item.name}"
    

class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    current_table = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - Table {self.current_table}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_item = models.ForeignKey('FoodItem', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=50, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # New field
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)  # New field
    payment_status = models.CharField(max_length=50, default='Pending')  # New field
    
    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, null=True, blank=True)  # Allow null and blank values
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    table_number = models.CharField(max_length=10, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Transaction {self.id} - {self.user.email}"
    
class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)
    food_item = models.ForeignKey('FoodItem', on_delete=models.SET_NULL, null=True)  # Changed from menu_item to food_item
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    item_name = models.CharField(max_length=255)  # Store name in case food item is deleted

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"
    

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


