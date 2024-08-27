import random
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from lista import palavras


# Funções auxiliares
def escolher_palavra(tamanho=None):
    filtro = [p.lower() for p in palavras if len(p) == (tamanho if tamanho else len(palavras[0]))]
    return random.choice(filtro)


def verificar_palavra(palavra_secreta, tentativa):
    palavra_secreta = palavra_secreta.lower()
    tentativa = tentativa.lower()

    if len(palavra_secreta) != len(tentativa):
        raise ValueError("A tentativa e a palavra secreta devem ter o mesmo comprimento.")

    resultado = ["⬜"] * len(tentativa)
    contador_palavra = Counter(palavra_secreta)
    palavra_secreta_lista = list(palavra_secreta)

    for i, (p, t) in enumerate(zip(palavra_secreta, tentativa)):
        if t == p:
            resultado[i] = "🟩"
            contador_palavra[t] -= 1
            palavra_secreta_lista[i] = None

    for i, t in enumerate(tentativa):
        if resultado[i] != "🟩" and t in palavra_secreta_lista:
            if contador_palavra[t] > 0:
                resultado[i] = "🟨"
                contador_palavra[t] -= 1
                palavra_secreta_lista[palavra_secreta_lista.index(t)] = None

    return "".join(resultado)


def filtrar_palavras(lista_palavras, tentativa, resultado):
    tentativa = tentativa.lower()
    palavras_filtradas = []

    for palavra in lista_palavras:
        palavra = palavra.lower()
        palavra_valida = True
        letras_confirmadas = Counter()
        letras_invalidas = set()

        for i in range(len(tentativa)):
            if resultado[i] == "🟩":
                if palavra[i] != tentativa[i]:
                    palavra_valida = False
                    break
                letras_confirmadas[tentativa[i]] += 1

        if not palavra_valida:
            continue

        for i in range(len(tentativa)):
            if resultado[i] == "🟨":
                if tentativa[i] not in palavra or palavra[i] == tentativa[i]:
                    palavra_valida = False
                    break
                letras_confirmadas[tentativa[i]] += 1

        if not palavra_valida:
            continue

        for i in range(len(tentativa)):
            if resultado[i] == "⬜":
                if tentativa[i] in palavra and palavra.count(tentativa[i]) > letras_confirmadas[tentativa[i]]:
                    palavra_valida = False
                    break
                letras_invalidas.add(tentativa[i])

        if palavra_valida:
            palavras_filtradas.append(palavra)

    return palavras_filtradas


def melhor_tentativa(palavras_possiveis):
    if not palavras_possiveis:
        return ""

    contador_posicional = [Counter() for _ in range(len(palavras_possiveis[0]))]

    for palavra in palavras_possiveis:
        for i, letra in enumerate(palavra):
            contador_posicional[i][letra] += 1

    def pontuar_palavra(palavra):
        score = sum(contador_posicional[i][letra] for i, letra in enumerate(palavra))
        return score

    return max(palavras_possiveis, key=pontuar_palavra)


def jogar_wordle(ia_jogar=False, palavra_inicial=None):
    palavra_secreta = escolher_palavra()
    tentativas = []
    tentativas_restantes = 6
    palavras_possiveis = [p for p in palavras if len(p) == len(palavra_secreta)]

    while tentativas_restantes > 0:
        if ia_jogar:
            if tentativas_restantes == 6:
                tentativa_atual = palavra_inicial or escolher_palavra(tamanho=len(palavra_secreta))
            else:
                tentativa_atual = melhor_tentativa(palavras_possiveis)

            resultado = verificar_palavra(palavra_secreta, tentativa_atual)
            tentativas.append((tentativa_atual, resultado))
            tentativas_restantes -= 1
            palavras_possiveis = filtrar_palavras(palavras_possiveis, tentativa_atual, resultado)

            if tentativa_atual == palavra_secreta:
                return 6 - tentativas_restantes
            if tentativas_restantes == 0:
                return 7
        else:
            break


def simular_jogos_com_palavra_inicial(n, palavra_inicial):
    resultados = [jogar_wordle(ia_jogar=True, palavra_inicial=palavra_inicial) for _ in range(n)]
    return sum(resultados) / len(resultados)


def simular_jogos_em_sublista(subpalavras, n_simulacoes):
    melhores_palavras = []
    for idx, palavra in enumerate(subpalavras):
        media_tentativas = simular_jogos_com_palavra_inicial(n_simulacoes, palavra)
        melhores_palavras.append((palavra, media_tentativas))
    return melhores_palavras


def encontrar_melhor_palavra_inicial(n_simulacoes_por_palavra, n_processos):
    start = time.time()

    sublistas_palavras = [palavras[i::n_processos] for i in range(n_processos)]

    with ProcessPoolExecutor(max_workers=n_processos) as executor:
        resultados_futuros = [executor.submit(simular_jogos_em_sublista, sublista, n_simulacoes_por_palavra)
                              for sublista in sublistas_palavras]

        melhores_palavras_sublistas = []
        for i, futuro in enumerate(resultados_futuros):
            sublista_resultado = futuro.result()
            melhores_palavras_sublistas.extend(sublista_resultado)
            # Exibindo o progresso dos processos
            print(f"Processo {i + 1}/{n_processos} finalizado.")

    melhores_palavras_sublistas.sort(key=lambda x: x[1])
    finish = time.time()
    elapsed = finish - start
    print(f"Tempo total: {elapsed:.5f}s")
    print(f'Média por simulação: {elapsed / (n_processos * len(palavras)):.5f}s')
    print(f'Média por palavra: {elapsed / len(palavras):.5f}s')
    return melhores_palavras_sublistas


if __name__ == "__main__":
    n_simulacoes = 200
    n_processos = 60
    melhores_palavras = encontrar_melhor_palavra_inicial(n_simulacoes, n_processos)
    print("As 100 melhores palavras iniciais de acordo com o teste são:")
    top_100 = []
    for palavras in melhores_palavras[:100][0]:
        top_100.append(palavras)
    print(top_100)

