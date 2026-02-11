""" AUTO-FORMATTED USING opendbc/car/debug/format_fingerprints.py, EDIT STRUCTURE THERE."""
from opendbc.car.structs import CarParams
from opendbc.car.canabstractcar.values import CAR

Ecu = CarParams.Ecu


# CAN message fingerprints for identifying this car
# Format: {message_id: message_length, ...}
# These are the CAN messages seen on bus 0 (CAN1) during identification
# 0x44 = 68 (VEHICLE_STATUS), 0x46 = 70 (BUTTONS_PEDALS)
FINGERPRINTS = {
  CAR.CANABSTRACTCAR: [{
    68: 8,   # VEHICLE_STATUS - 0x44
    70: 8,   # BUTTONS_PEDALS - 0x46
  }],
}

# Firmware versions for ECU fingerprinting
FW_VERSIONS = {
  CAR.CANABSTRACTCAR: {
    # No firmware queries defined yet
  },
}
