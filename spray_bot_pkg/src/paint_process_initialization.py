import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Int32, Float32
import time


class MasterSprayControl(Node):
    def __init__(self):
        super().__init__('paint_process_initialize')

        # --- Internal State ---
        self.current_pressure = 0
        self.current_angle = 0
        self.upper_limit_hit = False
        self.lower_limit_hit = False

        self.current_weight = 0.0
        self.weight_threshold = 0.5

        self.user_confirmed = False

        # 🔹 STEP 4 VARIABLES
        self.current_psi = 0.0
        self.calculated_pot_val = 0
        self.psi_confirmed = False

        self.current_process = "IDLE"
        self.last_completed_process = "NONE"

        self.step5_completed = False
        self.step5_repeat_requested = False

        self.step5_index = 0
        self.step5_last_time = 0
    

        # --- Publishers ---
        self.mode_pub = self.create_publisher(String, '/control_mode', 10)
        self.auto_goal_pub = self.create_publisher(String, '/auto_goal', 10)
        self.pressure_pub = self.create_publisher(String, '/set_pressure_level', 10)
        self.servo_pub = self.create_publisher(String, '/manual_cmd', 10)
        self.status_pub = self.create_publisher(String, '/process_status', 10)

        # --- Subscribers ---
        self.create_subscription(Int32, '/sensor/pressure', self.pressure_callback, 10)
        self.create_subscription(Int32, '/sensor/angle', self.angle_callback, 10)
        self.create_subscription(Bool, '/limits/lower_hit', self.lower_limit_callback, 10)
        self.create_subscription(Bool, '/limits/upper_hit', self.upper_limit_callback, 10)

        self.create_subscription(Float32, '/load_cell/weight', self.weight_callback, 10)
        self.create_subscription(Bool, '/user_confirmation', self.confirm_callback, 10)
        self.create_subscription(Bool, '/step5_repeat', self.step5_repeat_callback, 10)

        # 🔹 STEP 4 PSI INPUT
        self.create_subscription(Float32, '/psi_input', self.psi_callback, 10)



        self.timer = self.create_timer(0.1, self.control_loop)
        self.start_timer = self.create_timer(1.5, self.initiate_homing)

    # -------------------------
    # Callbacks
    # -------------------------
    def pressure_callback(self, msg): 
        self.current_pressure = msg.data

    def angle_callback(self, msg): 
        self.current_angle = msg.data

    def lower_limit_callback(self, msg): 
        self.lower_limit_hit = msg.data

    def upper_limit_callback(self, msg): 
        self.upper_limit_hit = msg.data

    def weight_callback(self, msg):
        self.current_weight = msg.data

    def confirm_callback(self, msg):
        if msg.data:
            self.user_confirmed = True
            self.psi_confirmed = True

    def psi_callback(self, msg):
        self.current_psi = msg.data

        # 🔹 Convert PSI to POT
        raw_val = 0.1097 * self.current_psi - 77.63
        self.calculated_pot_val = int(max(0, min(255, raw_val)))

        self.get_logger().info(
            f"PSI: {self.current_psi:.2f} -> POT: {self.calculated_pot_val}"
        )

    # -------------------------
    # Step 1 – Homing
    # -------------------------
    def initiate_homing(self):
        self.start_timer.cancel()
        self.current_process = "MOVING_UP"
        self.mode_pub.publish(String(data='auto'))
        self.auto_goal_pub.publish(String(data='U'))


    def run_step5_sequence(self):
        """Executes the A180, A0 sequence."""

        positions = ['A80', 'A0', 'A180', 'A0']

        for pos in positions:
            self.servo_pub.publish(String(data=str(pos)))
            time.sleep(0.5)

    def step5_repeat_callback(self, msg):
        if msg.data:
            self.step5_repeat_requested = True
    # -------------------------
    # Main Process Logic
    # -------------------------
    def control_loop(self):

        # STEP 1
        if self.current_process == "MOVING_UP" and self.upper_limit_hit:
            self.auto_goal_pub.publish(String(data='S'))
            self.current_process = "WAITING_FOR_WEIGHT"
            self.last_completed_process = "MOVING_UP_SUCCESS"

        # STEP 2
        elif self.current_process == "WAITING_FOR_WEIGHT":
            if self.current_weight > self.weight_threshold:
                self.current_process = "WAITING_FOR_CONFIRMATION"

        elif self.current_process == "WAITING_FOR_CONFIRMATION":
            if self.user_confirmed:
                self.current_process = "MOVING_DOWN"
                self.last_completed_process = "STEP2_WEIGHT_CONFIRMED"
                self.mode_pub.publish(String(data='auto'))
                self.auto_goal_pub.publish(String(data='D'))
                self.user_confirmed = False

        # STEP 3
        elif self.current_process == "MOVING_DOWN":
            if self.lower_limit_hit:
                self.auto_goal_pub.publish(String(data='S'))
                self.current_process = "WAITING_FOR_PSI"
                self.last_completed_process = "STEP3_MOVING_DOWN_SUCCESS"

        # STEP 4 – WAIT FOR PSI INPUT
        elif self.current_process == "WAITING_FOR_PSI":
            if self.current_psi > 0:
                self.current_process = "WAITING_FOR_PSI_CONFIRMATION"

        # STEP 4 – CONFIRM PSI & PUBLISH
        elif self.current_process == "WAITING_FOR_PSI_CONFIRMATION":

            if self.user_confirmed:

                self.pressure_pub.publish(
                    String(data=str(self.calculated_pot_val))
                )

                
                self.last_completed_process = "STEP4_PRESSURE_SET_SUCCESS"

                self.get_logger().info(
                    "Step 4 Complete: Pressure value confirmed and published."
                )
                self.user_confirmed = False

                # Move to delay state instead of IDLE
                self.current_process = "STEP4_DELAY_BEFORE_STEP5"
                self.step4_completed_time = time.time()
        elif self.current_process == "STEP4_DELAY_BEFORE_STEP5":

            if time.time() - self.step4_completed_time >= 5.0:
                self.step5_completed = False
                self.get_logger().info("5 seconds completed. Starting Step 5.")
                self.current_process = "STEP5_SERVO_SEQUENCE"


        elif self.current_process == "STEP5_SERVO_SEQUENCE":
    
            # Non-blocking servo sequence
            positions = ['A180', 'A0', 'A180', 'A0']

            # Check if it's time to move to the next position
            if time.time() - self.step5_last_time >= 0.5:
                pos = positions[self.step5_index]
                self.servo_pub.publish(String(data=pos))
                self.get_logger().info(f"Step5 servo command: {pos}")
                self.step5_index += 1
                self.step5_last_time = time.time()

            # Sequence finished
            if self.step5_index >= len(positions):
                self.step5_index = 0  # Reset for next repeat
                self.current_process = "WAITING_FOR_STEP5_CONFIRMATION"
                self.get_logger().info(
                    "Step 5 sequence executed. Waiting for user confirmation..."
                )

        # --------------------------
        # Wait for confirmation or repeat
        # --------------------------
        elif self.current_process == "WAITING_FOR_STEP5_CONFIRMATION":
            
            # Repeat requested by user
            if self.step5_repeat_requested:
                self.step5_repeat_requested = False
                self.current_process = "STEP5_SERVO_SEQUENCE"
                self.step5_index = 0
                self.step5_last_time = 0
                self.get_logger().info("Step 5 repeat requested. Restarting sequence...")

            # Step completed by user confirmation
            elif self.user_confirmed:
                self.user_confirmed = False
                self.step5_completed = True
                self.last_completed_process = "STEP5_SUCCESS"
                self.current_process = "IDLE"
                self.get_logger().info("Step 5 Completed Successfully.")


        # Status
        status_msg = String()
        status_msg.data = (
            f"CURRENT: {self.current_process} | "
            f"LAST_SUCCESS: {self.last_completed_process} | "
            f"WEIGHT: {self.current_weight:.2f} kg | "
            f"PSI: {self.current_psi:.2f} | "
            f"POT: {self.calculated_pot_val}"
        )
        self.status_pub.publish(status_msg)


def main(args=None):
    rclpy.init(args=args)
    node = MasterSprayControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
