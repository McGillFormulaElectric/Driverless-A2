"""Composed bring-up: professor stack + student LPF node.

Includes:
  - a2_professor/professor.launch.py   (NOT namespaced — it owns /professor/*)
  - a2_student/lpf.launch.py           (pushed under /<github_user>)

Usage:
    ros2 launch a2_student bringup.launch.py github_user:=<your-handle>
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

    professor_launch = os.path.join(
        get_package_share_directory('a2_professor'), 'launch', 'professor.launch.py'
    )
    student_launch = os.path.join(
        get_package_share_directory('a2_student'), 'launch', 'lpf.launch.py'
    )

    professor_group = GroupAction([
        # Professor publishes on absolute topics (/professor/signal,
        # /professor/feedback) and must NOT be namespaced.
        IncludeLaunchDescription(PythonLaunchDescriptionSource(professor_launch)),
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
        professor_group,
        student_group,
    ])
