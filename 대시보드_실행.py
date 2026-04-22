import webbrowser
import http.server
import socketserver
import threading
import time
import os

PORT = 8000
HTML_FILE = "주도테마_지형도.html"

def start_server():
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # 서버를 별도 스레드에서 실행
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()
    
    # 잠시 대기 후 브라우저 열기
    time.sleep(1)
    url = f"http://localhost:{PORT}/{HTML_FILE}"
    print(f"Opening dashboard: {url}")
    webbrowser.open(url)
    
    # 서버가 계속 실행되도록 유지
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped.")
