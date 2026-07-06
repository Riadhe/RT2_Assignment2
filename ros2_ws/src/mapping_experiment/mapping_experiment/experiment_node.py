"""
.. module:: experiment_node
   :platform: Unix
   :synopsis: ROS 2 node that simulates one 3D-mapping trial per request.

.. moduleauthor:: Riadh Bahri <s8335614@studenti.unige.it>

Stands in for the full Isaac Sim + mapping pipeline of the COGAR
benchmark. The Jupyter notebook publishes a trial request and the node
replies with the metrics of one simulated run, drawn from distributions
anchored to the real COGAR measurements.

Subscribed topics:
    /experiment/run (std_msgs/String): JSON request
        {"scene": ..., "framework": ..., "trial": ...}

Published topics:
    /experiment/result (std_msgs/String): JSON reply with the metrics
        (latency_ms, coverage_m3, density_pts_m3, success).
"""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from mapping_experiment.metrics_model import simulate_trial


class MappingExperimentNode(Node):
    """Serves simulated mapping trials over ROS 2 topics.

    Attributes:
        sub: subscriber to /experiment/run.
        pub: publisher on /experiment/result.
    """

    def __init__(self):
        """Initialise the node, its subscriber, publisher and seed param."""
        super().__init__("mapping_experiment_node")
        self.sub = self.create_subscription(
            String, "/experiment/run", self.run_callback, 10)
        self.pub = self.create_publisher(String, "/experiment/result", 10)
        self.declare_parameter("seed_base", 12345)
        self.get_logger().info(
            "mapping_experiment_node ready - waiting on /experiment/run")

    def run_callback(self, msg):
        """Handle one trial request and publish its metrics.

        Args:
            msg (std_msgs.msg.String): JSON with keys 'scene',
                'framework', 'trial'.
        """
        try:
            req = json.loads(msg.data)
            seed = int(self.get_parameter("seed_base").value)
            result = simulate_trial(
                req["scene"], req["framework"], int(req["trial"]),
                seed_base=seed)
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            result = {"error": str(exc)}
            self.get_logger().error(f"bad request: {exc}")
        out = String()
        out.data = json.dumps(result)
        self.pub.publish(out)
        if "error" not in result:
            self.get_logger().info(
                f"trial {result['trial']:02d} {result['scene']}/"
                f"{result['framework']}: latency={result['latency_ms']} ms")


def main(args=None):
    """Entry point: spin the node until interrupted."""
    rclpy.init(args=args)
    node = MappingExperimentNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
