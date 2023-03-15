
from datetime import datetime
from xml.dom import ValidationErr
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
import math
from dateutil import relativedelta
from typing import Any, Dict, Optional
from django_extensions.db.models import TimeStampedModel
from inventorySAS.strategy import AdminStrategy, BuyStrategy, InventoryTransactionStrategy, ObsoleteStrategy, RemissionStrategy, DevolutionStrategy, RepositionStrategy, SellStrategy
from django.core import validators
from django.contrib.auth.models import User as UserDjango
from django.db import connection


class TenantManager(models.Manager):
    def get_queryset(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('glb.tenant_id', '%s', FALSE)", [0])
            query = super().get_queryset()
        return query


class Company(TimeStampedModel, models.Model):
    name = models.CharField(max_length=128, unique=True)
    subdomain = models.CharField(max_length=128, null=True, blank=True)
    nit = models.CharField(max_length=128)

    # representant = models.ForeignKey('Customer', on_delete=models.DO_NOTHING, null=True)
    # owner = models.ForeignKey('Customer', on_delete=models.DO_NOTHING, null=True, blank=True)
    # pricings = models.ManyToManyField('RentProduct', through='OrderRate')

    def __str__(self):
        return self.name


class Utils(TimeStampedModel, models.Model):
    # tenant = models.ForeignKey(
    #     'Company',
    #     on_delete=models.CASCADE,
    #     related_name='%(app_label)s_%(class)s_set',
    #     related_query_name='%(app_label)s_%(class)s',
    #     blank=True,
    #     null=True,
    # )

    # def __str__(self):
    #     return str(f'{self.pk} - {self.tenant}')

    def __str__(self):
        return str(f'{self.pk}')

    class Meta:
        abstract = True


class Tenant(models.Model):
    tenant = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        related_query_name='%(app_label)s_%(class)s',
    )
    objects = models.Manager()
    tenants = TenantManager()

    class Meta:
        abstract = True


class Product(Tenant, Utils):
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0, editable=False)
    weight = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )
    sell_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )
    reposition_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )
    buy_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )
    rent_price = models.ForeignKey(
        'Rent', on_delete=models.DO_NOTHING, default=1)  # type: ignore
    brand = models.CharField(max_length=255, blank=True, null=True)
    is_supply = models.BooleanField(default=True)
    unit = models.ForeignKey(
        'Unit', on_delete=models.DO_NOTHING, blank=True, null=True)
    type = models.ForeignKey('ProductType', on_delete=models.DO_NOTHING)
    supplies = models.ManyToManyField('self', through='ProductCompound', through_fields=(
        'compound_product', 'supply_product'))

    def __str__(self):
        return self.name


class Unit(Utils):
    name = models.CharField(max_length=255, default='unit')

    def __str__(self):
        return self.name


class ProductType(Utils):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ProductCompound(Tenant, Utils):
    compound_product = models.ForeignKey(
        'Product', on_delete=models.DO_NOTHING, related_name='compound_products')
    supply_product = models.ForeignKey(
        'Product', on_delete=models.DO_NOTHING, related_name='supply_products')
    quantity = models.IntegerField(
        validators=[validators.MinValueValidator(1)])

    class Meta:
        constraints = [models.UniqueConstraint(name='A supply cannot be in a compound product', fields=['compound_product', 'supply_product']), models.CheckConstraint(
            name='Inventory Transaction must have a quantity grater than 0', check=models.Q(quantity__gt=0))]

    def clean(self) -> None:
        if self.compound_product.id == self.supply_product.id:
            raise ValidationError('Product cannot be a supplied by itself')

        supply_count = self.supply_product.compound_products.filter(
            supply_product_id=self.compound_product.id).count()

        if supply_count != 0:
            raise ValidationError(
                f'{self.compound_product} is a supply of {self.supply_product}')

        return super().clean()

    def save(self, **kwargs):
        self.compound_product.is_supply = False
        self.compound_product.save()
        return super().save(**kwargs)


class TimeType(models.TextChoices):
    CALENDAR_DAY = 'CD', _('Día Calendario')
    MONTH = 'MO', _('Mes')
    HOUR = 'HO', _('Hora')
    AVAILABLE_DAY = 'AD', _('Día Hábil')
    WEEK = 'WE', _('Semana')


