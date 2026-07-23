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
import subprocess

status_codes = {
    200: "200 OK",
    404: "404 NOT FOUND",
    400: "400 BAD REQUEST"
}

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
    
    try:
        request_line = next(line_generator).decode('utf-8')
    except StopIteration:
        raise ValueError("Empty request stream received.")
        
    parts = request_line.split(" ")
    if len(parts) != 3:
        raise ValueError(f"Bad Start Line. Expected 3 parts, got {len(parts)}.")
        
    method, path, version = parts
    
    headers = {}
    for line in line_generator:
        line_str = line.decode('utf-8')
        if line_str == "":
            break
            
        if ":" in line_str:
            key, val = line_str.split(":", 1)
            headers[key.strip().lower()] = val.strip()
            
    return method, path, version, headers


def send_response(version, status_code_str, content_type, body_text):
    body_bytes = body_text.encode('utf-8')
    
    status_line = f"HTTP/1.1 {status_code_str}\r\n"
    response_headers = (
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    # Return raw bytes for status line + headers + body
    return status_line.encode('utf-8') + response_headers.encode('utf-8') + body_bytes


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

            # Routing predefined paths
            if path == "/hello.server":
                # 2. Run hello.py externally and capture its output!
                try:
                    result = subprocess.run(
                        ["python", "hello.py"], 
                        capture_output=True, 
                        text=True, 
                        check=True
                    )
                    hello_output = result.stdout
                    response_bytes = send_response(version, status_codes[200], "text/plain", hello_output)
                except Exception as e:
                    error_msg = f"Failed to execute script: {e}"
                    response_bytes = send_response(version, status_codes[500], "text/plain", error_msg)

            elif path == "/index.html":
                # Read directly from index.html file!
                try:
                    with open("index.html", "r", encoding="utf-8") as f:
                        html_content = f.read()
                    response_bytes = send_response(version,status_codes[200], "text/html", html_content)
                except FileNotFoundError:
                    response_bytes = send_response(version, status_codes[404], "text/html", "<h1>404 File Not Found</h1>")

            else:
                response_bytes = send_response(version,status_codes[404], "text/html", "<h1>404 Page Not Found</h1>")

            # Always send response back to socket
            client_socket.sendall(response_bytes)

        except ValueError as err:
            print(f" VALIDATION FAILED: {err}")
            err_response = send_response(status_codes[400], "text/html", f"<h1>400 Bad Request</h1><p>{err}</p>")
            client_socket.sendall(err_response)
            
        client_socket.close()

except KeyboardInterrupt:
    print("\nShutting down the server cleanly.")
    server_socket.close()