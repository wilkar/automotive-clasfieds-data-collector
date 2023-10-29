# placeholder for extender vin validation
from wltr_vin import Vin
vins = ["JTEBU29J205045704"]

for vin in vins:
    result = Vin(vin)

    print(result.years)
