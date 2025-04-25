from django.contrib import admin
from unfold.admin import ModelAdmin  # Custom admin class
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.contrib import messages
import pandas as pd
from django.urls import path
from django.db import models

from .models import FoodItem, Category, Order, AddOn, CustomizationGroup, CustomizationOption
from .forms import ExcelImportForm
from .views import send_order_ready_email  # Import the function
from .models import Category
class AddOnInline(admin.TabularInline):
    model = AddOn
    extra = 1  # Number of blank rows to show

# ✅ Fixed CategoryAdmin
class CategoryAdmin(ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'image_preview')  # Ensure image_preview exists
    fields = ('name','image', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html('<img src="{}" width="100" height="70" style="border-radius: 5px;" />', obj.image.url)
        return "(No Image)"

    image_preview.short_description = 'Image Preview'

# ✅ FoodItemAdmin
class FoodItemAdmin(ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_vegetarian', 'image_tag')
    search_fields = ['name', 'category__name']
    readonly_fields = ('image_tag',)
    fields = ('name', 'price', 'description', 'category', 'is_vegetarian', 'image', 'image_tag', 'stock_quantity')
    change_list_template = 'admin/food_items_changelist.html'
    autocomplete_fields = ['category']
    inlines = [AddOnInline]

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:100px;"/>', obj.image.url)
        return "No Image"

    image_tag.short_description = 'Image Preview'

    # Custom admin URLs
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.import_excel, name='food_items_import_excel'),
        ]
        return custom_urls + urls

    # Import food items from an Excel file
    def import_excel(self, request):
        if request.method == 'POST':
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    excel_file = request.FILES['excel_file']
                    df = pd.read_excel(excel_file)

                    # Validate required columns
                    required_columns = ['name', 'description', 'price', 'category', 'is_vegetarian', 'stock_quantity']
                    if not all(col in df.columns for col in required_columns):
                        messages.error(request, 'Excel file is missing required columns')
                        return redirect('admin:food_items_fooditem_changelist')

                    # Create or update food items
                    for _, row in df.iterrows():
                        FoodItem.objects.update_or_create(
                            name=row['name'],
                            defaults={
                                'description': row.get('description', ''),
                                'price': row['price'],
                                'category': row.get('category', ''),
                                'is_vegetarian': row.get('is_vegetarian', False),
                                'stock_quantity': row.get('stock_quantity', 0)
                            }
                        )

                    messages.success(request, 'Excel file imported successfully')
                    return redirect('admin:food_items_fooditem_changelist')

                except Exception as e:
                    messages.error(request, f'Error importing file: {str(e)}')
                    return redirect('admin:food_items_fooditem_changelist')

        form = ExcelImportForm()
        return render(request, 'admin/import_excel.html', {'form': form})

# ✅ Register Models
admin.site.register(Category, CategoryAdmin)
admin.site.register(FoodItem, FoodItemAdmin)
admin.site.register(AddOn)
admin.site.register(CustomizationGroup)
admin.site.register(CustomizationOption)

# ✅ OrderAdmin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'food_item', 'quantity', 'status', 'created_at', 'payment_status')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__email', 'food_item__name', 'payment_id', 'razorpay_order_id')
    readonly_fields = ('payment_id', 'razorpay_order_id', 'created_at')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user', 'food_item', 'quantity')
        return self.readonly_fields

admin.site.register(Order, OrderAdmin)
