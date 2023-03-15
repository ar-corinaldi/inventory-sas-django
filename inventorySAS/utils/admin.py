from django.contrib import admin
from inventorySAS.models import RentProduct

class RentProductInline(admin.TabularInline):
    model = RentProduct

class ProductAbstract(admin.ModelAdmin):
    inlines = [RentProductInline]
    exclude = ['is_supply']

class CompanyAbstract(admin.ModelAdmin):
    inlines = [RentProductInline]
    exclude = ['is_supply']