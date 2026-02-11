from opendbc.can import CANParser
from opendbc.car import Bus, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.interfaces import CarStateBase
from opendbc.car.canabstractcar.values import DBC, CAN_FREQUENCY_HZ


class CarState(CarStateBase):
  def __init__(self, CP):
    super().__init__(CP)
    self.cruise_buttons_prev = 0

  def update(self, can_parsers) -> structs.CarState:
    cp = can_parsers[Bus.main]
    ret = structs.CarState()

    # Parse VEHICLE_STATUS (0x44)
    # Speed - convert km/h to m/s
    speed_kmh = cp.vl['VEHICLE_STATUS']['SPEED']
    ret.vEgoRaw = speed_kmh * CV.KPH_TO_MS
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)

    # Wheel speeds (assuming all wheels have same speed for now)
    ret.wheelSpeeds.fl = ret.vEgoRaw
    ret.wheelSpeeds.fr = ret.vEgoRaw
    ret.wheelSpeeds.rl = ret.vEgoRaw
    ret.wheelSpeeds.rr = ret.vEgoRaw

    ret.standstill = ret.vEgo < 0.1

    # Gear
    gear_val = int(cp.vl['VEHICLE_STATUS']['GEAR'])
    if gear_val == 1:
      ret.gearShifter = structs.CarState.GearShifter.neutral
    elif gear_val == 2:
      ret.gearShifter = structs.CarState.GearShifter.drive
    elif gear_val == 3:
      ret.gearShifter = structs.CarState.GearShifter.park
    elif gear_val == 4:
      ret.gearShifter = structs.CarState.GearShifter.reverse
    else:
      ret.gearShifter = structs.CarState.GearShifter.unknown

    # Driver steering torque
    torque_polarity = int(cp.vl['VEHICLE_STATUS']['TORQUE_POLARITY'])
    torque_value = cp.vl['VEHICLE_STATUS']['DRIVER_TORQUE']
    if torque_polarity == 1:  # Left
      ret.steeringTorque = -torque_value
    elif torque_polarity == 2:  # Right
      ret.steeringTorque = torque_value
    else:
      ret.steeringTorque = 0
    ret.steeringTorqueEps = ret.steeringTorque
    ret.steeringPressed = abs(ret.steeringTorque) > 20

    # Car bools from byte 4
    ret.seatbeltUnlatched = not cp.vl['VEHICLE_STATUS']['SEATBELT_OK']
    ret.brakePressed = bool(cp.vl['VEHICLE_STATUS']['BRAKE_PRESSED'])
    ret.brake = 1.0 if ret.brakePressed else 0.0
    ret.gasPressed = bool(cp.vl['VEHICLE_STATUS']['ACCELERATOR_PRESSED'])
    ret.doorOpen = not cp.vl['VEHICLE_STATUS']['DOORS_CLOSED']
    ret.leftBlinker = bool(cp.vl['VEHICLE_STATUS']['INDICATOR_LEFT'])
    ret.rightBlinker = bool(cp.vl['VEHICLE_STATUS']['INDICATOR_RIGHT'])
    # Charging status (charger disconnected = not charging)
    ret.charging = not cp.vl['VEHICLE_STATUS']['CHARGER_DISCONNECTED']

    # Parse BUTTONS_PEDALS (0x46)
    # Cruise control set speed - now from BUTTONS_PEDALS, convert km/h to m/s
    cruise_set_speed_kmh = cp.vl['BUTTONS_PEDALS']['CRUISE_SET_SPEED']
    ret.cruiseState.speed = cruise_set_speed_kmh * CV.KPH_TO_MS

    # Pedal positions
    ret.gas = cp.vl['BUTTONS_PEDALS']['ACCELERATOR_PEDAL'] / 100.0

    # Parking brake
    parking_brake = bool(cp.vl['BUTTONS_PEDALS']['PARKING_BRAKE'])

    # Cruise control buttons
    cruise_main = bool(cp.vl['BUTTONS_PEDALS']['CRUISE_MAIN'])
    cruise_resume = bool(cp.vl['BUTTONS_PEDALS']['CRUISE_RESUME'])
    cruise_cancel = bool(cp.vl['BUTTONS_PEDALS']['CRUISE_CANCEL'])
    cruise_up_1 = bool(cp.vl['BUTTONS_PEDALS']['CRUISE_UP_1'])
    cruise_down_1 = bool(cp.vl['BUTTONS_PEDALS']['CRUISE_DOWN_1'])
    cruise_up_10 = bool(cp.vl['BUTTONS_PEDALS']['CRUISE_UP_10'])
    cruise_down_10 = bool(cp.vl['BUTTONS_PEDALS']['CRUISE_DOWN_10'])

    # Set cruise state
    ret.cruiseState.available = True  # Always available if CAN is healthy
    ret.cruiseState.enabled = cruise_main and (cruise_set_speed_kmh > 0)
    ret.cruiseState.standstill = parking_brake and ret.standstill

    # Button events
    ret.buttonEvents = self._create_button_events(
      cruise_main, cruise_resume, cruise_cancel,
      cruise_up_1, cruise_down_1, cruise_up_10, cruise_down_10
    )

    return ret

  def _create_button_events(self, cruise_main, cruise_resume, cruise_cancel,
                            cruise_up_1, cruise_down_1, cruise_up_10, cruise_down_10):
    """Create button events from current button states."""
    events = []
    ButtonType = structs.CarState.ButtonEvent.Type

    # Encode current button state into single value for comparison
    current_buttons = (
      (cruise_main << 0) |
      (cruise_resume << 1) |
      (cruise_cancel << 2) |
      (cruise_up_1 << 3) |
      (cruise_down_1 << 4) |
      (cruise_up_10 << 5) |
      (cruise_down_10 << 6)
    )

    # Create events on button state changes
    if current_buttons != self.cruise_buttons_prev:
      # Main cruise button
      if cruise_main and not (self.cruise_buttons_prev & 0x01):
        events.append(structs.CarState.ButtonEvent(pressed=True, type=ButtonType.altButton1))
      elif not cruise_main and (self.cruise_buttons_prev & 0x01):
        events.append(structs.CarState.ButtonEvent(pressed=False, type=ButtonType.altButton1))

      # Resume
      if cruise_resume and not (self.cruise_buttons_prev & 0x02):
        events.append(structs.CarState.ButtonEvent(pressed=True, type=ButtonType.resumeCruise))
      elif not cruise_resume and (self.cruise_buttons_prev & 0x02):
        events.append(structs.CarState.ButtonEvent(pressed=False, type=ButtonType.resumeCruise))

      # Cancel
      if cruise_cancel and not (self.cruise_buttons_prev & 0x04):
        events.append(structs.CarState.ButtonEvent(pressed=True, type=ButtonType.cancel))
      elif not cruise_cancel and (self.cruise_buttons_prev & 0x04):
        events.append(structs.CarState.ButtonEvent(pressed=False, type=ButtonType.cancel))

      # Accel (+1 or +10)
      if (cruise_up_1 or cruise_up_10) and not (self.cruise_buttons_prev & 0x28):
        events.append(structs.CarState.ButtonEvent(pressed=True, type=ButtonType.accelCruise))
      elif not (cruise_up_1 or cruise_up_10) and (self.cruise_buttons_prev & 0x28):
        events.append(structs.CarState.ButtonEvent(pressed=False, type=ButtonType.accelCruise))

      # Decel (-1 or -10)
      if (cruise_down_1 or cruise_down_10) and not (self.cruise_buttons_prev & 0x50):
        events.append(structs.CarState.ButtonEvent(pressed=True, type=ButtonType.decelCruise))
      elif not (cruise_down_1 or cruise_down_10) and (self.cruise_buttons_prev & 0x50):
        events.append(structs.CarState.ButtonEvent(pressed=False, type=ButtonType.decelCruise))

      self.cruise_buttons_prev = current_buttons

    return events

  @staticmethod
  def get_can_parsers(CP):
    messages = [
      # Message name, frequency in Hz
      ("VEHICLE_STATUS", CAN_FREQUENCY_HZ),
      ("BUTTONS_PEDALS", CAN_FREQUENCY_HZ),
    ]
    return {Bus.main: CANParser(DBC[CP.carFingerprint][Bus.main], messages, 0)}
