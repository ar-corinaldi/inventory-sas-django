import pandas as pd
import os
from pathlib import Path

path = Path(os.getcwd())
folder = os.path.join(path.parent.absolute(), 'EquiposARCO')
file = os.path.join(folder, 'remisiones-y-reintegros-noviembre.csv')

new_line = ',,,,,,,,'
rents_arr = []
with open(file) as f:
    line = f.readline().strip()
    rent_info = None
    while line != '':
        prev_rent_info = rent_info
        rent_info = line.split(',')
        if rent_info[1] == 'ARTíCULO':

            '''
            [prev_rent_info[0], prev_rent_info[2], prev_rent_info[3], prev_rent_info[5], product_arr[2], product_arr[3], prduct_arr[1]]
            [movement_type, date, origin, destination, product, quantity,transport]
            '''
            product_str = f.readline().strip()
            
            while product_str != new_line and product_str != '':
                product_arr = product_str.split(',')
                print(prev_rent_info)
                movement_type = 'RE' if prev_rent_info[0] == 'RS' else 'DE'
                cur_rent = [movement_type, prev_rent_info[2], prev_rent_info[3], prev_rent_info[5], product_arr[2], product_arr[3]]
                
                if prduct_arr[1].startswith('VJ'):
                    cur_rent.append(product_arr[1])
                rents_arr.append(cur_rent)
                product_str = f.readline().strip()

            if product_str == new_line:
                f.readline().strip()

        line = f.readline().strip()


# dt = pd.DataFrame(rents_arr, columns=['movement_type', 'date', 'origin', 'destination', 'product', 'quantity','transport])
# dt.to_csv(os.path.join(folder, 'rents.csv'))