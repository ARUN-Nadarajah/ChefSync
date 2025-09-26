#!/usr/bin/env python
"""
Script to check which models are registered in Django admin
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.contrib import admin

def main():
    print("=" * 80)
    print("DJANGO ADMIN MODELS REGISTRATION CHECK")
    print("=" * 80)
    
    # Get all model classes
    all_models = []
    for app_config in apps.get_app_configs():
        if app_config.name.startswith('apps.'):
            for model in app_config.get_models():
                all_models.append(model)
    
    print(f"\nTotal models found: {len(all_models)}")
    print("\n" + "-" * 80)
    
    registered_models = []
    unregistered_models = []
    
    for model in all_models:
        if model in admin.site._registry:
            registered_models.append(model)
        else:
            unregistered_models.append(model)
    
    # Display registered models
    print(f"\n✅ REGISTERED MODELS ({len(registered_models)}):")
    print("-" * 40)
    for model in sorted(registered_models, key=lambda x: f"{x._meta.app_label}.{x.__name__}"):
        admin_class = admin.site._registry[model]
        print(f"  ✓ {model._meta.app_label}.{model.__name__} -> {admin_class.__class__.__name__}")
    
    # Display unregistered models
    if unregistered_models:
        print(f"\n❌ UNREGISTERED MODELS ({len(unregistered_models)}):")
        print("-" * 40)
        for model in sorted(unregistered_models, key=lambda x: f"{x._meta.app_label}.{x.__name__}"):
            print(f"  ✗ {model._meta.app_label}.{model.__name__}")
    else:
        print(f"\n🎉 ALL MODELS ARE REGISTERED!")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"  Total Models: {len(all_models)}")
    print(f"  Registered: {len(registered_models)}")
    print(f"  Unregistered: {len(unregistered_models)}")
    print(f"  Coverage: {(len(registered_models)/len(all_models)*100):.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()