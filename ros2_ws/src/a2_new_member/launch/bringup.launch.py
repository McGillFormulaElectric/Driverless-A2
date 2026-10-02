"""Composed bring-up: student hello_publisher + student lpf_node.

Launches both student nodes under the /<github_user> ROS namespace.
Optionally also launches the grader stack via launch_grader:=true.

Usage:
    ros2 launch a2_new_member bringup.launch.py github_user:=<your-handle>
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    github_user = LaunchConfiguration('github_user')
    launch_grader = LaunchConfiguration('launch_grader')

    new_member_share = get_package_share_directory('a2_new_member')
    grader_share = get_package_share_directory('a2_grader')

    hello_launch = os.path.join(new_member_share, 'launch', 'hello.launch.py')
    lpf_launch = os.path.join(new_member_share, 'launch', 'lpf.launch.py')
    grader_launch = os.path.join(grader_share, 'launch', 'grader.launch.py')

    return LaunchDescription([
        DeclareLaunchArgument(
            'github_user',
            default_value=os.environ.get('GITHUB_USER', 'student'),
            description='Your GitHub username; used as the ROS namespace.',
        ),
        DeclareLaunchArgument(
            'launch_grader',
            default_value='false',
            description='Whether to launch the grader stack (signal_publisher + grader).',
        ),
        # Grader service (optional, if not already running in background)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(grader_launch),
            condition=IfCondition(launch_grader),
        ),
        # Student nodes (both launched under <github_user> namespace)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(hello_launch),
            launch_arguments={'github_user': github_user}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(lpf_launch),
            launch_arguments={'github_user': github_user}.items(),
        ),
    ])

