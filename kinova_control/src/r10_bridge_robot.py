import rospy
import re

import socket
import select
import time

def extract_last_packet(data):
  # Find all occurrences of packets using regex
  packets = re.findall(r'\d+:\[[^\]]+\]', data)
  
  if packets:
      # Return the last packet from the list
      return packets[-1]
  return None

def receive_data(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.setblocking(0)  # Set the socket to non-blocking mode
        while True:
            # Use select to check for incoming data
            readable, _, _ = select.select([s], [], [], 10)  # Timeout of 1 second
            if readable:
                data = s.recv(1024).decode()
                if data:
                    print(f"Received: {data}")
                    # <RTEN> get timestamp here ====================================================
                    data_temp = extract_last_packet(data)
                    timestamp, _ = data_temp.split(":", 1) # split only once for the first :
                    timestamp = int(timestamp)
                    print("one-way delay(ms): ", round(time.time()*1000)-timestamp)
                    # End ==========================================================================

                    with open('data', 'w') as file:
                        file.write(str(data))  # Convert list to string and write it to the file
                else:
                    print("Connection closed by the server")
                    break
            else:
                print("No new data, still listening...")
            time.sleep(1/10)  # Adjust sleep duration as needed

if __name__ == '__main__':
  try:
    host = "192.168.176.76"  # Replace with server IP address if needed
    port = 5000
    # print(round(time.time() * 1000))
    receive_data(host, port)
  except rospy.ROSInterruptException:
    print("program interrupted before completion")