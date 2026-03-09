import socket
import threading
import json
import time
from authentication import register, login, voted, init_db
from Main import add_vote, encrypt_vote, blockchain, counter, validate_chain, get_vote

# Server configuration
HOST = '127.0.0.1'
PORT = 65432

# Initialize database
init_db()

def handle_client(conn, addr):
    print(f"Connected: {addr}")
    current_user_id = None
    username_logged_in = None

    try:
        while True:
            data = conn.recv(2048)
            if not data:
                break

            try:
                command = json.loads(data.decode())
            except json.JSONDecodeError:
                conn.sendall(b"INVALID_JSON")
                continue

            action = command.get("action")

            # REGISTER
            if action == "REGISTER":
                username = command.get("username")
                password = command.get("password")
                try:
                    register(username=username, password=password)
                    conn.sendall(b"REGISTERED")
                except Exception as e:
                    conn.sendall(f"ERROR: {str(e)}".encode())

            # LOGIN
            elif action == "LOGIN":
                username = command.get("username")
                password = command.get("password")
                result = login(username=username, password=password)
                if result[0] is not None:
                    current_user_id = result[0]   # <-- ensures subsequent VOTE works
                    username_logged_in = username
                    conn.sendall(b"LOGGED_IN")
                else:
                    conn.sendall(b"LOGIN_FAILED")

            # VOTE
            elif action == "VOTE":
                if current_user_id is None:
                    conn.sendall(b"NOT_LOGGED_IN")
                    continue

                vote_choice = command.get("vote")
                if vote_choice not in ["A", "B", "C", "D", "E"]:
                    conn.sendall(b"INVALID_VOTE")
                    continue

                # Encrypt, sign, and store the vote
                encrypted_vote = encrypt_vote(vote_choice)
                add_vote(encrypted_vote, signature=None)  # assuming no signature for automated votes
                voted(current_user_id)
                counter.add_vote(vote_choice)  # update tally
                conn.sendall(b"VOTE_ACCEPTED")

            # EXIT
            elif action == "EXIT":
                conn.sendall(b"BYE")
                break

            else:
                conn.sendall(b"UNKNOWN_COMMAND")

    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        conn.close()
        print(f"Disconnected: {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()