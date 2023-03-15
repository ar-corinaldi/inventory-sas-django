from rest_framework import serializers
from inventorySAS import models, serializers as se


class BillingSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Billing
        fields = '__all__'
        depth = 1


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Employee
        fields = '__all__'
        depth = 1


class InventoryTransactionSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format="%d-%m-%Y")

    class Meta:
        model = models.InventoryTransaction
        fields = '__all__'
        depth = 1


class OrderSerializer(serializers.ModelSerializer):
    inventory_transaction_set = InventoryTransactionSerializer(
        many=True, read_only=True)

    class Meta:
        model = models.Order
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%d-%m-%Y")  # type: ignore

    class Meta:
        model = models.InvoiceItem
        fields = '__all__'


class OrderTransactionSerializer(serializers.ModelSerializer):
    start_date = serializers.DateTimeField(format="%d-%m-%Y")  # type: ignore
    end_date = serializers.DateTimeField(format="%d-%m-%Y")  # type: ignore

    class Meta:
        model = models.InvoiceTransaction
        fields = ['id', 'created', 'start_date', 'end_date',
                  'quantity', 'period', 'price', 'total', 'product']
        depth = 1


class OutboundTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OutboundTransaction
        fields = '__all__'


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductType
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    type = ProductTypeSerializer(read_only=True)

    class Meta:
        model = models.Product
        fields = '__all__'


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Provider
        fields = '__all__'


class RentProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RentProduct
        fields = '__all__'


class TransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Transport
        fields = '__all__'


class WarehouseSerializer(serializers.ModelSerializer):
    inventory_set = InventoryTransactionSerializer(many=True, required=False)
    tenant_id = serializers.PrimaryKeyRelatedField(read_only=True)
    origins = InventoryTransactionSerializer(many=True, required=False)
    destinations = InventoryTransactionSerializer(many=True, required=False)

    # def save(self, **kwargs):
    #     print('kwargsss', **kwargs)
    #     return super().save(**kwargs)

    class Meta:
        model = models.Warehouse
        fields = '__all__'
        depth = 1


class CompanySerializer(serializers.ModelSerializer):
    warehouse_set = WarehouseSerializer(many=True)

    class Meta:
        model = models.Company
        fields = '__all__'
