import random
from collections import Counter
import time
import matplotlib.pyplot as plt

from lista import palavras, melhor_palavra


# Funções auxiliares
def escolher_palavra(tamanho=None):
    palavras_filtradas = [p.lower() for p in palavras if len(p) == (tamanho if tamanho else len(palavras[0]))]
    return random.choice(palavras_filtradas)


def verificar_palavra(palavra_secreta, tentativa):
    palavra_secreta = palavra_secreta.lower()
    tentativa = tentativa.lower()

    if len(palavra_secreta) != len(tentativa):
        raise ValueError("A tentativa e a palavra secreta devem ter o mesmo comprimento.")

    resultado = ["⬜"] * len(tentativa)
    palavra_secreta_lista = list(palavra_secreta)
    tentativa_lista = list(tentativa)

    for i, letra in enumerate(tentativa):
        if letra == palavra_secreta[i]:
            resultado[i] = "🟩"
            palavra_secreta_lista[i] = None
            tentativa_lista[i] = None

    for i, letra in enumerate(tentativa):
        if tentativa_lista[i] is not None:
            if letra in palavra_secreta_lista:
                resultado[i] = "🟨"
                palavra_secreta_lista[palavra_secreta_lista.index(letra)] = None

    return "".join(resultado)


def filtrar_palavras(lista_palavra, tentativa, resultado):
    tentativa = tentativa.lower()
    resultado = resultado.lower()
    palavras_filtradas = []

    for palavra in lista_palavra:
        palavra = palavra.lower()
        letras_confirmadas = {}
        letras_invalidas = set()
        palavra_valida = True

        for i, letra in enumerate(tentativa):
            if resultado[i] == "🟩":
                if palavra[i] != letra:
                    palavra_valida = False
                    break
                letras_confirmadas[letra] = letras_confirmadas.get(letra, 0) + 1

        if not palavra_valida:
            continue

        for i, letra in enumerate(tentativa):
            if resultado[i] == "🟨":
                if letra not in palavra or palavra[i] == letra:
                    palavra_valida = False
                    break
                letras_confirmadas[letra] = letras_confirmadas.get(letra, 0) + 1

        if not palavra_valida:
            continue

        for i, letra in enumerate(tentativa):
            if resultado[i] == "⬜":
                if letra in palavra:
                    if palavra.count(letra) > letras_confirmadas.get(letra, 0):
                        palavra_valida = False
                        break
                    letras_invalidas.add(letra)

        if palavra_valida:
            palavras_filtradas.append(palavra)

    return palavras_filtradas


def melhor_tentativa(palavras_possiveis):
    if not palavras_possiveis:
        return ""

    contador_posicional = [Counter() for _ in range(len(palavras_possiveis[0]))]

    # Contabiliza a frequência de cada letra em cada posição das palavras possíveis
    for palavra in palavras_possiveis:
        for i, letra in enumerate(palavra):
            contador_posicional[i][letra] += 1

    # Pontua as palavras com base nas frequências
    def pontuar_palavra(palavra):
        score = sum(contador_posicional[i][letra] for i, letra in enumerate(palavra))
        # Penaliza palavras com letras repetidas (não favorece tanto duplicatas)
        score -= len(set(palavra)) - len(palavra)
        return score

    # Retorna a palavra com a maior pontuação
    return max(palavras_possiveis, key=pontuar_palavra)


def jogar_wordle(ia_jogar=False):
    palavra_secreta = escolher_palavra()
    tentativas = []
    tentativa_atual = ""
    tentativas_restantes = 6
    fim_de_jogo = False
    palavras_possiveis = [p for p in palavras if len(p) == len(palavra_secreta)]

    while True:
        if ia_jogar and not fim_de_jogo:
            if tentativas_restantes == 6:
                tentativa_atual = melhor_palavra[0]
            else:
                if palavras_possiveis:
                    tentativa_atual = melhor_tentativa(palavras_possiveis)

            if tentativa_atual:
                resultado = verificar_palavra(palavra_secreta, tentativa_atual)
                tentativas.append((tentativa_atual, resultado))
                tentativas_restantes -= 1
                palavras_possiveis = filtrar_palavras(palavras_possiveis, tentativa_atual, resultado)

                if tentativa_atual == palavra_secreta or tentativas_restantes == 0:
                    return 6 - tentativas_restantes
                tentativa_atual = ""


def simular_jogos(n):
    start = time.time()
    vitorias_por_tentativas = []

    for i in range(n):
        tentativas_usadas = jogar_wordle(ia_jogar=True)
        vitorias_por_tentativas.append(tentativas_usadas)
        porcentagem = (i/n)*100
        if porcentagem % 5 == 0:
            print(f'{porcentagem}%')
        i += 1
    elapsed = time.time() - start
    tempo_medio = elapsed / n
    print(f"Tempo para executar todos os jogos: {elapsed:.5f}")
    print(f"Tempo médio de execução por jogo: {tempo_medio:.5f}")
    return vitorias_por_tentativas


# Configurar o número de jogos para simular
numero_de_jogos = 2000
resultados = simular_jogos(numero_de_jogos)
media_melhor_palavra = sum(resultados)/numero_de_jogos
print(f'Média de tentativas da palavra {melhor_palavra[0]}: {media_melhor_palavra}')

# Contar o número de vitórias por número de tentativas
contagem_vitorias = Counter(resultados)

# Plotar gráfico
tentativas = list(contagem_vitorias.keys())
vitorias = [contagem_vitorias[t] for t in tentativas]

plt.figure(figsize=(10, 7))
plt.bar(tentativas, vitorias, color='skyblue')
plt.xlabel('Número de Tentativas')
plt.ylabel('Número de Vitórias')
plt.title('Número de Vitórias por Número de Tentativas')
plt.xticks(tentativas)
plt.grid(axis='y')
plt.show()
