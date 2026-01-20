import pygame
import networkx as nx
import random
import math
import array

pygame.init()
pygame.font.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# ---------- Configurações Visuais ----------
LARGURA = 1280
ALTURA = 720
LARGURA_PAINEL = 380
AREA_MAPA = LARGURA - LARGURA_PAINEL - 10
FPS = 60

# Paleta v7.0
C_FUNDO = (10, 15, 20)
C_GRID = (20, 40, 50)
C_PAINEL_BG = (15, 20, 25)
C_BORDA = (0, 255, 255) 
C_TEXTO = (200, 240, 255)
C_DESTAQUE = (0, 255, 100) 
C_RISCO = (255, 50, 50)    
C_VENTO = (100, 200, 255)
C_TURBO = (255, 200, 50)
C_BLOCK = (60, 60, 70)
C_CARD_BG = (20, 30, 40)
C_PREVIEW = (255, 255, 255) 

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("ROTA DE RISCO v7.0: MODO CRIA")

# Fontes
try:
    FONTE_TIT = pygame.font.SysFont("Impact", 28)
    FONTE_NUM = pygame.font.SysFont("Consolas", 30, bold=True)
    FONTE_BIG = pygame.font.SysFont("Impact", 60) # Fonte gigante para frases
except:
    FONTE_TIT = pygame.font.SysFont("Arial", 28, bold=True)
    FONTE_NUM = pygame.font.SysFont("Arial", 30, bold=True)
    FONTE_BIG = pygame.font.SysFont("Arial", 60, bold=True)

FONTE = pygame.font.SysFont("Consolas", 16)
FONTE_PEQ = pygame.font.SysFont("Consolas", 12)
FONTE_MISS = pygame.font.SysFont("Verdana", 14)
FONTE_GO = pygame.font.SysFont("Verdana", 50, bold=True)
FONTE_PARTICULA = pygame.font.SysFont("Arial", 20, bold=True)

relogio = pygame.time.Clock()

# ---------- SOM PROCEDURAL ----------
class SoundFX:
    def __init__(self):
        self.sounds = {}
        self.criar_sons()

    def gerar_onda(self, freq_start, freq_end, duration, volume=0.5, type='sin'):
        sample_rate = 44100; n_samples = int(sample_rate * duration); buf = array.array('h')
        for i in range(n_samples):
            t = i / n_samples
            freq = freq_start + (freq_end - freq_start) * t
            val = 0
            if type == 'sin': val = math.sin(2 * math.pi * freq * (i / sample_rate))
            elif type == 'square': val = 1 if math.sin(2 * math.pi * freq * (i / sample_rate)) > 0 else -1
            elif type == 'noise': val = random.uniform(-1, 1)
            env = 1.0 - t
            sample = int(val * 32767 * volume * env)
            buf.append(sample)
        return pygame.mixer.Sound(buffer=buf)

    def criar_sons(self):
        self.sounds['click'] = self.gerar_onda(800, 1200, 0.05, 0.3, 'sin')
        self.sounds['cash'] = self.gerar_onda(1200, 2000, 0.15, 0.4, 'square')
        self.sounds['alert'] = self.gerar_onda(150, 100, 0.4, 0.5, 'noise')
        self.sounds['error'] = self.gerar_onda(150, 100, 0.2, 0.4, 'square')
        self.sounds['wind'] = self.gerar_onda(400, 300, 0.3, 0.2, 'noise')
        self.sounds['shake'] = self.gerar_onda(100, 80, 0.2, 0.4, 'square')
        self.sounds['win_big'] = self.gerar_onda(400, 800, 0.4, 0.5, 'square') # Som de vitória

    def play(self, name):
        if name in self.sounds: self.sounds[name].play()

sfx = SoundFX()

