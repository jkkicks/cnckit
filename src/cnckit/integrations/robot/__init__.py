"""
Robot interfaces for ROS2 and TCP-based robots.

Provides coordination between CNC machine and robotic systems.
Requires: pip install cnckit[robot]
"""


class ROS2Interface:
    """
    ROS2 interface for robot coordination.

    Publishes CNC events to ROS2 topics and subscribes to robot commands.

    Raises:
        ImportError: If rclpy is not installed
    """

    def __init__(self, node_name: str = "cnckit"):
        """
        Initialize ROS2 node.

        Args:
            node_name: ROS2 node name
        """
        try:
            import rclpy  # noqa: F401
        except ImportError:
            raise ImportError(
                "rclpy is required for ROS2 integration. "
                "Install ROS2 and source the setup script."
            )

        raise NotImplementedError("ROS2 integration will be implemented in Phase 2")


class TCPRobotClient:
    """
    TCP client for simple robot protocols.

    Sends commands to robots over TCP sockets.
    """

    def __init__(self, host: str, port: int):
        """
        Initialize TCP connection to robot.

        Args:
            host: Robot hostname or IP
            port: Robot TCP port
        """
        raise NotImplementedError("TCP robot client will be implemented in Phase 2")
