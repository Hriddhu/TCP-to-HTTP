import socket
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


import socket

def get_lines(client_sock):
    buffer = b""
    while True:
        chunk = client_sock.recv(1)
        if not chunk:
            if buffer:
                yield buffer
            break
        buffer += chunk
        if buffer.endswith(b"\r\n"):
            yield buffer[:-2]
            buffer = b""

def parse_http_request(client_sock):
    line_generator = get_lines(client_sock)
    
    # First call: Grab and validate the Request Line
    try:
        request_line = next(line_generator).decode('utf-8')
    except StopIteration:
        raise ValueError("Empty request stream received.")
        
    parts = request_line.split(" ")
    if len(parts) != 3:
        raise ValueError(f"Bad Start Line. Expected 3 parts, got {len(parts)}.")
        
    method, path, version = parts
    
    # Second call onwards: Loop through and collect headers
    headers = {}
    for line in line_generator:
        line_str = line.decode('utf-8')
        
        # Stopping when hit the empty line delimiter (\r\n\r\n)
        if line_str == "":
            break
            
        if ":" in line_str:
            key, val = line_str.split(":", 1)
            headers[key.strip().lower()] = val.strip()
            
    return method, path, version, headers

# Runtime listener
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('127.0.0.1', 8080))
server_socket.listen(5)
print("Parsing Engine active on http://127.0.0.1:8080 ...")

try:
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"\n[TRAFFIC] Inbound connection from {client_address}")
        
        try:
            method, path, version, headers = parse_http_request(client_socket)
            print(f" SUCCESS: Parsed successfully!")
            print(f"   -> Method:  {method}")
            print(f"   -> Path:    {path}")
            print(f"   -> Headers: {headers}")
        except ValueError as err:
            print(f" VALIDATION FAILED: {err}")
            
        client_socket.close()

except KeyboardInterrupt:
    print("\nShutting down the server cleanly.")
    server_socket.close()
