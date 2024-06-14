import socket
import threading
from flask import Flask, jsonify, render_template, request, send_from_directory, url_for, redirect
from prettytable import PrettyTable 
import mysql.connector 
from mysql.connector import Error
import csv
import os
import struct 

app = Flask(__name__)

# Variáveis globais para armazenar as conexões com o gestor de serviços
gestor_servicos_conn_lock = threading.Lock()
gestor_servicos_conns = []

#função para conectar com a base de dados
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='Eduarda.06',
            database='pit'
        )
        return connection
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None
    
#função para listar todos os ids dos SS; retorna todos os ids, em lista
def read_ss_id(connection):
    cursor = connection.cursor()
    comando = f'SELECT id_ss FROM SistemaSensores'
    cursor.execute(comando)
    resultado = cursor.fetchall()
    connection.commit()
    cursor.close() 
    return resultado



@app.route('/')
def index():
  return render_template('paginicial.html')

#função para remover um ss; procura pelo id_ss no SistemaSensoresUtilizadores para remover a conexã com o utilizador
#depois elimina no SistemaSensores
def delete_ss(connection, id_ss):
    cursor = connection.cursor()
    
    comando1 = f'DELETE FROM Amostra WHERE id_ss = "{id_ss}"'
    cursor.execute(comando1)
    connection.commit()

    comando2 = f'DELETE FROM SistemaSensoresUtilizadores WHERE id_ss = "{id_ss}"'
    cursor.execute(comando2)
    connection.commit()

    comando3 = f'DELETE FROM SistemaSensores WHERE id_ss = "{id_ss}"'
    cursor.execute(comando3)
    connection.commit()
    
    cursor.close()
@app.route('/delete_ss', methods=['POST'])
def route_delete_ss():
    id_ss = request.json.get('id_ss')
    connection = get_db_connection()  # Chama a função corretamente
    delete_ss(connection, id_ss)
    connection.close()
    return jsonify(id_ss)

def read_utilizador_id(connection):
    cursor = connection.cursor()
    comando = 'SELECT id_utilizador, email, palavrapasse FROM Utilizadores'
    cursor.execute(comando)
    resultado = cursor.fetchall()
    connection.commit()
    cursor.close() 
    return resultado

@app.route('/get-utilizador', methods=['GET'])
def get_utilizador():
    connection = get_db_connection()
    resultados = read_utilizador_id(connection)
    utilizadores = [{'id_utilizador': resultado[0], 'email': resultado[1], 'palavrapasse': resultado[2]} for resultado in resultados]
    connection.close()
    return jsonify(utilizadores)

@app.route('/get-ss-ids', methods=['GET'])
def get_ss_ids():
    connection = get_db_connection()
    ids = read_ss_id(connection)
    print(ids)
    connection.close()
    return jsonify(ids)

#função para fechar a conexão com a base de dados
def close_connection(connection):
    connection.close()

#função para adicionar um utilizador
def create_user(connection, email, palavrapasse, is_admin):
    cursor = connection.cursor()
    comando = f'INSERT INTO Utilizadores (email, palavrapasse, this_is_admin) VALUES ("{email}", "{palavrapasse}", {is_admin})'
    cursor.execute(comando)
    connection.commit()
    cursor.close()

#função de verificar se existe utilizador; true -> existe; false -> não existe
def verificar_user(connection, email):
    cursor = connection.cursor()
    comando = f'SELECT * FROM Utilizadores WHERE email = %s'
    cursor.execute(comando, (email,))
    resultado = cursor.fetchall()
    cursor.close()
    if resultado:
        verificar = True 
    else:
        verificar = False
    return verificar

#função de verificar se exixte utilizador; true -> existe; false -> não existe
def verificar_login(connection,email, password):
    cursor = connection.cursor()
    comando = 'SELECT * FROM Utilizadores WHERE email = %s AND palavrapasse = %s'
    cursor.execute(comando, (email, password,))
    resultado = cursor.fetchall()
    print(f"resulta: {resultado}")
    cursor.close()
    if resultado:
        verificar = True
        this_is_admin = resultado[0][3]
    else:
        verificar = False
        this_is_admin = None
    return verificar, this_is_admin


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/pagina-administrador')
def pagina_administrador():
    return render_template('index.html')

@app.route('/pagina-user')
def pagina_user():
    return render_template('página_do_user.html')



# Variável global para armazenar o email do usuário logado
email_logado = None

