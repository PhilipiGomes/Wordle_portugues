import random
from collections import Counter

import pygame

from lista import (  # mesmas premissas: minúsculas, mesmo tamanho
    melhores_palavras,
    palavras,
)

# -------------------- Pré-processamento (rápido e robusto) --------------------
WORDS = palavras
N_WORDS = len(WORDS)
WORD_LEN = len(WORDS[0]) if N_WORDS else 0

# Alfabeto dinâmico (suporta acentos/ç)
ALPHABET = sorted({ch for w in WORDS for ch in w})
ALPHABET_IDX = {ch: i for i, ch in enumerate(ALPHABET)}
ALPHABET_SIZE = len(ALPHABET)

# Representações pré-calculadas
WORD_CHARS = [list(w) for w in WORDS]


def _counts_arr(word):
    arr = [0] * ALPHABET_SIZE
    for ch in word:
        arr[ALPHABET_IDX[ch]] += 1
    return arr


WORD_COUNTS_ARR = [_counts_arr(w) for w in WORDS]
WORD_INDEX = {w: i for i, w in enumerate(WORDS)}


# -------------------- Lógica do jogo (otimizada) --------------------
def escolher_palavra():
    # trunk-ignore(bandit/B311)
    return random.choice(WORDS)


def compute_result_fast(secret_chars, secret_counts_arr, attempt):
    """
    Gera string com emojis (🟩🟨⬜). Usa arrays de contagem para evitar count()/index().
    """
    counts = secret_counts_arr[:]  # cópia rápida
    res = ["⬜"] * WORD_LEN

    # verdes
    for i, ch in enumerate(attempt):
        if ch == secret_chars[i]:
            res[i] = "🟩"
            counts[ALPHABET_IDX[ch]] -= 1

    # amarelos
    for i, ch in enumerate(attempt):
        if res[i] == "⬜":
            idx = ALPHABET_IDX.get(ch)
            if idx is not None and counts[idx] > 0:
                res[i] = "🟨"
                counts[idx] -= 1

    return "".join(res)


def filtrar_palavras(candidatos, tentativa, resultado):
    """Mantém só candidatos que produzem `resultado` para `tentativa`."""
    out = []
    for w in candidatos:
        idx = WORD_INDEX[w]
        if (
            compute_result_fast(WORD_CHARS[idx], WORD_COUNTS_ARR[idx], tentativa)
            == resultado
        ):
            out.append(w)
    return out


def melhor_tentativa(palavras_possiveis):
    """Heurística por frequência posicional; penaliza repetições."""
    if not palavras_possiveis:
        return ""
    L = WORD_LEN
    pos_counters = [Counter() for _ in range(L)]
    for w in palavras_possiveis:
        for i, ch in enumerate(w):
            pos_counters[i][ch] += 1

    def score(word):
        s = 0
        seen = set()
        for i, ch in enumerate(word):
            s += pos_counters[i].get(ch, 0)
            # penaliza letras repetidas (mais exploração)
            if ch in seen:
                s -= 1
            else:
                seen.add(ch)
        return s

    return max(palavras_possiveis, key=score)


# -------------------- Pygame: constantes + cache --------------------
CELL = 60
MARGIN_X = 50
MARGIN_Y = 50
ROW_SPACING = 80
COL_SPACING = CELL
WINDOW_W = MARGIN_X * 2 + WORD_LEN * (CELL + 10)
WINDOW_H = MARGIN_Y * 2 + 6 * ROW_SPACING

# cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERDE = (0, 185, 85)
AMARELO = (245, 200, 20)
CINZA = (100, 100, 100)

# Precompute cell positions to avoid recalcular no desenho
CELL_POS = [
    [(MARGIN_X + j * (CELL + 10), MARGIN_Y + i * ROW_SPACING) for j in range(WORD_LEN)]
    for i in range(6)
]


