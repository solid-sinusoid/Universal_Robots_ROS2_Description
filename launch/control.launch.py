from launch_ros.actions import Node
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "with_gripper",
            default_value="false",
            description="With gripper or not?",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_description",
            default_value="",
            description="robot description param",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "start_joint_controller",
            default_value="false",
            description="Enable headless mode for robot control",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "initial_joint_controller",
            default_value="joint_trajectory_controller",
            description="Robot controller to start.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "controllers_file",
            default_value="ur_controllers.yaml",
            description="YAML file with the controllers configuration.",
        )
    )
    robot_description_content = LaunchConfiguration("robot_description")
    runtime_config_package = LaunchConfiguration("runtime_config_package")
    controllers_file = LaunchConfiguration("controllers_file")
    start_joint_controller = LaunchConfiguration("start_joint_controller")
    with_gripper_condition = LaunchConfiguration("with_gripper")
    initial_joint_controller = LaunchConfiguration("initial_joint_controller")
    
    initial_joint_controllers_file_path = PathJoinSubstitution(
        [FindPackageShare(runtime_config_package), "config", controllers_file]
    )
    robot_description = {"robot_description": robot_description_content}

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, initial_joint_controllers_file_path],
        output="both",
        remappings=[
            ('motion_control_handle/target_frame', 'target_frame'),
            ('cartesian_compliance_controller/target_frame', 'target_frame'),
            ('cartesian_compliance_controller/target_wrench', 'target_wrench'),
            ('cartesian_compliance_controller/ft_sensor_wrench', 'ft_sensor_wrench'),
            ]
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
    )

    # FIXME: Start controllers one controller by one launch or launch it all and switch by runtime?
    initial_joint_controller_spawner_started = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[initial_joint_controller, "-c", "/controller_manager"],
        condition=IfCondition(start_joint_controller),
    )
    initial_joint_controller_spawner_stopped = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[initial_joint_controller, "-c", "/controller_manager", "--inactive"],
        condition=UnlessCondition(start_joint_controller),
    )
    
    gripper_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             "gripper_controller"],
        output='screen',
        condition=IfCondition(with_gripper_condition)
    )
    cartesian_motion_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["cartesian_motion_controller", "--inactive", "-c", "/controller_manager"],
    )
    motion_control_handle_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["motion_control_handle", "--inactive", "-c", "/controller_manager"],
    )
    
    cartesian_compliance_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["cartesian_compliance_controller", "--inactive", "-c", "/controller_manager"],
    )
    
    nodes_to_start = [
        control_node,
        joint_state_broadcaster_spawner,
        initial_joint_controller_spawner_started,
        initial_joint_controller_spawner_stopped,
        gripper_controller,
        cartesian_motion_controller_spawner,
        motion_control_handle_spawner,
        cartesian_compliance_controller_spawner
    ]
    
    return LaunchDescription(declared_arguments + nodes_to_start)