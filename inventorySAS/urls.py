from rest_framework import routers
from inventorySAS import views

router = routers.DefaultRouter()
router.register(r'billings', views.BillingViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'employees', views.EmployeeViewSet)
router.register(r'inventory-transactions', views.InventoryTransactionViewSet)
router.register(r'order-transactions', views.OrderTransactionViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'outbound-transactions', views.OutboundTransactionViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'product-types', views.ProductTypeViewSet)
router.register(r'rent-products', views.RentProductViewSet)
router.register(r'transports', views.TransportViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'providers', views.ProviderViewSet)
router.register(r'companies', views.CompanyViewSet)