# ---------- SISTEMA DE PARTÍCULAS ----------
class Particle:
    def __init__(self, x, y, texto, cor):
        self.x = x; self.y = y; self.texto = texto; self.cor = cor
        self.life = 60; self.alpha = 255; self.vel_y = -1.5
    def update(self):
        self.y += self.vel_y; self.life -= 1; self.alpha = max(0, int((self.life / 60) * 255))
    def draw(self, surf):
        if self.life > 0:
            txt_surf = FONTE_PARTICULA.render(self.texto, True, self.cor)
            txt_surf.set_alpha(self.alpha)
            surf.blit(txt_surf, (self.x - txt_surf.get_width()//2, self.y))

particulas = []
def spawn_floating_text(x, y, texto, cor): particulas.append(Particle(x, y, texto, cor))

# ---------- Parâmetros de Jogo (DIFICULDADE AUMENTADA) ----------
real_m_per_px = 0.2
velocidade_m_s = 60.0 
velocidade_px_s = velocidade_m_s / real_m_per_px

CUSTO_COMBUSTIVEL_POR_ARESTA = 15
MULTA_BLITZ = 300                 
PENALIDADE_TEMPO_BLITZ = 30.0     
PENALIDADE_MISSAO_FALHA = 500
CHANCE_PEGAR_BLITZ = 0.90 # Subiu para 90%

# Mais obstáculos no mapa
QTD_BLITZ = 9 
QTD_VENTO = 6
QTD_TURBO = 5
QTD_STORM = 3

# Frases de Vitória
FRASES_VITORIA = ["MAROLOU VAGABUNDO!", "AMASSOU CACHORRO!", "TU É FODA GURIZÃO!"]

# ---------- Geração do Grafo ----------
def gerar_grafo():
    G_temp = nx.Graph()
    linhas, colunas = 4, 5
    no = 0
    pos_raw = {}
    espaco_x = 180; espaco_y = 140
    inicio_x = 120; inicio_y = 100

    for r in range(linhas):
        for c in range(colunas):
            G_temp.add_node(no)
            x = inicio_x + c * espaco_x + random.randint(-25, 25)
            y = inicio_y + r * espaco_y + random.randint(-25, 25)
            pos_raw[no] = (x, y)
            no += 1

    for r in range(linhas):
        for c in range(colunas):
            idx = r * colunas + c
            if c + 1 < colunas: G_temp.add_edge(idx, idx + 1)
            if r + 1 < linhas: G_temp.add_edge(idx, idx + colunas)

    extras = [(0, 6), (3, 7), (5, 11), (2, 6), (8, 14), (9, 13)]
    for (a, b) in extras:
        if a in G_temp.nodes() and b in G_temp.nodes(): G_temp.add_edge(a, b)

    padding = 60
    xs = [p[0] for p in pos_raw.values()]; ys = [p[1] for p in pos_raw.values()]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    dw = AREA_MAPA - 2 * padding; dh = ALTURA - 2 * padding
    scale = min(dw/(maxx-minx or 1), dh/(maxy-miny or 1)) * 0.9

    pos = {}
    for n, (x, y) in pos_raw.items():
        pos[n] = (int((x - minx)*scale + padding), int((y - miny)*scale + padding))

    def cruzam(p1, p2, p3, p4):
        def orient(a, b, c): return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        return (orient(p1,p2,p3)*orient(p1,p2,p4)<0) and (orient(p3,p4,p1)*orient(p3,p4,p2)<0)

    edges = list(G_temp.edges())
    removidas = set()
    for i in range(len(edges)):
        u, v = edges[i]; p1, p2 = pos[u], pos[v]
        for j in range(i+1, len(edges)):
            x, y = edges[j]
            if u in (x,y) or v in (x,y): continue
            p3, p4 = pos[x], pos[y]
            if cruzam(p1, p2, p3, p4):
                d1 = math.hypot(p2[0]-p1[0], p2[1]-p1[1]); d2 = math.hypot(p4[0]-p3[0], p4[1]-p3[1])
                if d1 > d2: removidas.add((u, v))
                else: removidas.add((x, y))
    G_temp.remove_edges_from(list(removidas))

    G = G_temp.to_directed()
    for u, v in G.edges():
        dist = math.hypot(pos[u][0]-pos[v][0], pos[u][1]-pos[v][1])
        G.edges[u, v]['dist_px'] = dist
        G.edges[u, v]['base_time'] = dist / velocidade_px_s 
        G.edges[u, v]['risco'] = 0.0           
        G.edges[u, v]['tipo'] = 'normal' 
    return G, pos

G, pos = gerar_grafo()

# ---------- Estado do Jogo ----------
class Missao:
    def __init__(self, destino, recompensa, prazo, nome_droga):
        self.destino = destino
        self.recompensa = recompensa
        self.prazo = prazo
        self.nome_droga = nome_droga

tipos_droga = [("Cannabis", 1.0), ("Sintéticos", 1.5), ("Pó Branco", 2.5), ("Cristais", 3.0)]

# Adicionado estado SUCESSO_MISSAO
estado_jogo = "MENU"
saldo = 1000
missoes_disponiveis = []
missao_atual = None
tempo_missao_decorrido = 0.0
motivo_falha = ""
frase_vitoria_atual = "" # Armazena a frase da vez
flash_timer = 0 
shake_screen = 0 
radar_angle = 0 

no_jogador = 0
caminho_jogador = [0]

def verificar_falencia():
    global estado_jogo
    if saldo <= 0:
        sfx.play('error')
        estado_jogo = "GAME_OVER_TOTAL"
        return True
    return False

def gerar_missoes(no_atual):
    novas = []
    G_nav = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        if d['tipo'] != 'tempestade': G_nav.add_edge(u, v, weight=d['base_time'])
    try: lens = nx.single_source_dijkstra_path_length(G_nav, no_atual)
    except: lens = {}

    candidatos = [n for n, dist in lens.items() if dist > 2.0 and n != no_atual]
    if not candidatos: candidatos = [n for n in G.nodes() if n != no_atual]
    
    for _ in range(3):
        if not candidatos: break
        dest = random.choice(candidatos)
        dist_otima = lens.get(dest, 10.0)
        droga, mult = random.choice(tipos_droga)
        # Prazo mais apertado na v7.0 (1.1 a 1.6 de folga)
        folga = random.uniform(1.1, 1.6) 
        prazo = dist_otima * folga
        base_pay = dist_otima * 50
        bonus_urgencia = (2.0 - folga) * 150 # Bonus maior por pressa
        valor = int((base_pay * mult) + bonus_urgencia)
        novas.append(Missao(dest, valor, prazo, droga))
    return novas

missoes_disponiveis = gerar_missoes(no_jogador)

# ---------- Mecânicas ----------
menor_caminho = []
custo_menor = float('inf')

def recalcular_dijkstra(target):
    G_calc = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        if d['tipo'] != 'tempestade':
            peso = d['base_time'] * (2.0 if d['tipo'] == 'vento' else 1.0)
            G_calc.add_edge(u, v, weight=peso)
    try:
        path = nx.dijkstra_path(G_calc, no_jogador, target)
        dist = nx.dijkstra_path_length(G_calc, no_jogador, target)
        return path, dist
    except:
        return [], float('inf')

def calcular_peso_real(u, v):
    dados = G.edges[u, v]
    tempo = dados['base_time']
    custo_extra = 0
    msg = ""
    shake = 0
    
    tipo = dados['tipo']
    
    if tipo == 'blitz':
        if random.random() < dados['risco']:
            tempo += PENALIDADE_TEMPO_BLITZ
            custo_extra = MULTA_BLITZ
            msg = "BLITZ DETECTADA! SUBORNO PAGO!"
    elif tipo == 'vento':
        tempo *= 2.0
        msg = "VENTO CONTRA! VELOCIDADE REDUZIDA."
    elif tipo == 'turbulencia':
        msg = "TURBULÊNCIA SEVERA!"
        shake = 5
    elif tipo == 'tempestade':
        msg = "ROTA BLOQUEADA POR TEMPESTADE!"
        return float('inf'), 0, msg, 0
    
    return tempo, custo_extra, msg, shake

movendo = False
prog_mov = 0.0
inicio_mov, fim_mov = None, None
duracao_mov = 1.0
msg_evento = ""

def iniciar_voo(para_no):
    global movendo, inicio_mov, fim_mov, duracao_mov, msg_evento
    global tempo_missao_decorrido, saldo, estado_jogo, flash_timer, shake_screen
    
    if estado_jogo != "JOGANDO": return
    
    if G.edges[no_jogador, para_no]['tipo'] == 'tempestade':
        sfx.play('error')
        msg_evento = "ROTA INTERDITADA (TEMPESTADE)"
        spawn_floating_text(pos[para_no][0], pos[para_no][1], "BLOQUEADO", C_BLOCK)
        return

    saldo -= CUSTO_COMBUSTIVEL_POR_ARESTA
    spawn_floating_text(pos[no_jogador][0], pos[no_jogador][1] - 20, f"-${CUSTO_COMBUSTIVEL_POR_ARESTA}", (200, 200, 200))

    if verificar_falencia(): return

    tempo_real, custo_blitz, msg, shake_val = calcular_peso_real(no_jogador, para_no)
    
    shake_screen = shake_val
    if shake_val > 0: sfx.play('shake')

    if custo_blitz > 0:
        sfx.play('alert')
        flash_timer = 20
        saldo -= custo_blitz
        spawn_floating_text(LARGURA//2, ALTURA//2, f"-${custo_blitz} (BLITZ)", C_RISCO)
        if verificar_falencia(): return
    elif G.edges[no_jogador, para_no]['tipo'] == 'vento':
        sfx.play('wind')
    else:
        sfx.play('click')
        
    msg_evento = msg
    tempo_missao_decorrido += tempo_real
    
    inicio_mov = pos[no_jogador]
    fim_mov = pos[para_no]
    
    base_anim = min(tempo_real, 1.5)
    if G.edges[no_jogador, para_no]['tipo'] == 'vento': base_anim = 2.0
    duracao_mov = max(0.3, base_anim)
    
    movendo = True
    prog_mov = 0.0

def falhar_missao(motivo):
    global saldo, estado_jogo, missao_atual, movendo, motivo_falha
    sfx.play('error')
    saldo -= PENALIDADE_MISSAO_FALHA
    spawn_floating_text(LARGURA//2, ALTURA//2 - 50, f"FALHA: -${PENALIDADE_MISSAO_FALHA}", C_RISCO)
    movendo = False
    missao_atual = None
    if verificar_falencia(): return
    motivo_falha = motivo
    estado_jogo = "FALHA_MISSAO"

def finalizar_voo(para_no):
    global no_jogador, caminho_jogador, movendo, estado_jogo
    global missoes_disponiveis, missao_atual, saldo, msg_evento, shake_screen, frase_vitoria_atual
    
    no_jogador = para_no
    caminho_jogador.append(no_jogador)
    movendo = False
    shake_screen = 0
    
    if missao_atual and no_jogador == missao_atual.destino:
        if tempo_missao_decorrido <= missao_atual.prazo:
            sfx.play('win_big')
            saldo += missao_atual.recompensa
            spawn_floating_text(pos[no_jogador][0], pos[no_jogador][1] - 40, f"+${missao_atual.recompensa}", C_DESTAQUE)
            
            # ATIVA TELA DE SUCESSO
            frase_vitoria_atual = random.choice(FRASES_VITORIA)
            estado_jogo = "SUCESSO_MISSAO"
        else:
            falhar_missao("TEMPO ESGOTADO!")

def resetar_rodada_logica():
    global missoes_disponiveis, caminho_jogador
    pygame.event.clear()
    for u,v in G.edges():
        G.edges[u,v]['tipo'] = 'normal'; G.edges[u,v]['risco'] = 0.0
    arestas = list(G.edges())
    random.shuffle(arestas)
    idx = 0
    for _ in range(QTD_STORM):
        if idx < len(arestas):
            u, v = arestas[idx]; G.edges[u,v]['tipo'] = 'tempestade'
            if G.has_edge(v, u): G.edges[v,u]['tipo'] = 'tempestade'
            idx += 1
    for _ in range(QTD_BLITZ):
        if idx < len(arestas):
            u, v = arestas[idx]; 
            if G.edges[u,v]['tipo'] == 'normal': G.edges[u,v]['tipo'] = 'blitz'; G.edges[u,v]['risco'] = CHANCE_PEGAR_BLITZ
            idx += 1
    for _ in range(QTD_VENTO):
        if idx < len(arestas):
            u, v = arestas[idx]; 
            if G.edges[u,v]['tipo'] == 'normal': G.edges[u,v]['tipo'] = 'vento'
            idx += 1
    for _ in range(QTD_TURBO):
        if idx < len(arestas):
            u, v = arestas[idx]; 
            if G.edges[u,v]['tipo'] == 'normal': G.edges[u,v]['tipo'] = 'turbulencia'
            idx += 1
    missoes_disponiveis = gerar_missoes(no_jogador)
    caminho_jogador[:] = [no_jogador]
    global missao_atual; missao_atual = None

def reiniciar_tudo():
    global saldo, no_jogador, estado_jogo, msg_evento, caminho_jogador
    saldo = 1000
    no_jogador = 0
    estado_jogo = "MENU"
    msg_evento = ""
    caminho_jogador = [0]
    resetar_rodada_logica()

# ---------- UI & Desenho ----------
def desenhar_radar_efeito():
    global radar_angle
    radar_angle = (radar_angle + 2) % 360
    center = (AREA_MAPA // 2, ALTURA // 2)
    length = AREA_MAPA
    end_x = center[0] + length * math.cos(math.radians(radar_angle))
    end_y = center[1] + length * math.sin(math.radians(radar_angle))
    pygame.draw.line(tela, (0, 50, 0), center, (end_x, end_y), 2)

def desenhar_grid_radar():
    cor_grid = (30, 50, 60)
    for x in range(0, AREA_MAPA, 50): pygame.draw.line(tela, cor_grid, (x, 0), (x, ALTURA), 1)
    for y in range(0, ALTURA, 50): pygame.draw.line(tela, cor_grid, (0, y), (AREA_MAPA, y), 1)
    desenhar_radar_efeito()

def desenhar_aviao(cx, cy, angle=0):
    pygame.draw.ellipse(tela, (220, 220, 220), (cx-8, cy-15, 16, 30))
    pygame.draw.polygon(tela, (200, 200, 200), [(cx, cy-5), (cx-20, cy+5), (cx, cy+10), (cx+20, cy+5)])
    pygame.draw.polygon(tela, (180, 180, 180), [(cx, cy+10), (cx-8, cy+18), (cx+8, cy+18)])
    if (pygame.time.get_ticks() // 500) % 2 == 0:
        pygame.draw.circle(tela, (255, 0, 0), (cx-20, cy+5), 2) 
        pygame.draw.circle(tela, (0, 255, 0), (cx+20, cy+5), 2) 

def desenhar_pontilhado(p1, p2, cor=(255,255,255)):
    x1, y1 = p1; x2, y2 = p2; dist = math.hypot(x2-x1, y2-y1); steps = int(dist / 10)
    for i in range(0, steps, 2):
        start = (x1 + (x2-x1)*i/steps, y1 + (y2-y1)*i/steps)
        end = (x1 + (x2-x1)*(i+1)/steps, y1 + (y2-y1)*(i+1)/steps)
        pygame.draw.line(tela, cor, start, end, 2)

def desenhar_no_brilhante(pos, cor, tamanho):
    s = pygame.Surface((tamanho*4, tamanho*4), pygame.SRCALPHA)
    pygame.draw.circle(s, (*cor, 50), (tamanho*2, tamanho*2), tamanho*1.5)
    pygame.draw.circle(s, (*cor, 100), (tamanho*2, tamanho*2), tamanho*1.2)
    tela.blit(s, (pos[0]-tamanho*2, pos[1]-tamanho*2))
    pygame.draw.circle(tela, cor, pos, tamanho)

def obter_rects_missoes():
    rects = []
    start_x = 100; gap = 30
    card_w = (LARGURA - 200 - 2*gap) // 3
    card_h = 320
    for i in range(len(missoes_disponiveis)):
        r = pygame.Rect(start_x + i*(card_w+gap), 200, card_w, card_h)
        rects.append(r)
    return rects

def desenhar_menu_missoes():
    s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    s.fill((10, 15, 20, 230))
    tela.blit(s, (0,0))
    t = FONTE_TIT.render("DISPONIBILIDADE DE CONTRATOS", True, C_BORDA)
    tela.blit(t, (LARGURA//2 - t.get_width()//2, 100))
    rects = obter_rects_missoes()
    mx, my = pygame.mouse.get_pos()
    
    for i, m in enumerate(missoes_disponiveis):
        rect = rects[i]
        hover = rect.collidepoint(mx, my)
        cor_borda = C_DESTAQUE if hover else C_GRID
        cor_bg = (30, 40, 50) if hover else C_CARD_BG
        pygame.draw.rect(tela, cor_bg, rect, border_radius=15)
        pygame.draw.rect(tela, cor_borda, rect, 2, border_radius=15)
        
        if hover:
             p_dest = pos[m.destino]; p_orig = pos[no_jogador]
             desenhar_pontilhado(p_orig, p_dest, C_DESTAQUE)
             desenhar_no_brilhante(p_dest, C_DESTAQUE, 12)

        pygame.draw.rect(tela, (0,0,0), (rect.x+10, rect.y+10, rect.width-20, 30), border_radius=5)
        nome = FONTE.render(m.nome_droga.upper(), True, C_BORDA)
        tela.blit(nome, (rect.x + 20, rect.y + 16))
        
        lines = [(f"DESTINO: SETOR {m.destino}", (200,200,200)), (f"VALOR: ${m.recompensa}", C_DESTAQUE), (f"TEMPO: {m.prazo:.1f}s", (255, 200, 100))]
        off_y = 60
        for txt, cor in lines:
            r_txt = FONTE_MISS.render(txt, True, cor)
            tela.blit(r_txt, (rect.x + 20, rect.y + off_y))
            off_y += 35

        btn_y = rect.y + rect.height - 50
        cor_btn = C_DESTAQUE if hover else (50, 60, 70)
        pygame.draw.rect(tela, cor_btn, (rect.x+20, btn_y, rect.width-40, 30), border_radius=5)
        lbl_btn = FONTE.render("ACEITAR", True, (0,0,0) if hover else (150,150,150))
        tela.blit(lbl_btn, (rect.x + 40, btn_y + 8))

def desenhar_painel_lateral():
    pygame.draw.rect(tela, C_PAINEL_BG, (AREA_MAPA, 0, LARGURA_PAINEL+10, ALTURA))
    pygame.draw.line(tela, C_BORDA, (AREA_MAPA, 0), (AREA_MAPA, ALTURA), 2)
    pygame.draw.rect(tela, (0,0,0), (AREA_MAPA, 0, LARGURA_PAINEL+10, 60))
    tela.blit(FONTE_TIT.render("ROTA DE RISCO", True, C_BORDA), (AREA_MAPA+20, 15))
    
    y_start = 80
    cor_saldo = C_DESTAQUE if saldo > 0 else C_RISCO
    tela.blit(FONTE.render("SALDO ATUAL", True, (150,150,150)), (AREA_MAPA+20, y_start))
    tela.blit(FONTE_NUM.render(f"${saldo}", True, cor_saldo), (AREA_MAPA+20, y_start+20))
    
    y_start += 80
    pygame.draw.rect(tela, (20,30,40), (AREA_MAPA+10, y_start, LARGURA_PAINEL-20, 200), border_radius=10)
    pygame.draw.rect(tela, C_GRID, (AREA_MAPA+10, y_start, LARGURA_PAINEL-20, 200), 1, border_radius=10)
    
    if estado_jogo == "JOGANDO" and missao_atual:
        tela.blit(FONTE.render("MISSÃO EM ANDAMENTO", True, C_BORDA), (AREA_MAPA+30, y_start+15))
        tela.blit(FONTE_MISS.render(f"CARGA: {missao_atual.nome_droga}", True, C_TEXTO), (AREA_MAPA+30, y_start+50))
        tela.blit(FONTE_MISS.render(f"DESTINO: NÓ {missao_atual.destino}", True, C_RISCO), (AREA_MAPA+30, y_start+80))
        restante = missao_atual.prazo - tempo_missao_decorrido
        pct = max(0, restante / missao_atual.prazo)
        bar_w = LARGURA_PAINEL - 60
        pygame.draw.rect(tela, (50,0,0), (AREA_MAPA+30, y_start+120, bar_w, 10))
        pygame.draw.rect(tela, C_DESTAQUE if pct > 0.3 else C_RISCO, (AREA_MAPA+30, y_start+120, bar_w*pct, 10))
        tela.blit(FONTE.render(f"{restante:.1f}s", True, C_TEXTO), (AREA_MAPA+30 + bar_w + 5, y_start+115))
        tela.blit(FONTE_NUM.render(f"+${missao_atual.recompensa}", True, C_DESTAQUE), (AREA_MAPA+30, y_start+150))
    else:
        tela.blit(FONTE.render("NENHUMA MISSÃO ATIVA", True, (100,100,100)), (AREA_MAPA+30, y_start+90))

    y_start += 220
    tela.blit(FONTE.render("LOG DO SISTEMA:", True, C_BORDA), (AREA_MAPA+20, y_start))
    if msg_evento:
        msg_surf = FONTE_MISS.render(f"> {msg_evento}", True, (255,255,0))
        tela.blit(msg_surf, (AREA_MAPA+20, y_start+30))

    y_info = ALTURA - 150
    infos = [("VERMELHO: BLITZ (-$300)", C_RISCO), ("AZUL: VENTO CONTRA (2x Tempo)", C_VENTO), ("AMARELO: TURBULÊNCIA", C_TURBO), ("CINZA: TEMPESTADE (Bloqueio)", (150,150,150))]
    for i, (txt, cor) in enumerate(infos):
        pygame.draw.circle(tela, cor, (AREA_MAPA+25, y_info + i*25 + 8), 6)
        tela.blit(FONTE_PEQ.render(txt, True, (180,180,180)), (AREA_MAPA+40, y_info + i*25))

def desenhar_tela_falha_missao():
    s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    s.fill((50, 10, 10, 220))
    tela.blit(s, (0,0))
    t1 = FONTE_GO.render("FALHA", True, C_RISCO)
    tela.blit(t1, (LARGURA//2 - t1.get_width()//2, 250))
    m_surf = FONTE_TIT.render(motivo_falha, True, (255,255,255))
    tela.blit(m_surf, (LARGURA//2 - m_surf.get_width()//2, 300))
    t2 = FONTE_TIT.render(f"- ${PENALIDADE_MISSAO_FALHA}", True, C_RISCO)
    tela.blit(t2, (LARGURA//2 - t2.get_width()//2, 350))
    btn_rect = pygame.Rect(LARGURA//2 - 100, 420, 200, 50)
    mx, my = pygame.mouse.get_pos()
    cor_btn = (255, 255, 255) if btn_rect.collidepoint(mx, my) else (150, 150, 150)
    pygame.draw.rect(tela, cor_btn, btn_rect, border_radius=5)
    t_btn = FONTE_TIT.render("CONTINUAR", True, (0,0,0))
    tela.blit(t_btn, (btn_rect.x + 35, btn_rect.y + 10))

# NOVA TELA DE SUCESSO
def desenhar_tela_sucesso():
    s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    s.fill((0, 50, 0, 230)) # Fundo Verde Vitória
    tela.blit(s, (0,0))
    
    # Efeitos verdes aleatórios
    if (pygame.time.get_ticks() // 100) % 2 == 0:
        pygame.draw.rect(tela, C_DESTAQUE, (0,0, LARGURA, ALTURA), 10)

    t1 = FONTE_BIG.render(frase_vitoria_atual, True, C_DESTAQUE)
    tela.blit(t1, (LARGURA//2 - t1.get_width()//2, 200))
    
    if missao_atual:
        t2 = FONTE_BIG.render(f"+ R$ {missao_atual.recompensa}", True, (255, 255, 255))
        tela.blit(t2, (LARGURA//2 - t2.get_width()//2, 320))

    btn_rect = pygame.Rect(LARGURA//2 - 120, 450, 240, 60)
    mx, my = pygame.mouse.get_pos()
    cor_btn = (255, 255, 255) if btn_rect.collidepoint(mx, my) else (200, 255, 200)
    
    pygame.draw.rect(tela, cor_btn, btn_rect, border_radius=10)
    t_btn = FONTE_TIT.render("CONTINUAR", True, (0,0,0))
    tela.blit(t_btn, (btn_rect.x + 55, btn_rect.y + 15))

def desenhar_game_over_total():
    s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    s.fill((0,0,0, 245))
    tela.blit(s, (0,0))
    t = FONTE_GO.render("FALÊNCIA", True, C_RISCO)
    tela.blit(t, (LARGURA//2 - t.get_width()//2, 200))
    sub = FONTE_TIT.render("FIM DA LINHA, PILOTO.", True, (255, 255, 255))
    tela.blit(sub, (LARGURA//2 - sub.get_width()//2, 300))
    btn_rect = pygame.Rect(LARGURA//2 - 120, 400, 240, 50)
    pygame.draw.rect(tela, C_DESTAQUE, btn_rect, border_radius=5)
    t_btn = FONTE.render("REINICIAR SISTEMA", True, (0,0,0))
    tela.blit(t_btn, (btn_rect.x + 40, btn_rect.y + 15))

def input_handler(ev):
    global estado_jogo, movendo, flash_timer
    if ev.type == pygame.MOUSEBUTTONDOWN:
        mx, my = ev.pos
        if estado_jogo == "MENU":
            rects = obter_rects_missoes()
            for i, r in enumerate(rects):
                if r.collidepoint(mx, my):
                    sfx.play('click')
                    aceitar_missao(missoes_disponiveis[i])
                    break
        elif estado_jogo == "JOGANDO" and not movendo:
            for n, p in pos.items():
                if math.hypot(mx-p[0], my-p[1]) < 20:
                    if G.has_edge(no_jogador, n): iniciar_voo(n)
                    break
        elif estado_jogo == "FALHA_MISSAO":
            btn_rect = pygame.Rect(LARGURA//2 - 100, 420, 200, 50)
            if btn_rect.collidepoint(mx, my):
                sfx.play('click')
                estado_jogo = "MENU"
                resetar_rodada_logica()
        elif estado_jogo == "SUCESSO_MISSAO":
            btn_rect = pygame.Rect(LARGURA//2 - 120, 450, 240, 60)
            if btn_rect.collidepoint(mx, my):
                sfx.play('click')
                estado_jogo = "MENU"
                resetar_rodada_logica()
        elif estado_jogo == "GAME_OVER_TOTAL":
            btn_rect = pygame.Rect(LARGURA//2 - 120, 400, 240, 50)
            if btn_rect.collidepoint(mx, my):
                sfx.play('click')
                reiniciar_tudo()

def aceitar_missao(m):
    global estado_jogo, missao_atual, tempo_missao_decorrido
    global menor_caminho, custo_menor, caminho_jogador
    missao_atual = m
    estado_jogo = "JOGANDO"
    tempo_missao_decorrido = 0.0
    caminho_jogador = [no_jogador]
    menor_caminho, custo_menor = recalcular_dijkstra(m.destino)
    pygame.event.clear()

# ---------- Loop Principal ----------
rodando = True
while rodando:
    dt = relogio.tick(FPS) / 1000.0
    if flash_timer > 0: flash_timer -= 1
    
    if estado_jogo == "JOGANDO" and missao_atual:
        if tempo_missao_decorrido > missao_atual.prazo:
            falhar_missao("TEMPO ESGOTADO!")
            
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT: rodando = False
        input_handler(ev)

    # Animação
    jogador_pos_draw = list(pos[no_jogador])
    if movendo:
        prog_mov += dt / duracao_mov
        if prog_mov >= 1.0:
            alvo = [n for n, p in pos.items() if p == fim_mov][0]
            finalizar_voo(alvo)
        else:
            x = inicio_mov[0] + (fim_mov[0] - inicio_mov[0]) * prog_mov
            y = inicio_mov[1] + (fim_mov[1] - inicio_mov[1]) * prog_mov
            shake_x, shake_y = 0, 0
            if shake_screen > 0:
                shake_x = random.randint(-shake_screen, shake_screen)
                shake_y = random.randint(-shake_screen, shake_screen)
            jogador_pos_draw = [int(x + shake_x), int(y + shake_y)]

    # Render
    tela.fill(C_FUNDO)
    desenhar_grid_radar()
    
    for u, v in G.edges():
        p1, p2 = pos[u], pos[v]
        tipo = G.edges[u, v].get('tipo', 'normal')
        cor = (40, 80, 100); largura = 2
        
        if tipo == 'blitz':
            cor = C_RISCO; largura = 3
            if (pygame.time.get_ticks() // 200) % 2 == 0: pygame.draw.line(tela, cor, p1, p2, largura)
            else: pygame.draw.line(tela, (100,0,0), p1, p2, largura)
        elif tipo == 'vento': cor = C_VENTO; pygame.draw.line(tela, cor, p1, p2, largura)
        elif tipo == 'turbulencia': cor = C_TURBO; pygame.draw.line(tela, cor, p1, p2, largura)
        elif tipo == 'tempestade':
            cor = C_BLOCK; largura = 1
            pygame.draw.line(tela, cor, p1, p2, largura)
            mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
            pygame.draw.line(tela, cor, (mx-5, my-5), (mx+5, my+5), 2)
            pygame.draw.line(tela, cor, (mx+5, my-5), (mx-5, my+5), 2)
        else:
            pygame.draw.line(tela, cor, p1, p2, largura)
        
        if tipo != 'tempestade':
            mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
            tempo_base = G.edges[u, v]['base_time']
            if tipo == 'vento': tempo_base *= 2.0
            txt_peso = f"{tempo_base:.1f}s"
            s_txt = FONTE_PEQ.render(txt_peso, True, (100,150,150))
            tela.blit(s_txt, (mx, my))

    if estado_jogo == "JOGANDO" and not movendo:
        mx, my = pygame.mouse.get_pos()
        for n, p in pos.items():
            if math.hypot(mx-p[0], my-p[1]) < 20: 
                if G.has_edge(no_jogador, n): desenhar_pontilhado(pos[no_jogador], p, C_PREVIEW)
                break

    for n, p in pos.items():
        cor_no = C_GRID; tamanho = 8
        if n == no_jogador: cor_no = C_BORDA; tamanho = 10; desenhar_no_brilhante(p, cor_no, tamanho)
        elif missao_atual and n == missao_atual.destino: cor_no = C_RISCO; tamanho = 10; desenhar_no_brilhante(p, cor_no, tamanho)
        else:
            pygame.draw.circle(tela, (20,40,50), p, tamanho)
            pygame.draw.circle(tela, (50,80,100), p, tamanho, 1)
        lbl = FONTE_PEQ.render(str(n), True, (100,120,130))
        tela.blit(lbl, (p[0]-4, p[1]-22))

    cx, cy = jogador_pos_draw
    desenhar_aviao(cx, cy)
    if movendo: pygame.draw.circle(tela, (255,100,0), (cx, cy+18), random.randint(3,6))

    for p in particulas[:]:
        p.update(); p.draw(tela)
        if p.life <= 0: particulas.remove(p)

    if flash_timer > 0:
        s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        s.fill((255, 0, 0, 100))
        tela.blit(s, (0,0))

    desenhar_painel_lateral()
    if estado_jogo == "MENU": desenhar_menu_missoes()
    elif estado_jogo == "FALHA_MISSAO": desenhar_tela_falha_missao()
    elif estado_jogo == "SUCESSO_MISSAO": desenhar_tela_sucesso()
    elif estado_jogo == "GAME_OVER_TOTAL": desenhar_game_over_total()

    pygame.display.flip()

pygame.quit()