class RentProduct(Tenant, Utils):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    rent = models.ForeignKey('Rent', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.product} - {self.rent}'


class Rent(Tenant, Utils):
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )
    time = models.CharField(
        max_length=2,
        choices=TimeType.choices,
        default=TimeType.CALENDAR_DAY
    )
    minimun_time = models.IntegerField(
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(365)])

    products = models.ManyToManyField('Product', through='RentProduct')

    def __str__(self):
        return f'{self.value} / {self.time} ({self.minimun_time})'


class Inventory(Tenant, Utils):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE)
    quantity = models.IntegerField(
        validators=[validators.MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(name='Product and Warehouse must be unique', fields=[
                                    'product', 'warehouse']),
            models.CheckConstraint(
                name='Quantity must be greater than or equal 0', check=models.Q(quantity__gte=0)),
        ]


class Warehouse(Tenant, Utils):
    name = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    municipio = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    owner = models.ForeignKey('Customer', on_delete=models.DO_NOTHING)
    is_owned = models.BooleanField(default=False)

    def __str__(self):
        if self.is_owned:
            return self.name + ' (Dueño)'
        return self.name


class User(Tenant, Utils):
    class DocumentType(models.TextChoices):
        ID = 'ID', _('Cédula de ciudadanía')
        PASSPORT = 'PA', _('Pasaporte')
        IDENTITY_CARD = 'TI', _('Tarjeta de identidad')
        OTHER = 'OT', _('Otro')

    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    email = models.EmailField(_("email address"), blank=True)
    document_type = models.CharField(
        max_length=2,
        choices=DocumentType.choices,
        blank=True, null=True
    )
    document_number = models.CharField(max_length=30, blank=True, null=True)
    contact_phone = models.CharField(max_length=255, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True, validators=[
                              validators.MinValueValidator(15), validators.MaxValueValidator(150)])

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        abstract = True

    def __str__(self):
        return self.full_name


class Customer(User):
    discounts = models.ManyToManyField(
        'Discount', through='CustomerDiscount', through_fields=('customer', 'discount'))


class EmployeeManager(models.Manager):
    def save_with_user(self, username, password, **extrafields):
        user = UserDjango.objects.create_user(
            username=username, email=username, password=password, is_staff=True)
        self.model(**extrafields, auth_user=user).save()


class Employee(User):
    auth_user = models.OneToOneField(UserDjango, on_delete=models.CASCADE)
    objects = EmployeeManager()


class Provider(User):
    pass


class Vehicle(Tenant, Utils):
    plate = models.CharField(max_length=12)
    weight_transport = models.DecimalField(
        help_text='Weight in Kg',
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )
    brand = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.plate


class Transport(Tenant, Utils):
    driver = models.ForeignKey(
        'Employee', on_delete=models.DO_NOTHING, related_name='driver', blank=True, null=True)
    helper = models.ForeignKey(
        'Employee', on_delete=models.DO_NOTHING, related_name='helper', blank=True, null=True)
    weight_to_carry = models.DecimalField(
        help_text='Weight in Kg',
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )
    vehicle = models.ForeignKey('Vehicle', on_delete=models.DO_NOTHING)


class MovementType(models.TextChoices):
    DEVOLUTION = 'DE', _('DEVOLUCION')
    REMISSION = 'RE', _('REMISION')
    FABRICATION = 'FA', _('FABRICACION')
    BUY = 'BU', _('COMPRA')
    SELL = 'SE', _('VENTA')
    OBSOLETE = 'OB', _('OBSOLETO')
    ADMIN = 'AD', _('ADMIN')
    REPOSITION = 'RP', _('REPOSICION')


class InventoryTransaction(Tenant, Utils):
    inventory_transaction_strategies: Optional[Dict[str,
                                                    InventoryTransactionStrategy]] = None
    product = models.ForeignKey('Product', on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(
        validators=[validators.MinValueValidator(1)])
    transport = models.ForeignKey(
        'Transport', on_delete=models.DO_NOTHING, null=True, blank=True)
    order = models.ForeignKey('Order', on_delete=models.DO_NOTHING,
                              null=True, blank=True, related_name='inventory_transaction_set')
    date = models.DateTimeField(default=timezone.now)
    is_inbound = models.BooleanField(default=False, editable=False)
    movement_type = models.CharField(
        max_length=2,
        choices=MovementType.choices,
        default=MovementType.REMISSION,
    )
    origin = models.ForeignKey(
        'Warehouse', on_delete=models.DO_NOTHING, related_name='origins', null=True, blank=True)
    destination = models.ForeignKey(
        'Warehouse', on_delete=models.DO_NOTHING, related_name='destinations', null=True, blank=True)

    class Meta:
        constraints = [models.CheckConstraint(
            name='Inventory Transaction must have a quantity grater than or equal 0', check=models.Q(quantity__gte=0))]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.inventory_transaction_strategies = {
            MovementType.DEVOLUTION: DevolutionStrategy(inventory_transaction=self),
            MovementType.REMISSION: RemissionStrategy(inventory_transaction=self),
            MovementType.SELL: SellStrategy(inventory_transaction=self),
            MovementType.BUY: BuyStrategy(inventory_transaction=self),
            MovementType.OBSOLETE: ObsoleteStrategy(inventory_transaction=self),
            MovementType.ADMIN: AdminStrategy(inventory_transaction=self),
            MovementType.REPOSITION: RepositionStrategy(
                inventory_transaction=self)
        }
        super().__init__(*args, **kwargs)

    def clean(self) -> None:
        if self.inventory_transaction_strategies is None:
            raise ValidationErr(
                _('__init__ did not load the strategies'),
                code='Internal error',
            )
        self.inventory_transaction_strategies[self.movement_type].clean()
        return super().clean()

    def save(self, *args, **kwargs):
        if self.order is not None and self.order.is_close:
            raise ValidationError(
                _('The order is close and transactions are no longer possible for the order'))
        if self.pk is not None:
            raise ValidationError(
                _('You cannot update an already existing transaction'))
        if self.inventory_transaction_strategies is None:
            raise ValidationErr(
                _('__init__ did not load the strategies'),
                code='Internal error',
            )
        selected_strategy = self.inventory_transaction_strategies[self.movement_type]
        selected_strategy.execute_inventory_movement(
        )
        selected_strategy.execute_product_movement(
        )
        super().save(*args, **kwargs)

        selected_strategy.execute_order_items()


class OutboundTransaction(Tenant, Utils):
    outbound_transaction = models.OneToOneField(
        'InventoryTransaction', on_delete=models.DO_NOTHING, primary_key=True)
    order = models.ForeignKey('Order', on_delete=models.DO_NOTHING)
    quantity_left = models.IntegerField()

    class Meta:
        constraints = [models.CheckConstraint(
            name='Outbound Transaction must have quantity_left grater than or equal 0', check=models.Q(quantity_left__gte=0))]


class Order(Tenant, Utils):
    billing = models.ForeignKey(
        'Billing', on_delete=models.DO_NOTHING, null=True)
    rent_pricings = models.ManyToManyField(RentProduct, through='OrderRate')
    is_close = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_close:
            self.is_close = False
            remaining_transactions = self.outboundtransaction_set.filter(  # type: ignore
                quantity_left__gt=0)
            for remaining_transaction in remaining_transactions:
                outbound_transaction = remaining_transaction.outbound_transaction
                inv_trans = InventoryTransaction(
                    product=outbound_transaction.product,
                    quantity=remaining_transaction.quantity_left,
                    transport=outbound_transaction.transport,
                    order=self,
                    movement_type=MovementType.REPOSITION,
                    origin=outbound_transaction.destination,
                    destination=outbound_transaction.origin,
                    tenant=outbound_transaction.tenant,
                )
                inv_trans.full_clean()
                inv_trans.save()
            self.is_close = True
        return super().save(*args, **kwargs)


class OrderRate(Tenant, Utils):
    order = models.ForeignKey('Order', on_delete=models.DO_NOTHING)
    rent = models.ForeignKey('RentProduct', on_delete=models.DO_NOTHING)

    def clean(self) -> None:

        product_count = OrderRate.objects.filter(
            order=self.order, rent__product__pk=self.rent.product.pk).count()

        if product_count > 0:
            raise ValidationError(
                _('An order should only have one product rate'))
        return super().clean()


class InvoiceItemType(models.TextChoices):
    BUY = 'BU', _('Compra')
    SELL = 'SE', _('Venta')
    REPOSITION = 'RE', _('Reposición')
    TRANSPORT = 'TA', _('Transporte')


class InvoiceItem(Tenant, Utils):
    order = models.ForeignKey('Order', on_delete=models.DO_NOTHING)
    inventory_transaction = models.ForeignKey(
        'InventoryTransaction', on_delete=models.DO_NOTHING)
    date = models.DateTimeField()
    item_name = models.CharField(max_length=255)
    quantity = models.IntegerField(
        validators=[validators.MinValueValidator(0)], default=0)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(1),
        ]
    )
    order_item_type = models.CharField(
        max_length=2, choices=InvoiceItemType.choices, default=InvoiceItemType.BUY)
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(1),
        ]
    )


