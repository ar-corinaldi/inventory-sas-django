from functools import reduce
from inventorySAS import models as mo
from inventorySAS import serializers as se
from rest_framework import viewsets, decorators, status
from django.contrib import messages
from django.template.loader import get_template
import pdfkit
from django.http import HttpResponse, HttpResponseBadRequest
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class BillingViewSet(viewsets.ModelViewSet):
    queryset = mo.Billing.objects.all()
    serializer_class = se.BillingSerializer

    @decorators.action(methods=['GET'], detail=True)
    def generate_pdf(self, request, pk):
        try:
            invoice = mo.Billing.objects.get(pk=pk)
            ser_invoice = se.BillingSerializer(invoice).data
        except:
            messages.error(request, 'something went wrong')
            return HttpResponse({'status': 'The invoice does not exist'})

        orders = invoice.order_set.all()
        # TODO: invoice_items = orders.orderitem_set.all()
        invoice_transactions = [
            invoice_transaction for order in orders for invoice_transaction in order.ordertransaction_set.all()]
        invoice_items = [
            invoice_item for order in orders for invoice_item in order.orderitem_set.all()]

        ser_invoice_transactions = se.OrderTransactionSerializer(
            invoice_transactions, many=True).data
        ser_invoice_items = se.OrderItemSerializer(
            invoice_items, many=True).data

        customer_warehouses = invoice.customer.warehouse_set.filter(
            is_owned=False)

        context = {}
        context['invoice'] = ser_invoice
        total_invoice = reduce(
            lambda x, y: x + y, [float(pair['total']) for pair in ser_invoice_transactions])
        total_others = reduce(
            lambda x, y: x + y, [float(pair['total']) for pair in ser_invoice_items])
        context['invoice_transactions'] = ser_invoice_transactions
        context['invoice_items'] = ser_invoice_items
        context['total_invoice_items'] = total_others
        context['total_invoice_transactions'] = total_invoice
        context['total'] = total_invoice + total_others

        filename = '{}.pdf'.format(f'invoice-{invoice.pk}')

        # HTML FIle to be converted to PDF - inside your Django directory
        template = get_template('invoice.html')
        html = template.render(context)

        # TODO: Will this change in linux server?
        path_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        # template_folder = os.path.join(Path(__file__).resolve().parent, 'templates')
        # static_folder = os.path.join(Path(__file__).resolve().parent, 'static')
        # Options - Very Important [Don't forget this]
        options = {
            'encoding': 'UTF-8',
            'javascript-delay': '10',  # Optional
            'enable-local-file-access': None,  # To be able to access CSS
            'page-size': 'Letter',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
        }
        # Javascript delay is optional
        file_content = pdfkit.from_string(
            html, False, configuration=config, options=options, verbose=True)

        response = HttpResponse(file_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename = {}'.format(
            filename)

        # Return
        return response


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = mo.Customer.objects.all()
    serializer_class = se.CustomerSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = mo.Employee.objects.all()
    serializer_class = se.EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        tenant_id = request.tenant_id
        data = request.body
        data_dict = json.loads(data.decode("utf-8"))
        data_dict['tenant_id'] = tenant_id
        if data_dict['password'] != data_dict['confirmPassword']:
            return HttpResponseBadRequest({'success': False, })

        del data_dict['confirmPassword']
        employee = se.EmployeeSerializer(data=data_dict).data
        mo.Employee.objects.save_with_user(**data_dict)
        return Response(employee)

    @decorators.action(methods=['GET'], detail=False)
    def retrieve_user(self, request):
        auth_user = request.user
        employee = mo.Employee.objects.get(auth_user=auth_user)
        employee_ser = se.EmployeeSerializer(employee).data
        return Response(employee_ser)


class InventoryTransactionViewSet(viewsets.ModelViewSet):
    queryset = mo.InventoryTransaction.objects.all()
    serializer_class = se.InventoryTransactionSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = mo.Order.objects.all()
    serializer_class = se.OrderSerializer


class OrderTransactionViewSet(viewsets.ModelViewSet):
    queryset = mo.InvoiceTransaction.objects.all()
    serializer_class = se.OrderTransactionSerializer


class OutboundTransactionViewSet(viewsets.ModelViewSet):
    queryset = mo.OutboundTransaction.objects.all()
    serializer_class = se.OutboundTransactionSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = mo.Product.objects.get_queryset()
    serializer_class = se.ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return mo.Product.objects.get_queryset()

    def create(self, request):
        tenant_id = request.tenant_id
        data = request.body
        data_dict = json.loads(data.decode("utf-8"))
        data_dict['tenant_id'] = tenant_id
        rent = data_dict['rent_price']
        rent['tenant_id'] = tenant_id
        rent_mo = mo.Rent(**rent)
        rent_mo.save()

        data_dict['rent_price'] = rent_mo
        product_mo = mo.Product(**data_dict)
        product_mo.save()
        product = se.ProductSerializer(product_mo).data
        return Response(product)


class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = mo.ProductType.objects.all()
    serializer_class = se.ProductTypeSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        queryset = mo.ProductType.objects.all()
        name = self.request.query_params.get('name')  # type: ignore

        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        if not name:
            queryset = queryset.all()[:5]
        return queryset


class ProviderViewSet(viewsets.ModelViewSet):
    queryset = mo.Provider.objects.all()
    serializer_class = se.ProviderSerializer


class RentProductViewSet(viewsets.ModelViewSet):
    queryset = mo.RentProduct.objects.all()
    serializer_class = se.RentProductSerializer


class TransportViewSet(viewsets.ModelViewSet):
    queryset = mo.Transport.objects.all()
    serializer_class = se.TransportSerializer


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = mo.Warehouse.objects.all()
    serializer_class = se.WarehouseSerializer

    def create(self, request, *args, **kwargs):
        request.data['tenant_id'] = request.tenant_id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(**request.data)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = mo.Company.objects.all()
    serializer_class = se.CompanySerializer
