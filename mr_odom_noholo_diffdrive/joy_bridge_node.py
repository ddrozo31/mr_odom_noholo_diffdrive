import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import socket
import json

DEADBAND = 0.05  # Adjust this threshold as needed

def apply_deadband(value, threshold):
    return 0.0 if abs(value) < threshold else value

class JoyBridge(Node):
    def __init__(self):
        super().__init__('joy_bridge')
        self.publisher_ = self.create_publisher(Joy, 'joy', 10)

        # Setup TCP server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('127.0.0.1', 5005))
        self.sock.listen(1)

        self.get_logger().info("Waiting for joystick stream on 127.0.0.1:5005...")
        self.conn, addr = self.sock.accept()
        self.get_logger().info(f"Joystick stream connected from {addr}")

        self.buffer = ""  # Accumulate partial data
        self.timer = self.create_timer(0.02, self.timer_callback)

    def timer_callback(self):
        try:
            data = self.conn.recv(4096).decode()
            if not data:
                return
            self.buffer += data

            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                if not line.strip():
                    continue

                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as e:
                    self.get_logger().warn(f"JSON decode error: {e}")
                    continue

                # Apply deadband to axes
                axes = [apply_deadband(val, DEADBAND) for val in payload.get('axes', [])]

                msg = Joy()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.axes = axes
                msg.buttons = payload.get('buttons', [])
                self.publisher_.publish(msg)

        except Exception as e:
            self.get_logger().warn(f"Stream error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = JoyBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

