import sys
import os
import io
import time
import math
import random
import ctypes
import numpy as np
import pygame
import psutil
import pyautogui
import win32api
import win32con
import win32gui

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int)
    ]

def aplicar_transparencia_widget(hwnd, cor_chroma):
    try:
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX | win32con.WS_SYSMENU | win32con.WS_BORDER)
        style |= win32con.WS_POPUP
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

        exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        exstyle &= ~(win32con.WS_EX_WINDOWEDGE | win32con.WS_EX_CLIENTEDGE | win32con.WS_EX_DLGMODALFRAME | win32con.WS_EX_STATICEDGE)
        exstyle |= (win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, exstyle)

        r, g, b = cor_chroma
        colorkey = win32api.RGB(r, g, b)
        win32gui.SetLayeredWindowAttributes(hwnd, colorkey, 0, win32con.LWA_COLORKEY)

        policy = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 2, ctypes.byref(policy), ctypes.sizeof(policy))
    except Exception as e:
        print(f"[HUD DWM WARN] Erro ao aplicar estilo transparente: {e}")

class Particle:
    def __init__(self, center):
        self.center = center
        self.reset()

    def reset(self):
        self.angle = random.uniform(0, math.tau)
        self.dist = random.uniform(60, 160)
        self.speed = random.uniform(0.01, 0.03)
        self.size = random.uniform(2, 4)
        self.alpha = random.randint(100, 255)

    def update(self, audio_amp=0.0):
        self.angle += self.speed * (1.0 + audio_amp * 4.0)
        self.dist += math.sin(self.angle * 2) * 0.3
        self.x = self.center[0] + self.dist * math.cos(self.angle)
        self.y = self.center[1] + self.dist * math.sin(self.angle)

    def draw(self, surface, color):
        glow_surf = pygame.Surface((int(self.size*4), int(self.size*4)), pygame.SRCALPHA)
        c = (color[0], color[1], color[2], int(self.alpha * 0.6))
        pygame.draw.circle(glow_surf, c, (int(self.size*2), int(self.size*2)), int(self.size*2))
        pygame.draw.circle(glow_surf, (255, 255, 255, self.alpha), (int(self.size*2), int(self.size*2)), int(self.size*0.8))
        surface.blit(glow_surf, (self.x - self.size*2, self.y - self.size*2))

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    )

