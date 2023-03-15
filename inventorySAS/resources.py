from import_export import resources
from inventorySAS.models import *

from import_export.admin import ImportExportModelAdmin
class ProductResource(resources.ModelResource):

    class Meta:
        model = Product
        fields = ('id', 'name', 'quantity', 'weight','sell_price','reposition_price','buy_price','rent_price', 'unit', 'type')
        use_natural_foreign_keys = True

class ProductTypeResource(resources.ModelResource):

    class Meta:
        model = ProductType
        fields = ('id','name')

class ProductUnitResource(resources.ModelResource):

    class Meta:
        model = Unit
        fields = ('id','name')

class RentResource(resources.ModelResource):

    class Meta:
        model = Rent
        fields = (
        'id',
        'value',
        'time',
        'minimun_time',
    )


class ProductResourceAdmin(ImportExportModelAdmin):
    resource_classes = [ProductResource]

class ProductTypeResourceAdmin(ImportExportModelAdmin):
    resource_classes = [ProductTypeResource]

class ProductUnitResourceAdmin(ImportExportModelAdmin):
    resource_classes = [ProductUnitResource]

class RentResourceAdmin(ImportExportModelAdmin):
    resource_classes = [RentResource]