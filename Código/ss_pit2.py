import socket
import struct
import random
import time
from datetime import datetime
import threading

HOST = 'localhost'
PORT = 9571

def generate_sensor_values():
    sensor_values = {
        'Temperatura': round(random.uniform(10.0, 100.0), 2),
        'Humidade': round(random.uniform(0.0, 100.0), 2),
        'Movimento': random.randint(0, 1),
        'Luminosidade': round(random.uniform(0.0, 1000.0), 2)
    }
    return sensor_values

def create_message(id, sensor_values):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{id} {timestamp} "

    for sensor, value in sensor_values.items():
        message += f"{sensor} {value} "

    return message.strip()

def handle_commands(sock):
    global sampling_period, sending_data

    while True:
        data = sock.recv(1024)
        command, value = struct.unpack("2sB", data)
        command = command.decode("utf-8")

        if command == "cs":
            sampling_period = value
            print(f"Recebido comando start com período de amostragem {sampling_period}")
            sending_data = True
       
        if command == "st":
            sampling_period = 0
            print("Recebido comando stop, parando o envio de dados")
            sending_data = False

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        global sampling_period, sending_data
        sampling_period = 0
        sending_data = False

        commands_thread = threading.Thread(target=handle_commands, args=(s,))
        commands_thread.start()

        id = 1

        while True:
            if sending_data and sampling_period > 0:
                sensor_values = generate_sensor_values()
                message = create_message(id, sensor_values)
                print(f"Enviando: {message}")
                s.sendall(message.encode("utf-8"))


            time.sleep(sampling_period)

if __name__ == "__main__":
    main()