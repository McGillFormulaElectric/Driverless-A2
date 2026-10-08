"""Composed bring-up: grader stack + student hello and LPF nodes.

Includes:
  - a2_grader/grader.launch.py        (NOT namespaced - it owns /grader/*)
  - a2_new_member/hello.launch.py     (namespaced under /<github_user>)
  - a2_new_member/lpf.launch.py       (namespaced under /<github_user>)

Usage:
    ros2 launch a2_new_member bringup.launch.py github_user:=<your-handle>
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _include(package, name, **args):
    path = os.path.join(get_package_share_directory(package), 'launch', name)
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(path), launch_arguments=args.items()
    )


def generate_launch_description():
    github_user = LaunchConfiguration('github_user')
    return LaunchDescription([
        DeclareLaunchArgument(
            'github_user',
            description='Your GitHub username; used as the ROS namespace for the student nodes.',
        ),
        _include('a2_grader', 'grader.launch.py'),
        _include('a2_new_member', 'hello.launch.py', github_user=github_user),
        _include('a2_new_member', 'lpf.launch.py', github_user=github_user),
    ])
