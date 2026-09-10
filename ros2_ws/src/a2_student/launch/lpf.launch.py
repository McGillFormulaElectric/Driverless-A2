"""Launch A2.2 LPF node under the student's GitHub-username namespace.

Usage:
    ros2 launch a2_student lpf.launch.py github_user:=<your-handle>
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    github_user = LaunchConfiguration('github_user')
    return LaunchDescription([
        DeclareLaunchArgument(
            'github_user',
            description='Your GitHub username; used as the ROS namespace.',
        ),
        Node(
            package='a2_student',
            executable='lpf_node',
            name='lpf_node',
            namespace=github_user,
            output='screen',
        ),
    ])
