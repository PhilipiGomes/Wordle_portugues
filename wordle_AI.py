import os
import random
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt
from tqdm import tqdm

from lista import melhores_palavras, palavras  # suas listas (minúsculas, mesmo tamanho)

# -------------------- Pré-processamento --------------------
WORDS = palavras
N_WORDS = len(WORDS)
WORD_LEN = len(WORDS[0]) if N_WORDS else 0

ALPHABET = sorted({ch for w in WORDS for ch in w})
ALPHABET_IDX = {ch: i for i, ch in enumerate(ALPHABET)}
ALPHABET_SIZE = len(ALPHABET)

WORD_CHARS = [list(w) for w in WORDS]


def _counts_arr(word):
    arr = [0] * ALPHABET_SIZE
    for ch in word:
        arr[ALPHABET_IDX[ch]] += 1
    return arr


WORD_COUNTS_ARR = [_counts_arr(w) for w in WORDS]
WORD_INDEX = {w: i for i, w in enumerate(WORDS)}
WORDS_BY_LEN = {WORD_LEN: WORDS}


# -------------------- Funções rápidas --------------------
def escolher_palavra(tamanho=None):
    tamanho = tamanho or WORD_LEN
    escolhas = WORDS_BY_LEN.get(tamanho, WORDS)
    # trunk-ignore(bandit/B311)
    return random.choice(escolhas)


def compute_result_fast(secret_chars, secret_counts_arr, attempt):
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
    res = []
    for w in candidatos:
        idx = WORD_INDEX[w]
        if (
            compute_result_fast(WORD_CHARS[idx], WORD_COUNTS_ARR[idx], tentativa)
            == resultado
        ):
            res.append(w)
    return res


def melhor_tentativa(palavras_possiveis):
    if not palavras_possiveis:
        return ""
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


# -------------------- Jogo / Simulação unitária --------------------
def jogar_wordle(ia_jogar=False, palavra_inicial=None):
    palavra_secreta = escolher_palavra()
    idx_secret = WORD_INDEX[palavra_secreta]
    secret_chars = WORD_CHARS[idx_secret]
    secret_counts = WORD_COUNTS_ARR[idx_secret]

    palavras_possiveis = WORDS.copy()
    tentativas_restantes = 6
    tentativas_usadas = 0

    while tentativas_restantes > 0:
        if not ia_jogar:
            return None

        if tentativas_restantes == 6:
            tentativa_atual = palavra_inicial or (
                melhores_palavras[0] if melhores_palavras else escolher_palavra()
            )
        else:
            tentativa_atual = melhor_tentativa(palavras_possiveis)

        if not tentativa_atual:
            return None

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


# worker de processo (sempre top-level)
def _sim_once(_):
    # argumento ignorado, existe só para permitir map(range(n))
    return jogar_wordle(ia_jogar=True)


# -------------------- Simulação paralela --------------------
def simular_jogos_parallel(n, max_workers=None, chunksize=1):
    """
    Simula `n` jogos em paralelo com ProcessPoolExecutor.
    Retorna lista de resultados (somente jogos ganhos — ints).
    """
    start = time.time()
    resultados = []

    # ajustar chunksize por segurança quando None ou > n
    chunksize = int(max(1, chunksize))

    with ProcessPoolExecutor(max_workers=max_workers) as exc:
        # passamos um iterable de n elementos (os valores não importam dentro do worker)
        mapped = exc.map(_sim_once, range(n), chunksize=chunksize)
        # iteramos com tqdm para mostrar progresso
        for res in tqdm(mapped, total=n, desc="Simulando jogos (paralelo)", ncols=100):
            if res is not None:
                resultados.append(res)

    elapsed = time.time() - start
    # relatório curto
    # trunk-ignore(bandit/B605)
    os.system("cls" if os.name == "nt" else "clear")
    h = int(elapsed // 3600)
    m = int((elapsed % 3600) // 60)
    s = elapsed % 60
    print(f"Tempo total (paralelo): {h}h {m}min {s:.3f}s")
    avg = elapsed / n if n > 0 else float("nan")
    print(f"Média por simulação: {avg:.6f}s")
    return resultados


# -------------------- Execução principal --------------------
if __name__ == "__main__":
    # trunk-ignore(bandit/B605)
    os.system("cls" if os.name == "nt" else "clear")
    random.seed()

    numero_de_jogos = 10000
    # ajuste max_workers conforme CPU; None => usa default do executor
    resultados = simular_jogos_parallel(numero_de_jogos, max_workers=None, chunksize=4)

    jogos_ganhos = len(resultados)
    media_melhores_palavras = (
        (sum(resultados) / jogos_ganhos) if jogos_ganhos > 0 else float("nan")
    )
    print(
        f"Jogos simulados: {numero_de_jogos}, Jogos ganhos: {jogos_ganhos}, porcentagem de vitórias: {(jogos_ganhos/numero_de_jogos)*100}%"
    )
    mp = melhores_palavras[0] if melhores_palavras else "<sem_melhor>"
    print(f"Média de tentativas da palavra {mp}: {media_melhores_palavras:.6f}")

    # Plot
    contagem_vitorias = Counter(resultados)
    tentativas = sorted(contagem_vitorias.keys())
    vitorias = [contagem_vitorias[t] for t in tentativas]

    plt.figure(figsize=(10, 7))
    plt.bar(tentativas, vitorias)
    plt.xlabel("Número de Tentativas")
    plt.ylabel("Número de Vitórias")
    plt.title("Número de Vitórias por Número de Tentativas")
    plt.xticks(tentativas)
    plt.grid(axis="y")
    plt.show()