class InvoiceTransaction(Tenant, Utils):
    outbound = models.ForeignKey(
        'OutboundTransaction', related_name='outbound_order_transaction', on_delete=models.DO_NOTHING)
    inbound_inventory = models.ForeignKey(
        'InventoryTransaction', related_name='inbound_order_transaction', on_delete=models.DO_NOTHING)
    product = models.ForeignKey('Product', on_delete=models.DO_NOTHING)
    order = models.ForeignKey('Order', on_delete=models.DO_NOTHING)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    quantity = models.IntegerField(
        validators=[validators.MinValueValidator(1)])
    period = models.IntegerField(validators=[validators.MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(1),
        ]
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(1),
        ]
    )

    def save(self, *args, **kwargs):
        if self.start_date > self.end_date:
            raise ValidationError(
                _('Start date cannot be greater than End date'))

        rent_product = None
        try:
            rent_product = self.order.rent_pricings.get(
                product=self.product).rent
        except:
            if not self.product.rent_price:
                ValidationError(_('There is no rent price for the product'))
            rent_product = self.product.rent_price

        def get_period_by_time(time, start_date, end_date):
            delta = end_date - start_date
            month_delta = relativedelta.relativedelta(end_date, start_date)
            return {
                TimeType.HOUR: 0,
                TimeType.AVAILABLE_DAY: delta.days + 1,
                TimeType.CALENDAR_DAY: delta.days + 1,
                TimeType.WEEK: (math.ceil(delta.days + 1))/7,
                TimeType.MONTH: month_delta.months if month_delta.days + 1 < 30 else month_delta.months + 1,
            }[time]

        self.period = max(get_period_by_time(
            rent_product.time, self.start_date, self.end_date), rent_product.minimun_time)
        self.price = rent_product.value
        self.total = self.period * self.price * self.quantity
        return super().save(*args, **kwargs)


