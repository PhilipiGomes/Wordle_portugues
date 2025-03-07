import random
import time
from collections import Counter
from lista import palavras
import os
from tqdm import tqdm  # Importando a biblioteca tqdm para barras de progresso
from concurrent.futures import ProcessPoolExecutor  # Para paralelização


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
        return sum(contador_posicional[i][letra] for i, letra in enumerate(palavra))

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
        else:
            break
    return None


# Função para simular os jogos
def simular_jogos_com_palavra_inicial_func(palavra_inicial, n_simulacoes_por_palavra):
    return (palavra_inicial, simular_jogos_com_palavra_inicial(n_simulacoes_por_palavra, palavra_inicial))

def simular_jogos_com_palavra_inicial(n, palavra_inicial):
    resultados = []
    for _ in range(n):
        tentativas_usadas = jogar_wordle(ia_jogar=True, palavra_inicial=palavra_inicial)
        if tentativas_usadas is not None:
            resultados.append(tentativas_usadas)
    return (sum(resultados) / len(resultados)) if len(resultados) > 0 else sum(resultados)


# Função auxiliar para ser usada no `map` (evita o uso de `lambda`)
def map_simular_palavra(palavra, n_simulacoes_por_palavra):
    return simular_jogos_com_palavra_inicial_func(palavra, n_simulacoes_por_palavra)

def encontrar_melhor_palavra_inicial(n_simulacoes_por_palavra):
    start = time.time()

    melhores_palavras = []
    
    # Paralelizando a simulação com ProcessPoolExecutor
    with ProcessPoolExecutor() as executor:
        # Substituímos a função lambda pela função auxiliar
        resultados = list(tqdm(executor.map(map_simular_palavra, palavras, [n_simulacoes_por_palavra]*len(palavras)), desc="Simulando jogos", ncols=100, total=len(palavras)))

    # Organiza as palavras por melhor desempenho
    melhores_palavras = sorted(resultados, key=lambda x: x[1])
    piores_palavras = sorted(resultados, key=lambda x: x[1], reverse=True)

    finish = time.time()
    elapsed = finish - start
    os.system('cls')
    horas = elapsed // 3600
    minutos = (elapsed - (horas * 3600)) // 60
    segundos = (elapsed - ((horas * 3600) + (minutos * 60)))
    print(f"Tempo total: {int(horas)}h, {int(minutos)}min, {segundos:.5f}s")
    print(f'Média por simulação: {elapsed / len(palavras) / n_simulacoes_por_palavra:.5f}s')
    print(f'Média por palavra: {elapsed / len(palavras):.5f}s')
    return melhores_palavras, piores_palavras


if __name__ == "__main__":
    os.system('cls')
    n_simulacoes = 50
    melhores_palavras, piores_palavras = encontrar_melhor_palavra_inicial(n_simulacoes)
    print(f"As 10 melhores palavras iniciais de acordo com o teste são:{'\n'}{[(palavra, pontuacao) for palavra, pontuacao in melhores_palavras[:10]]}")
    print(f'Melhor palavra: ', [melhores_palavras[0][0]])
    print(f"As 10 piores palavras iniciais de acordo com o teste são:{'\n'}{[(palavra, pontuacao) for palavra, pontuacao in piores_palavras[:10]]}")
    print(f'Pior palavra: ', [piores_palavras[0][0]])

    print([melhores_palavras[0][0], piores_palavras[0][0]])
