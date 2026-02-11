from opendbc.car import Bus, CarSpecs, PlatformConfig, Platforms
from opendbc.car.structs import CarParams
from opendbc.car.docs_definitions import CarDocs
from opendbc.car.fw_query_definitions import FwQueryConfig, Request, StdQueries

Ecu = CarParams.Ecu

# CAN bus speed for CANabstractCAR (125 kbps)
CAN_SPEED_KBPS = 125

# CAN message frequency requirement (5Hz minimum)
CAN_FREQUENCY_HZ = 5

# Car ID for fingerprinting (0x6C = 108 decimal = 01101100 binary)
CAR_ID = 0x6C


class CarControllerParams:
  """Parameters for the car controller tuning."""
  STEER_MAX = 300  # Maximum steering torque
  STEER_DELTA_UP = 10  # Ramp up rate per control step
  STEER_DELTA_DOWN = 25  # Ramp down rate per control step
  STEER_DRIVER_ALLOWANCE = 50  # Allowance for driver override

  def __init__(self, CP):
    pass


class CAR(Platforms):
  CANABSTRACTCAR = PlatformConfig(
    [CarDocs("CANabstract CAR", package="All")],
    CarSpecs(mass=1500, wheelbase=2.7, steerRatio=15.0),
    # Single CAN bus (CAN1) mapped to Bus.main
    {Bus.main: 'canabstractcar'},
  )


# Firmware query configuration for ECU fingerprinting
FW_QUERY_CONFIG = FwQueryConfig(
  requests=[
    Request(
      [StdQueries.TESTER_PRESENT_REQUEST, StdQueries.UDS_VERSION_REQUEST],
      [StdQueries.TESTER_PRESENT_RESPONSE, StdQueries.UDS_VERSION_RESPONSE],
      bus=0,  # CAN1 is bus 0
    ),
  ],
)

# DBC file mapping for each platform
DBC = CAR.create_dbc_map()
