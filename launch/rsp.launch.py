import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue

import xacro


def generate_launch_description():

    # Check if we're told to use sim time
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_ros2_control = LaunchConfiguration('use_ros2_control')

    # Produce the URDF string from collection of .xacro's:
    pkg_path = os.path.join(get_package_share_directory('stingray'))
    xacro_file = os.path.join(pkg_path,'description/urdf','robot.urdf.xacro')

    robot_description_sdf = Command(['xacro ', xacro_file,
                                ' use_ros2_control:=', use_ros2_control,
                                ' sim_mode:=', use_sim_time])

    # Create a robot_state_publisher node
    params = {
        'robot_description': ParameterValue(robot_description_sdf, value_type=str),
        #'publish_frequency' : 5.0,  - this has no effect. The topic is published on demand.
        'use_sim_time': use_sim_time
        }

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        namespace='/',
        parameters=[params]
    )

    node_joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        namespace='/',
        output=['screen']
    )
    # spawn entity (robot model) in the Gazebo gz_sim
    # see arguments:  ros2 run ros_gz_sim create --helpshort
    spawn_sim_robot = Node(package='ros_gz_sim',
        executable='create',
        namespace='/',
        arguments=[
            '-name', 'stingray',
            '-topic', '/robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.4',
            '-Y', '0.333',
            '-allow_renaming', 'true'],
        parameters=[{'use_sim_time': True}],
        output='screen')

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace='/',
        arguments=["joint_broad", "--controller-manager", "/controller_manager"],
    )
    # For publishing and controlling the robot pose in the pop-up GUI:
    node_joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        namespace='/',
        # no need to supply SDF source here, it will be picked from topic /robot_description by default
        #arguments=[sdf_file],
        output=['screen']
    )

    # Launch!
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),
        DeclareLaunchArgument(
            'use_ros2_control',
            default_value='true',
            description='Use ros2_control if true'),

        node_robot_state_publisher,

        # Either of these two will override /joint_states topic with zeroes.
        # Normally, joint_state_broadcaster publishes it.
        #node_joint_state_publisher,
        #node_joint_state_publisher_gui
    ])