@app.route('/formulario', methods=['POST'])
def formulario():
    global email_logado  # Acessa a variável global

    connection = get_db_connection()
    data = request.json
    if data and 'action' in data and data['action'] == 'submit':
        email = data['email']
        password = data['palavrapasse']

        try:
            existe_user, this_is_admin = verificar_login(connection, email, password)

            if existe_user:
                email_logado = email  # Armazena o email do usuário logado na variável global
                if this_is_admin == 1:
                    mensagem = 'pagina admin'
                elif this_is_admin == 0:
                    mensagem = 'pagina utilizador'
            else:
                mensagem = 'Dados inválidos'
            
        except mysql.connector.Error as error:
            print(f"Erro de banco de dados: {error}")
            mensagem = 'Erro de banco de dados'

        finally:
            if connection.is_connected():
                connection.close()

        return jsonify({'message': mensagem})
    else:
        return jsonify({'message': 'Dados inválidos'})


@app.route ('/registar', methods =['POST'])
def registar():
    connection = get_db_connection()
    data = request.json
    if data and 'action' in data and data['action'] == 'registar':
        email = data['email']
        password = data['password']
        print(f"Mensagem recebida do cliente: {email} {password}")
        
        try:
            existe_user = verificar_user(connection, email)
            print(f"existe user?", existe_user)
            if existe_user == False: 
                create_user(connection, email,password,False)
                mensagem = 'Registo realizado com sucesso'
            elif existe_user == True: 
                mensagem = 'O utilizador já existe'

        except mysql.connector.Error as error:
            # Lidar com erros de conexão ou consulta ao banco de dados
            print(f"Erro de banco de dados: {error}")
            mensagem = 'Erro de banco de dados'

        finally:
            # Fechar a conexão com o banco de dados
            if connection.is_connected():
                connection.close()
        
        # Envie a mensagem para o gestor de serviços
        #Main('fm', email, password)
        return jsonify({'message': mensagem})
    else:
        return jsonify({'message': 'Dados inválidos'})
    

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    if data and 'action' in data and data['action'] == 'start':
        sampling_period = data['sampling_period']
        print(f"Botão Start clicado com período de amostragem: {sampling_period}")

        send_message_to_gestor_servicos("cs", sampling_period)

        return jsonify({'message': 'Botão Start clicado'})
    else:
        return jsonify({'message': 'Dados inválidos'})


@app.route('/stop', methods=['POST'])
def stop():
    data = request.json
    if data and 'action' in data and data['action'] == 'stop':
        print(f"Botão Stop")

        send_message_to_gestor_servicos("st", 0)
        return jsonify({'message': 'Botão Stop clicado'})
    else:
        return jsonify({'message': 'Dados inválidos'})
    
    
# Funções user
    

@app.route('/verificar-id', methods=['POST'])
def verificar_id():
    connection = get_db_connection()
    data = request.json
    if data and 'id_ss' in data:
        id_ss = data['id_ss']

        # Verificar se o ID contém apenas números
        if not id_ss.isdigit():
            mensagem = 'O ID deve conter apenas números'
            connection.close()
            return jsonify({'message': mensagem})

        ids_disponiveis = ss_disponiveis(connection)
        ids_disponiveis = [int(id) for id in ids_disponiveis]
        if int(id_ss) in ids_disponiveis:
            email = email_logado  # Obtém o email do usuário logado da variável global
            if email:
                id_utilizador = verificar_user_id(connection, email)
                if id_utilizador is not None:
                    adicionar_id_utilizador(connection, id_ss, id_utilizador)
                    mensagem = f"ID {id_ss} associado ao utilizador"
                else:
                    mensagem = f"Não foi possível obter o ID do utilizador"
            else:
                mensagem = f"Email do utilizador não encontrado"
        else:
            mensagem = f"ID {id_ss} inválido"
    else:
        mensagem = 'Dados inválidos'

    connection.close()
    return jsonify({'message': mensagem})




def verificar_user_id(connection, email):
    cursor = connection.cursor()
    comando = f'SELECT id_utilizador FROM Utilizadores WHERE email = %s'
    cursor.execute(comando, (email,))
    resultado = cursor.fetchone()
    cursor.close()
    if resultado:
        id_utilizador = resultado[0]
    else:
        id_utilizador = None
    return id_utilizador


def get_ss_ids_utilizador(connection, email):
    cursor = connection.cursor()
    comando = '''
        SELECT su.id_ss 
        FROM SistemaSensoresUtilizadores su 
        INNER JOIN Utilizadores u ON su.id_utilizador = u.id_utilizador 
        WHERE u.email = %s
    '''
    cursor.execute(comando, (email,))
    ids = cursor.fetchall()
    cursor.close()
    return ids

@app.route('/get-ids-utilizador', methods=['GET'])
def get_ids_utilizador():
    global email_logado

    if email_logado:
        connection = get_db_connection()
        ids = get_ss_ids_utilizador(connection, email_logado)
        connection.close()
        return jsonify(ids)
    else:
        return jsonify([])

