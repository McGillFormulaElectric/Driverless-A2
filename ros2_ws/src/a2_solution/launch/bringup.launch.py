"""Composed bring-up: Neil's stack + student LPF node.

Includes:
  - a2_neil/neil.launch.py         (NOT namespaced — it owns /neil/*)
  - a2_solution/lpf.launch.py      (pushed under /<github_user>)

Usage:
    ros2 launch a2_solution bringup.launch.py github_user:=<your-handle>
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace


def generate_launch_description():
    github_user = LaunchConfiguration('github_user')

    neil_launch = os.path.join(
        get_package_share_directory('a2_neil'), 'launch', 'neil.launch.py'
    )
    student_launch = os.path.join(
        get_package_share_directory('a2_solution'), 'launch', 'lpf.launch.py'
    )

    neil_group = GroupAction([
        # Neil's nodes publish on absolute topics (/neil/signal,
        # /neil/feedback) and must NOT be namespaced.
        IncludeLaunchDescription(PythonLaunchDescriptionSource(neil_launch)),
    ])

    student_group = GroupAction([
        PushRosNamespace(github_user),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(student_launch),
            launch_arguments={'github_user': github_user}.items(),
        ),
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            'github_user',
            description='Your GitHub username; used as the ROS namespace for the student node.',
        ),
        neil_group,
        student_group,
    ])
