# Generated by Django 5.1.4 on 2025-03-21 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_items', '0018_alter_fooditem_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='categories/'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='fooditem',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='food_items/'),
        ),
    ]
