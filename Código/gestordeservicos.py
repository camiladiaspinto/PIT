import csv
import threading
import socket
from prettytable import PrettyTable
import re
from flask import Flask, jsonify, render_template, request, send_from_directory
import concurrent.futures
import time
import struct
import mysql.connector


HOST = ''  # O servidor aceita conexões em todos os IPs disponíveis
PORT_ARDUINO = 1238  # Porta a ser utilizada
PORT_SS = 9571
PORT_WS = 9689

app = Flask(__name__)
connections = []  # Lista para armazenar todas as conexões estabelecidas


# função para conectar com a base de dados
def connect_to_database():
    # Informações de conexão
    host = 'localhost'
    user = 'root'
    password = 'Eduarda.06'
    database = 'pit'

    try:
        # Estabelece a conexão com o banco de dados
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        if connection.is_connected():
            print("Conectado à base de dados.")

        return connection

    except mysql.connector.Error as error:
        print("Erro ao conectar ao MySQL:", error)


# função para fechar a conexão com a base de dados
def close_connection(connection):
    connection.close()


# função para separar dados recebidos do ss e do arduino
def separar_dados(message):
    dados = message.split()
    indices_a_remover = [3, 5, 7, 9]

    for indice in sorted(indices_a_remover, reverse=True):
        if indice < len(dados):
            del dados[indice]
    print(dados)
    return dados


# função para guardar dados na base de dados
def create_amostra(dados):
    connection = connect_to_database()
    cursor = connection.cursor()
    comando = f'INSERT INTO Amostra (data_hora, temperatura, humidade, movimento, luminosidade, id_ss) VALUES ("{dados[1] + dados[2]}", {dados[3]}, {dados[4]}, {dados[5]}, {dados[6]}, {dados[0]})'
    cursor.execute(comando)
    connection.commit()
    print("Dados enviados para a base de dados")
    cursor.close()
    close_connection(connection)

#função que queria um ss
def create_ss(id_ss):
    connection = connect_to_database()
    cursor = connection.cursor()
    comando = f'INSERT INTO SistemaSensores (id_ss) VALUES ({id_ss})'
    cursor.execute(comando)
    connection.commit()
    cursor.close()
    close_connection(connection)

def verificar_ss(id_ss):
    connection = connect_to_database()
    cursor = connection.cursor()
    comando = f'SELECT * FROM SistemaSensores WHERE id_ss = %s'
    cursor.execute(comando, (id_ss,))
    resultado = cursor.fetchall()
    cursor.close()
    if resultado:
        existe_ss = True 
    else:
        existe_ss = False
    return existe_ss


def handle_form_data(data):
    # Supondo que os dados do formulário estejam no formato 'email,senha'
    email, password = data.split(',')

    # Aqui, você pode adicionar o código para salvar os dados no banco de dados
    # Supondo que você tenha uma função `save_to_db(email, password)` que faça isso
    pass


def handle_connection(conn, addr, PORT, arduino_conn, ss_conn):
    print(f'Conexão estabelecida com {addr} no dispositivo {PORT}')

    while True:
        if PORT == PORT_ARDUINO:
            try:
                print("oi_1")
                data = conn.recv(1024)
                data.strip()
                message = data.decode('utf-8')
                print(f'Recebido do Arduino: {message}')  # eduarda a partir desta mensagem manda para a base de dados
                dados1 = separar_dados(message)
                id_ss = dados1[0]
                existe_ss = verificar_ss(id_ss)
                if existe_ss:
                    create_amostra(dados1)
                else:
                    create_ss(id_ss)
                    create_amostra(dados1)
            except Exception as e:
                print(f"Exceção ao receber dados do Arduino: {e}")



        elif PORT == PORT_SS:
            try:
                print("oi_2")
                data = conn.recv(1024)
                data.strip()
                message = data.decode('utf-8')
                print(f'Recebido do SS: {message}')
                dados2 = separar_dados(message)
                id_ss = dados2[0]
                existe = verificar_ss(id_ss)
                if existe:
                    create_amostra(dados2)
                else:
                    create_ss(id_ss)
                    create_amostra(dados2)
            except Exception as e:
                print(f"Exceção ao receber dados do SS: {e}")

        elif PORT == PORT_WS:
            try:
                print("oi_3")
                data = conn.recv(1024)
                command, sampling_period = struct.unpack("2sB", data)
                command = command.decode("utf-8")
                print(f'Recebido do Web Server: {command}, {sampling_period}')

                if command == "cs":
                    if arduino_conn is not None:
                        try:
                            arduino_conn.sendall(struct.pack("2sB", command.encode("utf-8"), sampling_period))
                            print(f'Mensagem enviada para o Arduino: {command}, {sampling_period}')
                        except Exception as e:
                            print(f"Exceção ao enviar dados para o Arduino: {e}")

                    for connection in connections:
                        if connection is not None:
                            ss_conn = connection.get('conn')
                            try:
                                ss_conn.sendall(struct.pack("2sB", command.encode("utf-8"), sampling_period))
                                print(f'Mensagem enviada para o dispositivo na porta {connection["port"]}: {command}, {sampling_period}')
                            except Exception as e:
                                print(f"Exceção ao enviar dados para o dispositivo na porta {connection['port']}: {e}")

                elif command == "st":
                    if arduino_conn is not None:
                        arduino_conn.sendall(struct.pack("2sB", command.encode("utf-8")))
                        print(f'Mensagem enviada para o Arduino: {command}')
                    for conn1 in connections:
                        ss_conn = conn1.get('conn')
                        if ss_conn is not None:
                            try:
                                ss_conn.sendall(struct.pack("2sB", command.encode("utf-8"), sampling_period))
                                print(f'Mensagem enviada para o Sistema Simulado: {command}, {sampling_period}')
                            except Exception as e:
                                print(f"Exceção ao enviar dados para o Sistema Simulado: {e}")
                else:
                    print("Mensagem inválida do Web Server")

            except Exception as e:
                print(f"Exceção ao receber dados do Web Server: {e}")
                print(len(data))


def accept_connection(s, PORT):
    while True:
        conn, addr = s.accept()
        connection = {"conn": conn, "addr": addr, "port": PORT}
        connections.append(connection)
        threading.Thread(target=handle_connection, args=(conn, addr, PORT, None, None)).start()


def main():
    s_arduino = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_arduino.bind((HOST, PORT_ARDUINO))
    s_arduino.listen()
    print(f'Servidor TCP escutando em {HOST}:{PORT_ARDUINO}')

    s_ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_ss.bind((HOST, PORT_SS))
    s_ss.listen()
    print(f'Servidor TCP escutando em {HOST}:{PORT_SS}')

    s_ws = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_ws.bind((HOST, PORT_WS))
    s_ws.listen()
    print(f'Servidor TCP escutando em {HOST}:{PORT_WS}')

    connections.clear()

    threading.Thread(target=accept_connection, args=(s_arduino, PORT_ARDUINO)).start()
    threading.Thread(target=accept_connection, args=(s_ss, PORT_SS)).start()
    threading.Thread(target=accept_connection, args=(s_ws, PORT_WS)).start()


if __name__ == '__main__':
    threading.Thread(target=main).start()
