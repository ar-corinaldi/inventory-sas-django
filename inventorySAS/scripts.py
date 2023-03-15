import pandas as pd
import os
from pathlib import Path
import math
# os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# from settings import *
# from django.conf import settings
# BASE_DIR = Path(__file__).resolve().parent.parent
# print(BASE_DIR)
# settings.configure(
#     DATABASE_ENGINE = 'django.db.backends.sqlite3',
#     DATABASE_NAME = BASE_DIR / 'db.sqlite3',
#     TIME_ZONE = 'America/Bogota',
# )
from inventorySAS.models import *
# from django.conf import settings
# import django.conf.global_settings
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventorySAS.settings")
# django.setup()

path = Path(os.getcwd())
folder = os.path.join(path.parent.absolute(), 'EquiposARCO')
filename = os.path.join(folder, 'ARTICULOS INVENTARIO.csv')

def transform_products(file):
    dt = pd.read_csv(file)

    product_type_arr = dt['GRUPO'].unique()
    product_type_dict = get_dict_with_ids(product_type_arr)
    dt_type = pd.DataFrame(data={'name': product_type_arr})
    dt_type.to_csv(os.path.join(folder, 'product_types.csv'))
    
    product_unit_arr = dt['UNIDAD'].unique()
    unit_dict = get_dict_with_ids(product_unit_arr)
    dt_unit = pd.DataFrame(data={'name': product_unit_arr})
    dt_unit.to_csv(os.path.join(folder, 'product_units.csv'))

    rent_arr = []
    rent_dict = {}
    for i in range(len(dt['PRECIO ALQUILER'].unique())):
        rent = dt['PRECIO ALQUILER'].unique()[i]
        rent = rent.replace(',', '') if type(rent) is str else '0'
        if rent and not math.isnan(float(rent)):
            row = [float(rent), 'CD', 7]
            rent_dict[float(rent)] = i+1
            rent_arr.append(row)

    dt_rent = pd.DataFrame(rent_arr, columns=['value', 'time', 'minimun_time'])
    dt_rent.to_csv(os.path.join(folder, 'rents.csv'))
    
    '''
    ['NOMBRE','UNIDAD','PRECIO REPOSICION',]

    ['name','quantity','weight','sell_price','reposition_price','buy_price','rent_price','unit','type']

    '''
    product_arr = []
    for i, row in dt.iterrows():
        
        parsed_rent_price = parse_to_float(row['PRECIO ALQUILER'])
        id_rent_price = rent_dict[parsed_rent_price] if parsed_rent_price in rent_dict else 1

        name = row['NOMBRE']
        quantity = 0
        weight = 0
        sell_price = parse_to_float(row['PRECIO REPOSICION'])
        reposition_price = parse_to_float(row['PRECIO REPOSICION'])
        buy_price = parse_to_float(row['PRECIO REPOSICION'])
        rent_price = id_rent_price
        unit = unit_dict[row['UNIDAD']]
        product_type = product_type_dict[row['GRUPO']]
        product_arr.append([name, quantity, weight, sell_price, reposition_price, buy_price, rent_price, unit, product_type])
    
    dt_products = pd.DataFrame(product_arr, columns=['name','quantity','weight','sell_price','reposition_price','buy_price','rent_price','unit','type'])
    dt_products.to_csv(os.path.join(folder, 'products.csv'))
    
def  get_dict_with_ids(arr):
    dicty = {}
    for i in range(len(arr)):
        element = arr[i]
        dicty[element] = i+1
    
    return dicty

def parse_to_float(s):
    normalize_s = s.replace(',', '') if type(s) is str else '0'
    return float(normalize_s)
    


# transform_products(filename)


# Necesary to run on shell_plus django
def execute_products_import():
    file = os.path.join(folder, 'error_products.csv')
    df = pd.read_csv(file)
    rent_min_pk = Rent.objects.aggregate(Min('id'))['id__min']
    unit_min_pk = Unit.objects.aggregate(Min('id'))['id__min']
    type_min_pk = ProductType.objects.aggregate(Min('id'))['id__min']
    error_arr = []
    for p_pandas in df.iterrows():
        p = p_pandas[1]
        try:
            print(p[7], rent_min_pk, rent_min_pk-1+p[7])
            r = Rent.objects.get(pk=rent_min_pk-1+p[7])
            u = Unit.objects.get(pk=unit_min_pk-1+p[8])
            t = ProductType.objects.get(pk=type_min_pk-1+p[9])
            Product(
                name=p[1],
                quantity=p[2],
                weight=p[3],
                sell_price=p[4],
                reposition_price=p[5],
                buy_price=p[6],
                rent_price=r,
                unit=u,
                type=t
            ).save()
        except Exception as err:
            print(repr(err))
            error_arr.append(p[1:])

    pd.DataFrame(error_arr).to_csv(os.path.join(folder, 'error_products.csv'))
execute_products_import()