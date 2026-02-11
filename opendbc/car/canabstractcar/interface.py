from opendbc.car import get_safety_config, structs
from opendbc.car.interfaces import CarInterfaceBase
from opendbc.car.canabstractcar.carcontroller import CarController
from opendbc.car.canabstractcar.carstate import CarState
from opendbc.car.canabstractcar.values import CAN_SPEED_KBPS


class CarInterface(CarInterfaceBase):
  """
  CANabstractCAR interface for openpilot.

  IMPORTANT: This car port requires the CAN bus to be configured at 125 kbps.
  The panda must be configured before launching openpilot:
    panda.set_can_speed_kbps(0, 125)

  See CAN_SPEED_KBPS in values.py for the required speed constant.
  """
  CarState = CarState
  CarController = CarController

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, alpha_long, is_release, docs) -> structs.CarParams:
    ret.brand = "canabstractcar"

    # Safety configuration - using allOutput for development
    # TODO: Implement proper safety model for this car
    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.allOutput)]

    # Steering configuration
    ret.steerControlType = structs.CarParams.SteerControlType.torque
    ret.steerActuatorDelay = 0.1  # Tune based on actual car response
    ret.steerLimitTimer = 0.4

    # Lateral tuning - adjust based on actual car behavior
    ret.lateralTuning.pid.kpBP = [0.]
    ret.lateralTuning.pid.kpV = [0.3]
    ret.lateralTuning.pid.kiBP = [0.]
    ret.lateralTuning.pid.kiV = [0.05]
    ret.lateralTuning.pid.kf = 0.00006

    # Longitudinal configuration
    ret.openpilotLongitudinalControl = False  # Set to True if implementing long control
    ret.radarUnavailable = True  # Set to False if car has radar

    # CAN health - messages should arrive at 5Hz minimum
    # This ensures the system considers CAN unhealthy if messages stop
    ret.minSteerSpeed = 0.  # Allow steering at any speed

    return ret
