#!/usr/bin/env python
"""
Create sample subscription plans
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from auth_billing.models import Plan

# Create sample plans
plans_data = [
    {
        'name': 'Basic',
        'slug': 'basic',
        'description': 'Perfect for individuals getting started',
        'price': 9.99,
        'billing_cycle': 'monthly',
        'features': {
            'AI Image Generation': '100 images/month',
            'Image Resolution': 'Up to 1024x1024',
            'Storage': '1 GB',
            'Priority Support': 'Email only'
        },
        'max_users': 1,
        'max_storage_gb': 1,
        'is_active': True,
        'is_popular': False,
        'sort_order': 1
    },
    {
        'name': 'Professional',
        'slug': 'professional',
        'description': 'Best for creative professionals',
        'price': 29.99,
        'billing_cycle': 'monthly',
        'features': {
            'AI Image Generation': '500 images/month',
            'Image Resolution': 'Up to 2048x2048',
            'Storage': '10 GB',
            'Priority Support': 'Email & Chat',
            'Advanced Features': 'Style transfer, upscaling'
        },
        'max_users': 3,
        'max_storage_gb': 10,
        'is_active': True,
        'is_popular': True,
        'sort_order': 2
    },
    {
        'name': 'Enterprise',
        'slug': 'enterprise',
        'description': 'For teams and organizations',
        'price': 99.99,
        'billing_cycle': 'monthly',
        'features': {
            'AI Image Generation': 'Unlimited',
            'Image Resolution': 'Up to 4096x4096',
            'Storage': '100 GB',
            'Priority Support': '24/7 Phone & Chat',
            'Advanced Features': 'All features included',
            'API Access': 'Full API access',
            'Custom Models': 'Train custom models'
        },
        'max_users': 10,
        'max_storage_gb': 100,
        'is_active': True,
        'is_popular': False,
        'sort_order': 3
    }
]

created_count = 0
for plan_data in plans_data:
    plan, created = Plan.objects.get_or_create(
        slug=plan_data['slug'],
        defaults=plan_data
    )
    if created:
        created_count += 1
        print(f"✓ Created plan: {plan.name} - ${plan.price}/{plan.billing_cycle}")
    else:
        print(f"• Plan already exists: {plan.name}")

print(f"\n{'='*50}")
print(f"Total plans created: {created_count}")
print(f"Total plans in database: {Plan.objects.count()}")
print(f"{'='*50}")