@app.route('/get-amostra-data', methods=['GET'])
def get_amostra_data():
    id_ss = request.args.get('id_ss')

    connection = get_db_connection()
    resultado = read_amostra(connection, id_ss)
    connection.close()
    amostra_data = {
        'timeStamp': resultado[5],
        'temperatura': resultado[4],
        'humidade': resultado[0],
        'movimento': resultado[3],
        'luminosidade': resultado[2],
        'idSelecionado': resultado[1]
    }
    return jsonify(amostra_data)

def read_amostra(connection, id_ss):
    cursor = connection.cursor()
    comando = 'SELECT data_hora, temperatura, humidade, movimento, luminosidade, id_ss FROM Amostra WHERE id_ss = %s ORDER BY data_hora DESC LIMIT 1'
    cursor.execute(comando, (id_ss,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado





@app.route('/ids_disponiveis', methods=['GET'])
def obter_ids_disponiveis():
    connection = get_db_connection()  # Estabelece a conexão com o banco de dados
    ids_disponiveis = ss_disponiveis(connection)  # Chama a função ss_disponiveis passando a conexão
    connection.close()
    print(ids_disponiveis)
    # Retorna um objeto JSON contendo os IDs disponíveis
    return jsonify(ids_disponiveis)



#função para ler todos os id_ss da tabela SistemaSensores
def read_ss(connection):
    cursor = connection.cursor()
    comando = f'SELECT id_ss FROM SistemaSensores'
    cursor.execute(comando)
    resultado = cursor.fetchall()
    connection.commit()
    cursor.close()
    return resultado

#função para ler os id_ss da tabela SistemaSensoresUtilizadores -> associação utilizador-ss
def read_ss_utilizadores(connection):
    cursor = connection.cursor()
    comando = f'SELECT id_ss FROM SistemaSensoresUtilizadores'
    cursor.execute(comando)
    resultado = cursor.fetchall()
    print(resultado)
    connection.commit()
    cursor.close()
    return resultado

#função que retorna a lista de id_ss disponiveis para serem associados aos utilizadores
def ss_disponiveis(connection):
    id_ss_utilizadores = [row[0] for row in read_ss_utilizadores(connection)]
    print(f"id_ss_utilizadores", id_ss_utilizadores)
    id_ss_sensores = [row[0] for row in read_ss(connection)]
    print(f"id_ss_sensores", id_ss_sensores)

    non_common_id_ss = []
    for id_ss in id_ss_sensores:
        if id_ss not in id_ss_utilizadores:
            non_common_id_ss.append(id_ss)
    
    connection.commit()
    return non_common_id_ss

#função para associar o id_ss ao id_utilizador
def adicionar_id_utilizador(connection, id_ss, id_utilizador):
    cursor = connection.cursor()
    comando = f"INSERT INTO SistemaSensoresUtilizadores (id_ss, id_utilizador) VALUES ({id_ss}, {id_utilizador})"
    cursor.execute(comando)
    connection.commit()
    cursor.close()




#função para ver a quais id_ss o utilizador está associado
def lista_ss_utilizador(id_utilizador,connection):
    cursor = connection.cursor()
    comando = f'SELECT id_ss FROM SistemaSensoresUtilizadores WHERE id_utilizador = {id_utilizador}'
    cursor.execute(comando)
    resultado = cursor.fetchall()
    cursor.close()
    return resultado


def create_byte_message(command, value):
    if command == "st":
        return struct.pack("2sB", command.encode("utf-8"), 0)
    else:
        return struct.pack("2sB", command.encode("utf-8"), int(value))

def parse_byte_message(byte_message):
    if len(byte_message) == 0:
        return None, None
    elif len(byte_message) == 2:
        decoded_message = byte_message.decode("utf-8")
        command, value = decoded_message.split(" ")
        return command, value
    
def send_message_to_gestor_servicos(command, value):
    with gestor_servicos_conn_lock:
        for conn in gestor_servicos_conns:
            if conn.fileno() != -1:  # Verifica se a conexão ainda está aberta
                byte_message = create_byte_message(command, value)
                try:
                    conn.sendall(byte_message)
                except Exception as e:
                    print(f"Exceção ao receber dados do gestor de serviços: {e}")
            else:
                print("Conexão inválida com o gestor de serviços")

def connect_to_gestor_servicos():
    global gestor_servicos_conns

    host = '127.0.0.1'
    port = 9689

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((host, port))
    print("Conexão estabelecida com o gestor de serviços")

    with gestor_servicos_conn_lock:
        print("Adiconando conexão à lista do gestor de serviços.")
        gestor_servicos_conns.append(conn)

@app.before_first_request
def initialize():
    connect_to_gestor_servicos()
    

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)