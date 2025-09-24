import os
import random
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from tqdm import tqdm

from lista import palavras  # todas têm mesmo comprimento e já estão em minúsculas

# --- Pré-processamento robusto (suporta acentos/ç/qualquer caractere presente nas palavras) ---
WORDS = palavras  # já em minúsculas e mesmo comprimento
N_WORDS = len(WORDS)
WORD_LEN = len(WORDS[0]) if N_WORDS else 0

# conjunto do alfabeto presente nas palavras (ordenado só para determinismo)
ALPHABET = sorted({ch for w in WORDS for ch in w})
ALPHABET_IDX = {ch: i for i, ch in enumerate(ALPHABET)}
ALPHABET_SIZE = len(ALPHABET)

# lista de listas de chars para acesso rápido
WORD_CHARS = [list(w) for w in WORDS]


def _counts_arr(word):
    arr = [0] * ALPHABET_SIZE
    for ch in word:
        idx = ALPHABET_IDX.get(ch)
        if idx is not None:
            arr[idx] += 1
    return arr


WORD_COUNTS_ARR = [_counts_arr(w) for w in WORDS]
WORD_INDEX = {w: i for i, w in enumerate(WORDS)}


# --- Funções otimizadas ---
def compute_result_fast(secret_chars, secret_counts_arr, attempt):
    """Gera padrão sem assumir 'a'..'z' — usa ALPHABET_IDX."""
    res = ["⬜"] * WORD_LEN
    counts = secret_counts_arr[:]  # copia
    # verdes
    for i, ch in enumerate(attempt):
        if ch == secret_chars[i]:
            res[i] = "🟩"
            idx = ALPHABET_IDX.get(ch)
            if idx is not None:
                counts[idx] -= 1
    # amarelos
    for i, ch in enumerate(attempt):
        if res[i] == "⬜":
            idx = ALPHABET_IDX.get(ch)
            if idx is not None and counts[idx] > 0:
                res[i] = "🟨"
                counts[idx] -= 1
    return "".join(res)


def candidate_matches(candidate, guess, expected_result):
    """Verifica se candidate (segredo) produz expected_result para guess."""
    idx = WORD_INDEX[candidate]
    secret_chars = WORD_CHARS[idx]
    secret_counts = WORD_COUNTS_ARR[idx]
    return compute_result_fast(secret_chars, secret_counts, guess) == expected_result


def filtrar_palavras(lista_palavras, tentativa, resultado):
    """Mantém só candidatos que geram 'resultado' para 'tentativa'."""
    # list comprehension simples chamando candidate_matches (muito rápido com pré-cálculos)
    return [p for p in lista_palavras if candidate_matches(p, tentativa, resultado)]


def melhor_tentativa(palavras_possiveis):
    if not palavras_possiveis:
        return ""
    # contadores posicionais
    pos_counters = [Counter() for _ in range(WORD_LEN)]
    for w in palavras_possiveis:
        for i, ch in enumerate(w):
            pos_counters[i][ch] += 1

    def score(word):
        s = 0
        for i, ch in enumerate(word):
            s += pos_counters[i].get(ch, 0)
        return s

    return max(palavras_possiveis, key=score)


def escolher_palavra(tamanho=None):
    # todas mesmas, ignora tamanho
    # trunk-ignore(bandit/B311)
    return random.choice(WORDS)


# --- Simulação de um jogo com IA ---
def jogar_wordle(ia_jogar=False, palavra_inicial=None):
    palavra_secreta = escolher_palavra()
    idx_secret = WORD_INDEX[palavra_secreta]
    secret_chars = WORD_CHARS[idx_secret]
    secret_counts = WORD_COUNTS_ARR[idx_secret]

    tentativas_restantes = 6
    palavras_possiveis = WORDS.copy()
    tentativas_usadas = 0

    while tentativas_restantes > 0:
        if not ia_jogar:
            return None

        if tentativas_restantes == 6:
            tentativa_atual = palavra_inicial or escolher_palavra()
        else:
            tentativa_atual = melhor_tentativa(palavras_possiveis)

        resultado = compute_result_fast(secret_chars, secret_counts, tentativa_atual)
        tentativas_restantes -= 1
        tentativas_usadas += 1

        if tentativa_atual == palavra_secreta:
            return tentativas_usadas

        palavras_possiveis = filtrar_palavras(
            palavras_possiveis, tentativa_atual, resultado
        )
        if not palavras_possiveis:
            return None

    return None


# --- Estatísticas por palavra inicial ---
def simular_jogos_com_palavra_inicial(n, palavra_inicial):
    resultados = []
    for _ in range(n):
        usadas = jogar_wordle(ia_jogar=True, palavra_inicial=palavra_inicial)
        if usadas is not None:
            resultados.append(usadas)
    if resultados:
        return palavra_inicial, (sum(resultados) / len(resultados))
    return palavra_inicial, float("inf")


def _map_worker(args):
    return simular_jogos_com_palavra_inicial(*args)


def encontrar_melhor_palavra_inicial(n_simulacoes_por_palavra, max_workers=None):
    start = time.time()
    candidatos = WORDS
    resultados = []
    # cria dois iteráveis paralelos: primeiro argumento (n_sim) e segundo (palavra)
    iter_n = [n_simulacoes_por_palavra] * len(candidatos)
    # executor.map aceita várias iterables e passa elementos correspondentes às posições dos parâmetros
    with ProcessPoolExecutor(max_workers=max_workers) as exc:
        for res in tqdm(
            exc.map(simular_jogos_com_palavra_inicial, iter_n, candidatos),
            total=len(candidatos),
            desc="Simulando",
            ncols=100,
        ):
            resultados.append(res)

        melhores = sorted(resultados, key=lambda x: x[1])
        piores = sorted(resultados, key=lambda x: x[1], reverse=True)

    elapsed = time.time() - start
    # trunk-ignore(bandit/B605)
    os.system("cls" if os.name == "nt" else "clear")
    h = int(elapsed // 3600)
    m = int((elapsed % 3600) // 60)
    s = elapsed % 60
    print(f"Tempo total: {h}h {m}min {s:.3f}s")
    avg = elapsed / (len(candidatos) * n_simulacoes_por_palavra)
    print(f"Média por simulação: {avg:.6f}s")
    return melhores, piores


# --- Execução ---
if __name__ == "__main__":
    # trunk-ignore(bandit/B605)
    os.system("cls" if os.name == "nt" else "clear")
    random.seed()
    n_simulacoes = 10
    melhores, piores = encontrar_melhor_palavra_inicial(n_simulacoes)
    print()
    print("Top 3 melhores:", melhores[:3])
    print("Melhor:", melhores[0][0])
    print("Top 3 piores:", piores[:3])
    print("Pior:", piores[0][0])
