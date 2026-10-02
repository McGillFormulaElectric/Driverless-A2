"""Launch A2.1 hello publisher under the student's GitHub-username namespace.

Usage:
    ros2 launch a2_new_member hello.launch.py github_user:=<your-handle>
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    github_user = LaunchConfiguration('github_user')
    return LaunchDescription([
        DeclareLaunchArgument(
            'github_user',
            default_value=os.environ.get('GITHUB_USER', 'student'),
            description='Your GitHub username; used as the ROS namespace.',
        ),
        Node(
            package='a2_new_member',
            executable='hello_publisher',
            name='hello_publisher',
            namespace=github_user,
            output='screen',
        ),
    ])
