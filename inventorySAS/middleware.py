from django.db import connection
from django.contrib.auth.middleware import get_user
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Employee
from .serializers import EmployeeSerializer
import json


class RlsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = self.__class__.get_jwt_user(request)
        tenant_id = -1

        # user = self.__class__.get_jwt_user(request)
        if (user and user.is_authenticated and user.is_superuser and user.pk == 1):
            tenant_id = 0
        elif (user and user.is_authenticated):
            employee = Employee.objects.get(auth_user=user)
            employee_ser = EmployeeSerializer(employee).data
            if employee_ser.get('tenant', {'id': -1})['id']:
                tenant_id = employee_ser.get('tenant', {'id': -1})['id']

        request.tenant_id = tenant_id
        if hasattr(request, 'data'):
            print(request.data)
            data_dict = json.loads(request.data.decode("utf-8"))
            data_dict['tenant_id'] = tenant_id
            print('data_dict', data_dict)
            request.data = json.dumps(data_dict)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('glb.tenant_id', '%s', FALSE)", [tenant_id])

        response = self.get_response(request)
        return response

    @staticmethod
    def get_jwt_user(request):
        user = get_user(request)
        if user.is_authenticated:
            return user
        try:
            jwt_authentication = JWTAuthentication().authenticate(request)
            if not jwt_authentication:
                return None
            return jwt_authentication[0]
        except:
            return None
