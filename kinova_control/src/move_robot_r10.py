#! /usr/bin/env python3
"""Publishes joint trajectory to move robot to given pose"""

import rospy
from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from std_srvs.srv import Empty
import argparse
import time

import re

def argumentParser(argument):
  """ Argument parser """
  parser = argparse.ArgumentParser(description='Drive robot joint to command position')
  parser.add_argument('kinova_robotType', metavar='kinova_robotType', type=str, default='j2n6a300',
                    help='kinova_RobotType is in format of: [{j|m|r|c}{1|2}{s|n}{4|6|7}{s|a}{2|3}{0}{0}]. eg: j2n6a300 refers to jaco v2 6DOF assistive 3fingers. Please be noted that not all options are valided for different robot types.')
  #args_ = parser.parse_args(argument)
  argv = rospy.myargv()
  args_ = parser.parse_args(argv[1:])
  prefix = args_.kinova_robotType
  nbJoints = int(args_.kinova_robotType[3])	
  nbfingers = int(args_.kinova_robotType[5])	
  return prefix, nbJoints, nbfingers

def moveJoint (jointcmds,prefix,nbJoints):
  topic_name = '/' + prefix + '/effort_joint_trajectory_controller/command'
  pub = rospy.Publisher(topic_name, JointTrajectory, queue_size=1)
  jointCmd = JointTrajectory()  
  point = JointTrajectoryPoint()
  jointCmd.header.stamp = rospy.Time.now() + rospy.Duration.from_sec(0.0);  
  point.time_from_start = rospy.Duration.from_sec(0.1) # <RTEN> has to match while (count < x): 0.1s==100ms==10
  for i in range(0, nbJoints):
    jointCmd.joint_names.append(prefix +'_joint_'+str(i+1))
    point.positions.append(jointcmds[i])
    point.velocities.append(0)
    point.accelerations.append(0)
    point.effort.append(0) 
  jointCmd.points.append(point)
  rate = rospy.Rate(100)
  count = 0
  while (count < 10): # <RTEN> 10 == 100ms
    pub.publish(jointCmd)
    count = count + 1
    rate.sleep()

def moveFingers (jointcmds,prefix,nbJoints):
  topic_name = '/' + prefix + '/effort_finger_trajectory_controller/command'
  pub = rospy.Publisher(topic_name, JointTrajectory, queue_size=1)  
  jointCmd = JointTrajectory()  
  point = JointTrajectoryPoint()
  jointCmd.header.stamp = rospy.Time.now() + rospy.Duration.from_sec(0.0);  
  point.time_from_start = rospy.Duration.from_sec(5.0)
  for i in range(0, nbJoints):
    jointCmd.joint_names.append(prefix +'_joint_finger_'+str(i+1))
    point.positions.append(jointcmds[i])
    point.velocities.append(0)
    point.accelerations.append(0)
    point.effort.append(0) 
  jointCmd.points.append(point)
  rate = rospy.Rate(100)
  count = 0
  while (count < 500):
    pub.publish(jointCmd)
    count = count + 1
    rate.sleep()

def extract_last_packet(data):
  # Find all occurrences of packets using regex
  packets = re.findall(r'\d+:\[[^\]]+\]', data)
  
  if packets:
      # Return the last packet from the list
      return packets[-1]
  return None

if __name__ == '__main__':

  count = 0 # count for how many moves
  avg_one_way_latency = 0
  sum_one_way_latency = 0

  try:
    rospy.init_node('move_robot_using_trajectory_msg')		
    prefix, nbJoints, nbfingers = argumentParser(None)    
    #allow gazebo to launch
    time.sleep(5)

    # Unpause the physics
    rospy.wait_for_service('/gazebo/unpause_physics')
    unpause_gazebo = rospy.ServiceProxy('/gazebo/unpause_physics', Empty)
    resp = unpause_gazebo()

    while True:
      with open('data', 'r') as file:
        data = file.read().strip()  # Read and remove any extra whitespace
      with open('t1', 'r') as file:
        time_end_bridge = file.read().strip()  # Read and remove any extra whitespace
        time_end_bridge = float(time_end_bridge )
      
      if data:
        count += 1
      
        time1, data_string = data.split(":", 1) # split only once for the first :
        time1 = float(time1)
        time_start_mover = time.time()

        one_way_latency = time_start_mover - time1 - (time_start_mover - time_end_bridge)
        print("r10_bridge to move_robot(ms): ", round((time_start_mover - time_end_bridge)*1000, 4) )
        print("one-way delay(ms): ", round(one_way_latency*1000, 4))
        sum_one_way_latency += one_way_latency
        avg_one_way_latency = sum_one_way_latency / count
        print(f"Average one-way delay(ms): {avg_one_way_latency*1000:.4f}")
        print("6DoF Change to:", data_string)
        
        six_dof = eval(data_string)
      else:
        print("ERROR: None data")

      # # Unpause the physics
      # rospy.wait_for_service('/gazebo/unpause_physics')
      # unpause_gazebo = rospy.ServiceProxy('/gazebo/unpause_physics', Empty)
      # resp = unpause_gazebo()

      if (nbJoints==6):
        #home robots
        moveJoint (six_dof,prefix,nbJoints)
      else:
        moveJoint ([0.0,2.9,0.0,1.3,4.2,1.4,0.0],prefix,nbJoints)

      # moveFingers ([1,1,1],prefix,nbfingers)
      timestamp_2 = time.time()
      print("move joint delay(ms): ", round((timestamp_2-time_start_mover)*1000, 4))
      print ("<RTEN> move complete!\n")
  except rospy.ROSInterruptException:
    print("program interrupted before completion")
