# Generated by Django 5.1.4 on 2025-03-21 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_items', '0019_category_image_alter_category_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='image',
            field=models.ImageField(default='categories/default.jpg', upload_to='categories/'),
        ),
    ]
