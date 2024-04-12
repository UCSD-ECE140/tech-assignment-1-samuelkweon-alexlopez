import os
import json
from dotenv import load_dotenv

import paho.mqtt.client as paho
from paho import mqtt
import time
import threading


# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)


# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """

    print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    print(f"Received message on {msg.topic} with QoS {msg.qos}")
    payload = msg.payload.decode()
    if 'game_state' in msg.topic:
        game_state = json.loads(payload)
        process_game_state(game_state)
    elif 'scores' in msg.topic:
        print(f"Scores: {payload}")
    else:
        print(f"Message: {payload}")


def user_input_control(client, player_name, lobby_name):
    try:
        while True:
            move = input(f"{player_name}, enter your move (UP, DOWN, LEFT, RIGHT or STOP to end): ").upper()
            if move in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                client.publish(f"games/{lobby_name}/{player_name}/move", move)
            elif move == 'STOP':
                client.publish(f"games/{lobby_name}/start", "STOP")
                break
            else:
                print("Invalid move. Please try again.")
    except KeyboardInterrupt:
        print("Game interrupted.")

def process_game_state(state):
    
    try:
        grid = [[' ' for _ in range(5)] for _ in range(5)]  # 5x5 grid initialized with empty spaces
        center_x, center_y = 2, 2  # Center of the grid

        # Set player's position at the center
        grid[center_x][center_y] = 'P'

        # Place coins (assuming 'coins' are given as a list of positions)
        for coin in state.get('coins', []):
            x, y = coin
            grid[x - state['currentPosition'][0] + center_x][y - state['currentPosition'][1] + center_y] = 'C'

        # Place walls
        for wall in state.get('walls', []):
            x, y = wall
            if 0 <= x - state['currentPosition'][0] + center_x < 5 and 0 <= y - state['currentPosition'][1] + center_y < 5:
                grid[x - state['currentPosition'][0] + center_x][y - state['currentPosition'][1] + center_y] = 'W'

        # Print the grid
        for row in grid:
            print(' '.join(row))
        print("\n")

    except Exception as e:
        print("Error processing game state:", e)


if __name__ == '__main__':
    load_dotenv(dotenv_path='./credentials.env')
    
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="Player1", userdata=None, protocol=paho.MQTTv5)
    
    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)

    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
    client.on_message = on_message
    client.on_publish = on_publish # Can comment out to not print when publishing to topics

    lobby_name = "TestLobby"
    player_1 = "Player1"
    player_2 = "Player2"
    player_3 = "Player3"

    client.subscribe(f"games/{lobby_name}/lobby")
    client.subscribe(f'games/{lobby_name}/+/game_state')
    client.subscribe(f'games/{lobby_name}/scores')

    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'ATeam',
                                            'player_name' : player_1}))
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'BTeam',
                                            'player_name' : player_2}))
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                        'team_name':'BTeam',
                                        'player_name' : player_3}))

    time.sleep(1) # Wait a second to resolve game start
    client.publish(f"games/{lobby_name}/start", "START")
    client.publish(f"games/{lobby_name}/{player_1}/move", "UP")
    client.publish(f"games/{lobby_name}/{player_2}/move", "DOWN")
    client.publish(f"games/{lobby_name}/{player_3}/move", "DOWN")
    client.publish(f"games/{lobby_name}/start", "STOP")

    player_input_thread = threading.Thread(target=user_input_control, args=(client, player_1, lobby_name))
    player_input_thread.start()

    client.loop_forever()