class Billing(Tenant, Utils):
    is_paid = models.BooleanField(default=False)
    company = models.ForeignKey(
        'Company', on_delete=models.DO_NOTHING, null=True)
    customer = models.ForeignKey(
        'Customer', on_delete=models.DO_NOTHING, null=True)
    due_date = models.DateTimeField()
    tax_percentage = models.DecimalField(blank=True,
                                         null=True,
                                         max_digits=3,
                                         decimal_places=2,
                                         validators=[
                                             validators.MinValueValidator(0)]
                                         )
    total = models.DecimalField(
        blank=True,
        null=True,
        max_digits=12,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(1),
        ]
    )


class Discount(Tenant, Utils):
    title = models.TextField()
    description = models.TextField()
    product_type = models.ForeignKey(
        'ProductType', on_delete=models.DO_NOTHING)
    percentage = models.DecimalField(
        blank=True,
        null=True,
        max_digits=3,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
        ]
    )


class CustomerDiscount(Tenant, Utils):
    customer = models.ForeignKey('Customer', on_delete=models.DO_NOTHING)
    discount = models.ForeignKey('Discount', on_delete=models.DO_NOTHING)
    order = models.ForeignKey(
        'Order', on_delete=models.DO_NOTHING, null=True, blank=True)

    def save(self, **kwargs):
        order_count = self.customer.billing_set.filter(
            order=self.order).count()
        if self.order is not None and order_count == 0:
            raise ValidationError('The order does not belong to the customer')

        return super().save(**kwargs)
