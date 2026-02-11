from opendbc.can import CANPacker
from opendbc.car import Bus
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.canabstractcar.values import CarControllerParams


class CarController(CarControllerBase):
  def __init__(self, dbc_names, CP):
    super().__init__(dbc_names, CP)
    self.packer = CANPacker(dbc_names[Bus.main])
    self.params = CarControllerParams(CP)
    self.apply_steer_last = 0

  def update(self, CC, CS, now_nanos):
    can_sends = []
    actuators = CC.actuators

    # Steering control
    apply_steer = 0
    if CC.latActive:
      # Calculate steering command from actuators
      # TODO: Implement actual steering logic based on car's CAN protocol
      apply_steer = int(actuators.steer * self.params.STEER_MAX)

      # Apply rate limits
      apply_steer = self.apply_rate_limit(
        apply_steer,
        self.apply_steer_last,
        self.params.STEER_DELTA_DOWN,
        self.params.STEER_DELTA_UP
      )

    self.apply_steer_last = apply_steer

    # TODO: Create actual CAN messages for steering
    # Example: can_sends.append(self.packer.make_can_msg("STEERING_CMD", 0, {"STEER_TORQUE": apply_steer}))

    # Longitudinal control (if applicable)
    if CC.longActive:
      # TODO: Implement gas/brake control based on car's CAN protocol
      pass

    new_actuators = actuators.as_builder()
    new_actuators.steer = apply_steer / self.params.STEER_MAX if self.params.STEER_MAX else 0
    new_actuators.steerOutputCan = apply_steer

    self.frame += 1
    return new_actuators, can_sends

  @staticmethod
  def apply_rate_limit(new_value, last_value, down_limit, up_limit):
    """Apply rate limiting to a value."""
    return max(last_value - down_limit, min(new_value, last_value + up_limit))
