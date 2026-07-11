# def get_lines(file_obj):
#     buffer = b""
#     while True:
#         # Read exactly 1 byte to simulate streaming network packets
#         chunk = file_obj.read(1)
#         if not chunk:
#             if buffer:
#                 yield buffer
#             break

#         buffer += chunk
#         # Look for the correct backslash network line endings
#         if buffer.endswith(b"\r\n"):
#             yield buffer[:-2]  # Strip the \r\n off the end
#             buffer = b""       # Reset buffer for the next line

#with open("mock_request.txt", "rb") as file:
    #for line in get_lines(file):
        #print(f"Parsed Line: {line.decode('utf-8')}")


def get_lines(client_sock):
    buffer = b""
    while True:
        # Sockets use .recv() instead of .read()
        chunk = client_sock.recv(1)
        if not chunk:
            if buffer:
                yield buffer
            break

        buffer += chunk
        if buffer.endswith(b"\r\n"):
            yield buffer[:-2]
            buffer = b""

import socket

server_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind('127.0.0.1', 8080)
server_socket.listen(5)
try: 
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"\n[CONNECTION] Inbound traffic detected from {client_address}")


        for line in get_lines(client_socket):
            line_str = line.decode('utf-8')
            print(f" Live Network Line: {line_str}")

        client_socket.close()

except KeyboardInterrupt:
    print("\nShutting down the server cleanly.")
    server_socket.close()
