from __future__ import print_function
import roslibpy
import json

import rospy
import re

import socket
import select
import time

sum_network_latency = 0.0
avg_network_latency = 0.0
count = 0


def extract_last_packet(data):
  # Find all occurrences of packets using regex
  packets = re.findall(r'\d+:\[[^\]]+\]', data)
  
  if packets:
      # Return the last packet from the list
      return packets[-1]
  return None

def receive_data(host, port):
    current_time = None
    count = 0
    avg_one_way_latency = 0
    sum_one_way_latency = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.setblocking(0)  # Set the socket to non-blocking mode
        while True:
            # Use select to check for incoming data
            readable, _, _ = select.select([s], [], [], 10)  # Timeout of 1 second
            if readable:
                data = s.recv(1024).decode()
                if data:
                    count += 1
                    # print(f"Received: {data}")
                    # <RTEN> get timestamp here ====================================================
                    data_temp = extract_last_packet(data)
                    timestamp, _ = data_temp.split(":", 1) # split only once for the first :
                    timestamp = int(timestamp)
                    current_time = round(time.time()*1000)
                    one_way_latency = current_time - timestamp
                    sum_one_way_latency += one_way_latency
                    avg_one_way_latency = sum_one_way_latency/count
                    if count % 100 == 0:
                      print("one-way delay(ms): ", one_way_latency)
                      print(f"Average one-way delay(ms): {avg_one_way_latency:.2f}")
                    # End ==========================================================================

                    with open('data', 'w') as file:
                        file.write(str(data))  # Convert list to string and write it to the file
                    with open('t1', 'w') as file:
                        file.write(str(current_time))
                else:
                    print("Connection closed by the server")
                    break
            else:
                print("No new data, still listening...")
            time.sleep(1/10)  # Adjust sleep duration as needed

def parse_message(message):
  global count
  global sum_network_latency
  global avg_network_latency

  listener_start = time.time()

  # Parse the JSON data string
  parsed_message = json.loads(message)
  
  # Extract the values
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

  # Modify the lambda to parse JSON and extract data_string and time1
  listener.subscribe(lambda message: parse_message(message['data']))

  try:
      while True:
          pass
  except KeyboardInterrupt:
      client.terminate()

if __name__ == '__main__':
  try:
    host = "10.13.146.101"  # Replace with server IP address if needed
    port = 9090
    # receive_data(host, port)
    listen_from_xr(host, port)
  except rospy.ROSInterruptException:
    print("program interrupted before completion")