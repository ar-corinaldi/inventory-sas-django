# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Company, Product, Unit, ProductType, ProductCompound, RentProduct, Rent, Inventory, Warehouse, Customer, Employee, Provider, Vehicle, Transport, InventoryTransaction, OutboundTransaction, Order, OrderRate, InvoiceItem, InvoiceTransaction, Billing, Discount, CustomerDiscount


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'modified', 'name', 'subdomain', 'nit')
    list_filter = ('created', 'modified')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'name',
        'quantity',
        'weight',
        'sell_price',
        'reposition_price',
        'buy_price',
        'rent_price',
        'brand',
        'is_supply',
        'unit',
        'type',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'rent_price',
        'is_supply',
        'unit',
        'type',
    )
    raw_id_fields = ('supplies',)
    search_fields = ('name',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'modified', 'name')
    list_filter = ('created', 'modified')
    search_fields = ('name',)


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'modified', 'name')
    list_filter = ('created', 'modified')
    search_fields = ('name',)


@admin.register(ProductCompound)
class ProductCompoundAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'compound_product',
        'supply_product',
        'quantity',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'compound_product',
        'supply_product',
    )


@admin.register(RentProduct)
class RentProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'modified', 'tenant', 'product', 'rent')
    list_filter = ('created', 'modified', 'tenant', 'product', 'rent')


@admin.register(Rent)
class RentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'value',
        'time',
        'minimun_time',
    )
    list_filter = ('created', 'modified', 'tenant')
    raw_id_fields = ('products',)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'product',
        'warehouse',
        'quantity',
    )
    list_filter = ('created', 'modified', 'tenant', 'product', 'warehouse')


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'name',
        'contact_phone',
        'address',
        'municipio',
        'city',
        'department',
        'country',
        'owner',
        'is_owned',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'owner',
        'is_owned',
    )
    search_fields = ('name',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'first_name',
        'last_name',
        'email',
        'document_type',
        'document_number',
        'contact_phone',
        'age',
    )
    list_filter = ('created', 'modified', 'tenant')
    raw_id_fields = ('discounts',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'first_name',
        'last_name',
        'email',
        'document_type',
        'document_number',
        'contact_phone',
        'age',
        'auth_user',
    )
    list_filter = ('created', 'modified', 'tenant', 'auth_user')


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'first_name',
        'last_name',
        'email',
        'document_type',
        'document_number',
        'contact_phone',
        'age',
    )
    list_filter = ('created', 'modified', 'tenant')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'plate',
        'weight_transport',
        'brand',
        'model',
        'color',
    )
    list_filter = ('created', 'modified', 'tenant')


@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'driver',
        'helper',
        'weight_to_carry',
        'price',
        'vehicle',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'driver',
        'helper',
        'vehicle',
    )


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'product',
        'quantity',
        'transport',
        'order',
        'date',
        'is_inbound',
        'movement_type',
        'origin',
        'destination',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'product',
        'transport',
        'order',
        'date',
        'is_inbound',
        'origin',
        'destination',
    )


@admin.register(OutboundTransaction)
class OutboundTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'created',
        'modified',
        'tenant',
        'outbound_transaction',
        'order',
        'quantity_left',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'outbound_transaction',
        'order',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'billing',
        'is_close',
    )
    list_filter = ('created', 'modified', 'tenant', 'billing', 'is_close')
    raw_id_fields = ('rent_pricings',)


@admin.register(OrderRate)
class OrderRateAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'modified', 'tenant', 'order', 'rent')
    list_filter = ('created', 'modified', 'tenant', 'order', 'rent')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'order',
        'inventory_transaction',
        'date',
        'item_name',
        'quantity',
        'price',
        'order_item_type',
        'total',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'order',
        'inventory_transaction',
        'date',
    )


@admin.register(InvoiceTransaction)
class InvoiceTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'outbound',
        'inbound_inventory',
        'product',
        'order',
        'start_date',
        'end_date',
        'quantity',
        'period',
        'price',
        'total',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'outbound',
        'inbound_inventory',
        'product',
        'order',
        'start_date',
        'end_date',
    )


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'is_paid',
        'company',
        'due_date',
        'tax_percentage',
        'total',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'is_paid',
        'company',
        'due_date',
    )


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'title',
        'description',
        'product_type',
        'percentage',
    )
    list_filter = ('created', 'modified', 'tenant', 'product_type')


@admin.register(CustomerDiscount)
class CustomerDiscountAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'tenant',
        'customer',
        'discount',
        'order',
    )
    list_filter = (
        'created',
        'modified',
        'tenant',
        'customer',
        'discount',
        'order',
    )