# -------------------- Função principal (melhor prática de loop) --------------------
def jogar_wordle(ia_jogar=False):
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Wordle PT (otimizado)")
    font = pygame.font.Font(None, CELL - 10)

    # cache de superfícies para letras do alfabeto (upper)
    LETTER_SURF = {ch: font.render(ch.upper(), True, BRANCO) for ch in ALPHABET}

    def render_letter(ch):
        # fallback se caracter não estiver no alfabeto
        return LETTER_SURF.get(ch, font.render(ch.upper(), True, BRANCO))

    def desenhar_tela(tentativas, tentativa_atual):
        screen.fill(PRETO)

        # Desenha tentativas anteriores (limita a 6 linhas por segurança)
        for i, (pal, res) in enumerate(tentativas[:6]):
            for j, ch in enumerate(pal):
                x, y = CELL_POS[i][j]
                cor = VERDE if res[j] == "🟩" else (AMARELO if res[j] == "🟨" else CINZA)
                pygame.draw.rect(screen, cor, (x, y, CELL, CELL), border_radius=6)
                surf = render_letter(ch)
                sw, sh = surf.get_size()
                screen.blit(surf, (x + (CELL - sw) // 2, y + (CELL - sh) // 2))

        # Desenha a tentativa atual apenas se houver linha disponível (ou seja, < 6 tentativas já feitas)
        row = len(tentativas)
        if row < 6:
            for j in range(WORD_LEN):
                x, y = CELL_POS[row][j]
                pygame.draw.rect(screen, CINZA, (x, y, CELL, CELL), border_radius=6)
                if j < len(tentativa_atual):
                    surf = render_letter(tentativa_atual[j])
                    sw, sh = surf.get_size()
                    screen.blit(surf, (x + (CELL - sw) // 2, y + (CELL - sh) // 2))

        pygame.display.flip()

    # reiniciar estado
    def reiniciar():
        nonlocal palavra_secreta, tentativas, tentativa_atual, tentativas_restantes, fim_de_jogo, palavras_possiveis
        palavra_secreta = escolher_palavra()
        tentativas = []
        tentativa_atual = ""
        tentativas_restantes = 6
        fim_de_jogo = False
        palavras_possiveis = WORDS.copy()
        if ia_jogar:
            print("IA joga. palavra:", palavra_secreta)

    # inicialização
    palavra_secreta = escolher_palavra()
    tentativas = []
    tentativa_atual = ""
    tentativas_restantes = 6
    fim_de_jogo = False
    palavras_possiveis = WORDS.copy()

    if ia_jogar:
        print("IA joga. palavra:", palavra_secreta)

    clock = pygame.time.Clock()
    next_ai_time = 0  # para agendar ações da IA sem bloquear o loop

    running = True
    while running:
        now = pygame.time.get_ticks()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            if not ia_jogar and ev.type == pygame.KEYDOWN and not fim_de_jogo:
                if ev.key == pygame.K_BACKSPACE:
                    tentativa_atual = tentativa_atual[:-1]
                elif ev.key == pygame.K_RETURN and len(tentativa_atual) == WORD_LEN:
                    resultado = compute_result_fast(
                        list(palavra_secreta),
                        WORD_COUNTS_ARR[WORD_INDEX[palavra_secreta]],
                        tentativa_atual,
                    )
                    tentativas.append((tentativa_atual, resultado))
                    tentativas_restantes -= 1
                    if tentativa_atual == palavra_secreta:
                        fim_de_jogo = True
                        print("Acertou!")
                    elif tentativas_restantes == 0:
                        fim_de_jogo = True
                        print(f"Fim. Palavra: {palavra_secreta}")
                    tentativa_atual = ""
                elif (len(tentativa_atual) < WORD_LEN) and ev.unicode.isalpha():
                    tentativa_atual += ev.unicode.lower()

        # IA: executa ações agendadas (não usar time.sleep no loop)
        if ia_jogar and not fim_de_jogo and now >= next_ai_time:
            next_ai_time = now + 120  # ms entre ações da IA (~0.12s)
            if tentativas_restantes == 6:
                tentativa_atual = (
                    melhores_palavras[0] if melhores_palavras else escolher_palavra()
                )
                resultado = compute_result_fast(
                    list(palavra_secreta),
                    WORD_COUNTS_ARR[WORD_INDEX[palavra_secreta]],
                    tentativa_atual,
                )
                tentativas.append((tentativa_atual, resultado))
                tentativas_restantes -= 1
                palavras_possiveis = filtrar_palavras(
                    palavras_possiveis, tentativa_atual, resultado
                )
            else:
                if palavras_possiveis:
                    tentativa_atual = melhor_tentativa(palavras_possiveis)
                    resultado = compute_result_fast(
                        list(palavra_secreta),
                        WORD_COUNTS_ARR[WORD_INDEX[palavra_secreta]],
                        tentativa_atual,
                    )
                    tentativas.append((tentativa_atual, resultado))
                    tentativas_restantes -= 1
                    if tentativa_atual == palavra_secreta:
                        fim_de_jogo = True
                        print(f"IA acertou em {6 - tentativas_restantes} tentativas")
                    elif tentativas_restantes == 0:
                        fim_de_jogo = True
                        print(f"IA não acertou. Palavra: {palavra_secreta}")
                    palavras_possiveis = filtrar_palavras(
                        palavras_possiveis, tentativa_atual, resultado
                    )
                    tentativa_atual = ""
                else:
                    fim_de_jogo = True
                    print("IA sem candidatos.")

        desenhar_tela(tentativas, tentativa_atual)

        if fim_de_jogo:
            print("Pressione Espaço para reiniciar ou Q para sair.")
            esperando = True
            while esperando:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        return
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_SPACE:
                            reiniciar()
                            esperando = False
                        elif ev.key == pygame.K_q:
                            pygame.quit()
                            return

        clock.tick(60)  # limita para 60 FPS

    pygame.quit()


# executar IA por padrão (mude para False para jogar manual)
if __name__ == "__main__":
    random.seed()
    jogar_wordle(ia_jogar=False)
