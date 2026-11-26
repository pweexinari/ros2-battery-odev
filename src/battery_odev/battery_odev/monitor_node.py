import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from std_srvs.srv import Trigger


class MonitorNode(Node):
    def __init__(self):
        super().__init__('monitor_node')
        self.subscription = self.create_subscription(
            Float32,
            '/battery_level',
            self.listener_callback,
            10
        )
        self.client = self.create_client(Trigger, '/recharge')
        self.recharging = False
        self.get_logger().info('Monitor node (otomatik sarj aktif) baslatildi.')

    def listener_callback(self, msg):
        level = msg.data

        if level < 5.0 and not self.recharging:
            self.get_logger().warn(f'KRITIK PIL (%{level:.1f})! Otomatik sarj cagriliyor...')
            self.call_recharge_service()
        elif level < 20.0:
            self.get_logger().warn(f'UYARI! Dusuk pil seviyesi: %{level:.1f}')
        else:
            self.get_logger().info(f'Pil seviyesi normal: %{level:.1f}')

    def call_recharge_service(self):
        if not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().error('/recharge servisine ulasilamiyor!')
            return

        self.recharging = True
        request = Trigger.Request()
        future = self.client.call_async(request)
        future.add_done_callback(self.recharge_response_callback)

    def recharge_response_callback(self, future):
        try:
            response = future.result()
            self.get_logger().info(f'Servis cevabi alindi: "{response.message}"')
        except Exception as e:
            self.get_logger().error(f'Servis hatasi: {e}')
        finally:
            self.recharging = False


def main(args=None):
    rclpy.init(args=args)
    node = MonitorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