class HudKoda:
    def __init__(self, config):
        pygame.init()
        pygame.mixer.init()
        
        self.config = config
        self.modo_widget = False
        self.COR_CHROMA = (255, 0, 255) 
        self.MARGEM = 30 
        self.modulo_ativo = "SISTEMA_IDLE"
        self.camera_preview_surf = None
        
        larg = getattr(config, 'LARGURA', 1280)
        alt = getattr(config, 'ALTURA', 720)
        self._configurar_janela(larg, alt, tela_cheia=True)

        self.fonte_hud = pygame.font.SysFont("Verdana", 20, bold=True)
        self.fonte_pequena = pygame.font.SysFont("Consolas", 10)
        self.fonte_log = pygame.font.SysFont("Consolas", 12)
        self.fonte_stats = pygame.font.SysFont("Consolas", 12, bold=True)
        
        self.ang = 0
        self.centro = (larg // 2, alt // 2 - 20)
        self.current_color = (0, 220, 255)
        self.target_color = (0, 220, 255)

        self.particles = [Particle(self.centro) for _ in range(35)]

    def atualizar_preview_camera(self, image_bytes_ou_surf):
        try:
            if isinstance(image_bytes_ou_surf, (bytes, bytearray)):
                surf = pygame.image.load(io.BytesIO(image_bytes_ou_surf))
            else:
                surf = image_bytes_ou_surf

            self.camera_preview_surf = pygame.transform.smoothscale(surf, (220, 140))
            print("[HUD] Preview de imagem da câmera atualizado com sucesso no painel!")
        except Exception as e:
            print(f"[HUD WARN] Erro ao carregar preview da imagem no HUD: {e}")

    def _configurar_janela(self, larg, alt, tela_cheia):
        pygame.display.quit()
        pygame.display.init()
        
        if tela_cheia:
            self.tela = pygame.display.set_mode((larg, alt), pygame.DOUBLEBUF)
        else:
            self.tela = pygame.display.set_mode((larg, alt), pygame.NOFRAME)

        pygame.display.set_caption("KODA AI v2.0 | JARVIS Core Interface")
        try:
            caminho_icone = resource_path("koda_icon.png")
            if os.path.exists(caminho_icone):
                icone = pygame.image.load(caminho_icone)
                pygame.display.set_icon(icone)
        except Exception as e:
            print(f"[HUD WARN] Ícone não carregado: {e}")

    def alternar_modo(self, minimizado):
        self.modo_widget = minimizado
        larg = getattr(self.config, 'LARGURA', 1280)
        alt = getattr(self.config, 'ALTURA', 720)

        if self.modo_widget:
            self._configurar_janela(150, 150, tela_cheia=False)
            hwnd = pygame.display.get_wm_info()["window"]
            aplicar_transparencia_widget(hwnd, self.COR_CHROMA)
            screen_w, screen_h = pyautogui.size()
            flags = win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, screen_w - 180, 80, 150, 150, flags)
        else:
            self._configurar_janela(larg, alt, tela_cheia=True)
            hwnd = pygame.display.get_wm_info()["window"]
            exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, exstyle & ~win32con.WS_EX_LAYERED)
            win32gui.RedrawWindow(hwnd, None, None, win32con.RDW_INVALIDATE | win32con.RDW_UPDATENOW)
            screen_w, screen_h = pyautogui.size()
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, screen_w // 2 - larg // 2, screen_h // 2 - alt // 2, larg, alt, win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED)

    def desenhar_glow_circle(self, surface, color, center, radius, width=2, alpha=80):
        glow_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        c_glow = (color[0], color[1], color[2], alpha)
        c_glow_outer = (color[0], color[1], color[2], alpha // 3)
        pygame.draw.circle(glow_surf, c_glow_outer, (radius + 10, radius + 10), radius + 4, width + 4)
        pygame.draw.circle(glow_surf, c_glow, (radius + 10, radius + 10), radius, width + 2)
        surface.blit(glow_surf, (center[0] - radius - 10, center[1] - radius - 10))

    def desenhar_moldura_hud(self, cor):
        larg = getattr(self.config, 'LARGURA', 1280)
        alt = getattr(self.config, 'ALTURA', 720)
        m = self.MARGEM
        t = 35
        
        self.desenhar_glow_circle(self.tela, cor, (m, m), 4, 2, 60)
        self.desenhar_glow_circle(self.tela, cor, (larg-m, m), 4, 2, 60)
        self.desenhar_glow_circle(self.tela, cor, (m, alt-m), 4, 2, 60)
        self.desenhar_glow_circle(self.tela, cor, (larg-m, alt-m), 4, 2, 60)

        pygame.draw.line(self.tela, cor, (m, m), (m+t, m), 2)
        pygame.draw.line(self.tela, cor, (m, m), (m, m+t), 2)
        pygame.draw.line(self.tela, cor, (larg-m, m), (larg-m-t, m), 2)
        pygame.draw.line(self.tela, cor, (larg-m, m), (larg-m, m+t), 2)
        pygame.draw.line(self.tela, cor, (m, alt-m), (m+t, alt-m), 2)
        pygame.draw.line(self.tela, cor, (m, alt-m), (m, alt-m-t), 2)
        pygame.draw.line(self.tela, cor, (larg-m, alt-m), (larg-m-t, alt-m), 2)
        pygame.draw.line(self.tela, cor, (larg-m, alt-m), (larg-m, alt-m-t), 2)

    def desenhar_equalizador_audio(self, audio_visual, x, y, largura, altura, cor):
        num_barras = 16
        largura_barra = largura // num_barras
        
        pygame.draw.rect(self.tela, (15, 20, 35), (x, y, largura, altura))
        pygame.draw.rect(self.tela, cor, (x, y, largura, altura), 1)
        self.tela.blit(self.fonte_stats.render("AUDIO SPECTRUM", True, (150, 150, 150)), (x + 10, y + 5))

        for i in range(num_barras):
            idx = int((i / num_barras) * (len(audio_visual) - 1)) if len(audio_visual) > 0 else 0
            val = abs(audio_visual[idx]) if len(audio_visual) > 0 else 0
            h_bar = int(min(1.0, val * 3.5) * (altura - 25))
            h_bar = max(3, h_bar)

            bx = x + 10 + i * (largura_barra - 1)
            by = y + altura - 10 - h_bar

            cor_topo = (255, 255, 255) if h_bar > (altura - 35) else cor
            pygame.draw.rect(self.tela, (cor[0]//3, cor[1]//3, cor[2]//3), (bx, by, largura_barra - 3, h_bar))
            pygame.draw.rect(self.tela, cor_topo, (bx, by, largura_barra - 3, 2))

    def desenhar_frame_camera_satelite(self, x, y, largura, altura, cor):
        pygame.draw.rect(self.tela, (15, 20, 35), (x, y, largura, altura))
        pygame.draw.rect(self.tela, cor, (x, y, largura, altura), 1)
        self.tela.blit(self.fonte_stats.render("[ SATELLITE CAM CAPTURE ]", True, cor), (x + 10, y + 5))

        x_inner = x + 10
        y_inner = y + 25
        w_inner = largura - 20
        h_inner = altura - 35

        if self.camera_preview_surf:
            self.tela.blit(self.camera_preview_surf, (x_inner, y_inner))
            pygame.draw.rect(self.tela, cor, (x_inner, y_inner, w_inner, h_inner), 1)
        else:
            pygame.draw.rect(self.tela, (8, 12, 22), (x_inner, y_inner, w_inner, h_inner))
            pygame.draw.rect(self.tela, (40, 50, 70), (x_inner, y_inner, w_inner, h_inner), 1)
            
            for gx in range(x_inner, x_inner + w_inner, 20):
                pygame.draw.line(self.tela, (20, 30, 45), (gx, y_inner), (gx, y_inner + h_inner), 1)
            for gy in range(y_inner, y_inner + h_inner, 20):
                pygame.draw.line(self.tela, (20, 30, 45), (x_inner, gy), (x_inner + w_inner, gy), 1)

            surf_msg = self.fonte_pequena.render("SATELLITE CAM AGUARDANDO CAPTURA...", True, (120, 150, 170))
            self.tela.blit(surf_msg, surf_msg.get_rect(center=(x_inner + w_inner//2, y_inner + h_inner//2)))

    def desenhar(self, audio_visual, cor_alvo, status_texto, log_eventos, modulo="SISTEMA_IDLE"):
        self.modulo_ativo = modulo
        larg = getattr(self.config, 'LARGURA', 1280)
        alt = getattr(self.config, 'ALTURA', 720)
        cor_fundo = getattr(self.config, 'COR_FUNDO', (5, 10, 15))
        cor_texto = getattr(self.config, 'COR_TEXTO', (200, 255, 240))

        self.target_color = cor_alvo
        self.current_color = lerp_color(self.current_color, self.target_color, 0.08)
        cor = self.current_color

        audio_amp = float(np.max(np.abs(audio_visual))) if len(audio_visual) > 0 else 0.0

        # Modo Widget (Miniaturizado)
        if self.modo_widget:
            self.tela.fill(self.COR_CHROMA) 
            centro_widget = (75, 75)
            
            self.ang += 0.03
            pulso_mini = math.sin(time.time() * 4) * 3
            r_base_mini = 45 + pulso_mini + (audio_amp * 20)
            
            for i in range(0, 360, 30):
                pygame.draw.arc(self.tela, cor, (centro_widget[0]-r_base_mini+8, centro_widget[1]-r_base_mini+8, (r_base_mini-8)*2, (r_base_mini-8)*2), math.radians(i-self.ang*100), math.radians(i+15-self.ang*100), 2)
            
            pygame.draw.circle(self.tela, (cor[0]//3, cor[1]//3, cor[2]//3), centro_widget, int(r_base_mini), 1)
            pygame.draw.arc(self.tela, cor, (centro_widget[0]-r_base_mini, centro_widget[1]-r_base_mini, r_base_mini*2, r_base_mini*2), self.ang, self.ang + math.pi, 2)
            
            for i in range(0, 360, 90):
                pygame.draw.arc(self.tela, cor, (centro_widget[0]-r_base_mini-6, centro_widget[1]-r_base_mini-6, (r_base_mini+6)*2, (r_base_mini+6)*2), math.radians(i+self.ang*50), math.radians(i+45+self.ang*50), 1)

            pontos_onda = []
            base_onda_mini = 25
            for i in range(100):
                a = 2 * math.pi * (i / 100)
                idx = int((i / 100) * (len(audio_visual) - 1)) if len(audio_visual) > 0 else 0
                val = abs(audio_visual[idx]) if len(audio_visual) > 0 else 0
                d = base_onda_mini + int(val * 40)
                pontos_onda.append((centro_widget[0] + int(d * math.cos(a)), centro_widget[1] + int(d * math.sin(a))))
            if len(pontos_onda) > 2:
                pygame.draw.polygon(self.tela, (cor[0]//5, cor[1]//5, cor[2]//5), pontos_onda, 0)
                pygame.draw.polygon(self.tela, cor, pontos_onda, 2)
            pygame.draw.circle(self.tela, cor, centro_widget, base_onda_mini - 5, 1)
                
            pygame.display.flip()
            return

        # Modo Tela Cheia - Painel Simétrico Balanceado
        self.tela.fill(cor_fundo)
        
        for x in range(0, larg, 40):
            pygame.draw.line(self.tela, (12, 18, 28), (x, 0), (x, alt), 1)
        for y in range(0, alt, 40):
            pygame.draw.line(self.tela, (12, 18, 28), (0, y), (larg, y), 1)

        pygame.draw.line(self.tela, (20, 35, 50), (0, self.centro[1]), (larg, self.centro[1]), 1)
        pygame.draw.line(self.tela, (20, 35, 50), (self.centro[0], 0), (self.centro[0], alt), 1)
        
        self.desenhar_moldura_hud(cor)

        for p in self.particles:
            p.update(audio_amp)
            p.draw(self.tela, cor)

        self.ang += 0.03
        pulso = math.sin(time.time() * 4) * 5 + (audio_amp * 30)
        r_base = 115 + pulso

        self.desenhar_glow_circle(self.tela, cor, self.centro, int(r_base), 3, 90)
        
        radar_angle = self.ang * 2
        rx = self.centro[0] + int((r_base + 35) * math.cos(radar_angle))
        ry = self.centro[1] + int((r_base + 35) * math.sin(radar_angle))
        pygame.draw.line(self.tela, (cor[0]//2, cor[1]//2, cor[2]//2), self.centro, (rx, ry), 1)
        
        for i in range(0, 360, 30):
            pygame.draw.arc(self.tela, cor, (self.centro[0]-r_base+20, self.centro[1]-r_base+20, (r_base-20)*2, (r_base-20)*2), math.radians(i-self.ang*100), math.radians(i+15-self.ang*100), 2)
        
        pygame.draw.circle(self.tela, (cor[0]//3, cor[1]//3, cor[2]//3), self.centro, int(r_base), 1)
        pygame.draw.arc(self.tela, cor, (self.centro[0]-r_base, self.centro[1]-r_base, r_base*2, r_base*2), self.ang, self.ang + math.pi, 4)

        pontos_onda = []
        base_onda = 75
        for i in range(100):
            a = 2 * math.pi * (i / 100)
            idx = int((i / 100) * (len(audio_visual) - 1)) if len(audio_visual) > 0 else 0
            val = abs(audio_visual[idx]) if len(audio_visual) > 0 else 0
            d = base_onda + int(val * 150)
            pontos_onda.append((self.centro[0] + int(d * math.cos(a)), self.centro[1] + int(d * math.sin(a))))
        
        if len(pontos_onda) > 2:
            pygame.draw.polygon(self.tela, (cor[0]//5, cor[1]//5, cor[2]//5), pontos_onda, 0)
            pygame.draw.polygon(self.tela, cor, pontos_onda, 2)
        pygame.draw.circle(self.tela, cor, self.centro, base_onda - 10, 1)

        if status_texto:
            surf_txt = self.fonte_hud.render(f"[ {status_texto} ]", True, cor)
            self.tela.blit(surf_txt, surf_txt.get_rect(center=(self.centro[0], self.centro[1] + r_base + 35)))
        
        self.tela.blit(self.fonte_pequena.render(f"RAD: {r_base:.1f} | ANG: {self.ang:.2f}", True, cor_texto), (self.centro[0] + r_base + 25, self.centro[1]))
        self.tela.blit(self.fonte_pequena.render(f"JARVIS_v2.0_CORE", True, cor_texto), (self.centro[0] - r_base - 110, self.centro[1]))

        # =========================================================================
        # LAYOUT BALANCEADO E SIMÉTRICO DA INTERFACE HUD
        # =========================================================================

        # --- COLUNA ESQUERDA (Superior: Active Module | Logo Abaixo: Satellite Cam) ---
        x_left = self.MARGEM + 10
        w_col_left = 240

        # 1. Active Module Box
        pygame.draw.rect(self.tela, (15, 20, 35), (x_left, self.MARGEM + 10, w_col_left, 50))
        pygame.draw.rect(self.tela, cor, (x_left, self.MARGEM + 10, w_col_left, 50), 1)
        self.tela.blit(self.fonte_stats.render("ACTIVE_MODULE:", True, (150, 150, 150)), (x_left + 10, self.MARGEM + 15))
        self.tela.blit(self.fonte_log.render(self.modulo_ativo, True, cor), (x_left + 10, self.MARGEM + 35))

        # 2. Quadro da Câmera Satélite (Posicionado perfeitamente na Coluna Esquerda)
        self.desenhar_frame_camera_satelite(x_left, self.MARGEM + 70, w_col_left, 175, cor)


        # --- COLUNA DIREITA (Superior: Hardware Stats CPU/RAM | Logo Abaixo: Status do Sistema) ---
        w_col_right = 240
        x_right = larg - self.MARGEM - w_col_right

        # 1. Hardware Stats Box (CPU / RAM)
        pygame.draw.rect(self.tela, (15, 20, 35), (x_right, self.MARGEM + 10, w_col_right, 70))
        pygame.draw.rect(self.tela, cor, (x_right, self.MARGEM + 10, w_col_right, 70), 1)
        
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        self.tela.blit(self.fonte_stats.render(f"CPU [{cpu:04.1f}%]", True, cor_texto), (x_right + 10, self.MARGEM + 15))
        for i in range(12):
            cor_bloco = cor if (cpu/8.33) >= i else (20, 25, 45)
            pygame.draw.rect(self.tela, cor_bloco, (x_right + 10 + (i*17), self.MARGEM + 30, 13, 8))

        self.tela.blit(self.fonte_stats.render(f"RAM [{ram:04.1f}%]", True, cor_texto), (x_right + 10, self.MARGEM + 42))
        for i in range(12): 
            cor_bloco = cor if (ram/8.33) >= i else (20, 25, 45)
            pygame.draw.rect(self.tela, cor_bloco, (x_right + 10 + (i*17), self.MARGEM + 57, 13, 8))

        # 2. Quadro de Status do Sistema / Conectividade (Coluna Direita)
        pygame.draw.rect(self.tela, (15, 20, 35), (x_right, self.MARGEM + 90, w_col_right, 155))
        pygame.draw.rect(self.tela, cor, (x_right, self.MARGEM + 90, w_col_right, 155), 1)
        self.tela.blit(self.fonte_stats.render("[ SYSTEM DIAGNOSTICS ]", True, cor), (x_right + 10, self.MARGEM + 95))
        
        ip_cam = getattr(self.config, 'NOTEBOOK_CAM_IP', 'DESCONECTADO')
        self.tela.blit(self.fonte_pequena.render(f"SAT_CAM IP: {ip_cam}", True, cor_texto), (x_right + 10, self.MARGEM + 115))
        self.tela.blit(self.fonte_pequena.render(f"VOICE CORE: pt-BR-Antonio", True, cor_texto), (x_right + 10, self.MARGEM + 130))
        self.tela.blit(self.fonte_pequena.render(f"VECTOR RAG: ONLINE (ChromaDB)", True, cor_texto), (x_right + 10, self.MARGEM + 145))
        self.tela.blit(self.fonte_pequena.render(f"WAKE ENGINE: VOSK OFFLINE", True, cor_texto), (x_right + 10, self.MARGEM + 160))
        self.tela.blit(self.fonte_pequena.render(f"TUYA SMART: 192.168.0.4", True, cor_texto), (x_right + 10, self.MARGEM + 175))
        self.tela.blit(self.fonte_pequena.render(f"SECURITY: SENTINEL ACTIVE", True, cor_texto), (x_right + 10, self.MARGEM + 190))


        # --- RODAPÉ SIMÉTRICO (Esquerda: System Logs | Direita: Audio Spectrum) ---
        y_bottom = alt - self.MARGEM - 130
        w_bottom_box = 320

        # Logs do Sistema (Inferior Esquerdo)
        pygame.draw.rect(self.tela, (15, 20, 35), (self.MARGEM + 10, y_bottom, w_bottom_box, 130))
        pygame.draw.rect(self.tela, cor, (self.MARGEM + 10, y_bottom, w_bottom_box, 130), 1)
        self.tela.blit(self.fonte_stats.render(":: SYS_LOGS ::", True, cor), (self.MARGEM + 20, y_bottom + 8))
        pygame.draw.line(self.tela, cor, (self.MARGEM + 20, y_bottom + 22), (self.MARGEM + 150, y_bottom + 22), 1)
        
        for i, log in enumerate(log_eventos[-5:]):
            txt_log = log[0] if len(log[0]) < 42 else log[0][:40] + ".."
            self.tela.blit(self.fonte_log.render(txt_log, True, log[1]), (self.MARGEM + 20, y_bottom + 28 + (i * 18)))

        # Equalizador de Áudio (Inferior Direito - Largura equivalente para simetria)
        self.desenhar_equalizador_audio(audio_visual, larg - self.MARGEM - w_bottom_box, y_bottom, w_bottom_box, 130, cor)

        pygame.display.flip()

    def fechar(self):
        pygame.quit()
