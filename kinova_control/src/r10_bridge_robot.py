#! /usr/bin/env python3
"""RosBridge"""

from __future__ import print_function
import roslibpy
import json

import rospy

import time

sum_network_latency = 0.0
avg_network_latency = 0.0
count = 0

def parse_message(message):
  global count
  global sum_network_latency
  global avg_network_latency

  listener_start = time.time()

  # Parse the JSON data string
  parsed_message = json.loads(message)
  
  # Extract the vaalues
  data_string = parsed_message['fused_pose']
  time1 = parsed_message['time1']

  # Print or process the extracted values
  # print(f"Received data: {data_string}, time1: {time1}")

  count += 1
  network_latency = time.time() - time1
  sum_network_latency += network_latency
  avg_network_latency = sum_network_latency / count
  
  # print(f"Netowkr Latency: {round(network_latency*1000, 4)}ms, Avg: {round(avg_network_latency*1000, 4)}ms")

  with open('data', 'w') as file:
    file.write(str(time1)+":"+str(data_string))  # Convert list to string and write it to the file
  with open('t1', 'w') as file:
    file.write(str(time.time()))

  listener_latency = time.time() - listener_start

  print(f"Netowkr Latency: {round(network_latency*1000, 4)}ms, Avg: {round(avg_network_latency*1000, 4)}ms, Listener Latency: {round(listener_latency*1000, 4)}ms")


def listen_from_xr(xr, port):

  client = roslibpy.Ros(host=xr, port=port)
  client.run()

  listener = roslibpy.Topic(client, '/chatter', 'std_msgs/String')

  # Modify the lambda to parse JSON
  listener.subscribe(lambda message: parse_message(message['data']))

  try:
      while True:
          pass
  except KeyboardInterrupt:
      client.terminate()

if __name__ == '__main__':
  try:
    rospy.init_node('rosbridge_robot')

    # host = "10.13.146.101"  # Replace with server IP address if needed
    host = "localhost"  # Replace with server IP address if needed
    port = 9090
    # receive_data(host, port)
    listen_from_xr(host, port)
  except rospy.ROSInterruptException:
    print("program interrupted before completion")