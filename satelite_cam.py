# satelite_cam.py - Servidor de Câmera Satélite do Koda (Versão Ultra-Rápida / Threads)
import io
import time
import socket
import threading
import http.server
import cv2

latest_jpeg = None
camera_active = False

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def loop_captura_camera():
    global latest_jpeg, camera_active
    print("[WEBCAM] Inicializando a câmera do notebook (DirectShow)...")
    
    # cv2.CAP_DSHOW evita travamentos no Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[WEBCAM ERRO] Não foi possível abrir a câmera (verifique se outro app está usando a câmera).")
        return

    camera_active = True
    print("[WEBCAM OK] Câmera capturando quadros com sucesso!")

    while camera_active:
        ret, frame = cap.read()
        if ret:
            ret_jpg, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret_jpg:
                latest_jpeg = jpeg.tobytes()
        time.sleep(0.03) # ~30 FPS

    cap.release()
    print("[WEBCAM] Câmera encerrada.")

class CamHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global latest_jpeg
        if self.path in ['/frame.jpg', '/snapshot', '/']:
            if latest_jpeg is not None:
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(latest_jpeg)))
                self.end_headers()
                self.wfile.write(latest_jpeg)
            else:
                self.send_error(503, "Câmera ainda inicializando quadros...")
        else:
            self.send_error(404, "Endpoint não encontrado")

    def log_message(self, format, *args):
        return  # Silencia logs repetitivos do HTTP no terminal

def main():
    ip_notebook = obter_ip_local()
    porta = 8080
    
    # Inicia captura de câmera em thread separada para resposta instantânea
    threading.Thread(target=loop_captura_camera, daemon=True).start()

    print("=" * 60)
    print("      KODA AI SATELLITE CAMERA NODE v2.0 (Threading)")
    print("=" * 60)
    print(f"[IP DO NOTEBOOK]: http://{ip_notebook}:{porta}/frame.jpg")
    print("[STATUS]: Servidor de câmera ativo no notebook.")
    print("=" * 60)

    server = http.server.HTTPServer(('0.0.0.0', porta), CamHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        global camera_active
        camera_active = False
        server.server_close()

if __name__ == '__main__':
    main()
