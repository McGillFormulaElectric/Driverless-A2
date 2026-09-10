"""Bring up the professor side: reference signal publisher + grader."""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='a2_professor',
            executable='signal_publisher',
            name='signal_publisher',
            output='screen',
        ),
        Node(
            package='a2_professor',
            executable='grader',
            name='grader',
            output='screen',
        ),
    ])
