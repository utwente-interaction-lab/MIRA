import cv2
import mediapipe as mp
import numpy as np
import socket
import serial
import time
import threading

import tensorflow as tf

# Check for available GPUs
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print("Available GPUs:", gpus)
else:
    print("No GPU found or GPU access disabled.")
print(tf.config.list_physical_devices('GPU'))

# Initialize MediaPipe and OpenCV
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Set up Arduino connection
arduino = serial.Serial('COM4', 9600)

def send_arduino_data(client_socket, arduino_send_interval, connection_active):
    last_arduino_send_time = time.time()
    while connection_active.is_set():
        if time.time() - last_arduino_send_time >= arduino_send_interval:
            last_arduino_send_time = time.time()
            try:
                if arduino.in_waiting > 0:
                    arduino_data = arduino.readline().decode('utf-8').strip()
                    client_socket.send(arduino_data.encode('utf-8'))
                arduino.reset_input_buffer()
            except Exception as e:
                print(f"Error reading/sending Arduino data: {e}")
        time.sleep(0.05)

# Function to handle the socket server connection
def socket_server_connection(connection_active):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8080))
    server_socket.listen(5)
    print("Server started, waiting for connection...")

    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr} has been established.")
    connection_active.set()  # Signal connection is active

    return server_socket, client_socket

def start_pose_detection():
    # Capture and process video frames
    cap = cv2.VideoCapture(3)

    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera resolution: {actual_width}x{actual_height}")

    # Pose detection variables
    last_pose_send_time = time.time()
    pose_send_interval = 1 / 30

    # Socket variables
    connection_active = threading.Event()

    # Start the socket server connection and get client socket
    server_socket, client_socket = socket_server_connection(connection_active)

    # Start the Arduino data thread
    arduino_send_interval = 1 / 10  # Send Arduino data at 10 Hz
    arduino_thread = threading.Thread(
        target=send_arduino_data,
        args=(client_socket, arduino_send_interval, connection_active)
    )
    arduino_thread.start()

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            capture_start = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (1080, 1920))
            capture_time = time.time() - capture_start

            process_start = time.time()
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            process_time = time.time() - process_start

            draw_start = time.time()
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            draw_time = time.time() - draw_start

            # Only send data if connection is active
            if connection_active.is_set() and results.pose_landmarks:
                current_time = time.time()
                if current_time - last_pose_send_time >= pose_send_interval:
                    last_pose_send_time = current_time
                    landmarks = results.pose_landmarks.landmark
                    pose_data = np.array([[lm.x, lm.y, lm.z] for lm in landmarks]).flatten().astype(np.float32).tobytes()
                    try:
                        client_socket.send(b"P" + pose_data)
                    except (BrokenPipeError, ConnectionResetError):
                        print("Connection lost. Waiting for reconnection...")
                        connection_active.clear()  # Reset connection status

            display_start = time.time()
            cv2.imshow('frame', frame)
            display_time = time.time() - display_start
            total_time = time.time() - capture_start

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Print timing for each stage
            print(f"Capture: {capture_time:.4f}s | "
                  f"Process: {process_time:.4f}s | Draw: {draw_time:.4f}s | "
                  f"Display: {display_time:.4f}s | Total: {total_time:.4f}")

    # Release resources and close sockets
    cap.release()
    cv2.destroyAllWindows()
    connection_active.clear()
    if client_socket:
        client_socket.close()
    if server_socket:
        server_socket.close()
    print("Server and connections closed.")

if __name__ == "__main__":
    start_pose_detection()
