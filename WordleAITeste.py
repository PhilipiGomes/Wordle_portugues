import random
from collections import Counter
import time
import matplotlib.pyplot as plt
import os
from tqdm import tqdm  # Importando tqdm para a barra de progresso

from lista import palavras, melhores_palavras


# Funções auxiliares
def escolher_palavra(tamanho=None):
    # Filtra palavras com o tamanho correto, sem precisar fazer lower() em todas as palavras
    palavras_filtradas = list(filter(lambda p: len(p) == (tamanho if tamanho else len(palavras[0])), palavras))
    return random.choice(palavras_filtradas).lower()


def verificar_palavra(palavra_secreta, tentativa):
    if len(palavra_secreta) != len(tentativa):
        raise ValueError("A tentativa e a palavra secreta devem ter o mesmo comprimento.")

    resultado = ["⬜"] * len(tentativa)
    palavra_secreta_lista = list(palavra_secreta)
    tentativa_lista = list(tentativa)

    # Primeira iteração para marcas "🟩"
    for i, letra in enumerate(tentativa):
        if letra == palavra_secreta[i]:
            resultado[i] = "🟩"
            palavra_secreta_lista[i] = None
            tentativa_lista[i] = None

    # Segunda iteração para marcas "🟨"
    for i, letra in enumerate(tentativa):
        if tentativa_lista[i] is not None and letra in palavra_secreta_lista:
            resultado[i] = "🟨"
            palavra_secreta_lista[palavra_secreta_lista.index(letra)] = None

    return "".join(resultado)


def filtrar_palavras(lista_palavra, tentativa, resultado):
    letras_confirmadas = {}
    letras_invalidas = set()

    palavras_filtradas = [
        palavra for palavra in lista_palavra
        if valida_palavra(palavra, tentativa, resultado, letras_confirmadas, letras_invalidas)
    ]
    return palavras_filtradas


def valida_palavra(palavra, tentativa, resultado, letras_confirmadas, letras_invalidas):
    palavra = palavra.lower()
    palavra_valida = True

    # Processa letras confirmadas (🟩)
    for i, letra in enumerate(tentativa):
        if resultado[i] == "🟩":
            if palavra[i] != letra:
                return False
            letras_confirmadas[letra] = letras_confirmadas.get(letra, 0) + 1

    # Processa letras parcialmente corretas (🟨)
    for i, letra in enumerate(tentativa):
        if resultado[i] == "🟨":
            if letra not in palavra or palavra[i] == letra:
                return False
            letras_confirmadas[letra] = letras_confirmadas.get(letra, 0) + 1

    # Processa letras incorretas (⬜)
    for i, letra in enumerate(tentativa):
        if resultado[i] == "⬜" and letra in palavra:
            if palavra.count(letra) > letras_confirmadas.get(letra, 0):
                return False
            letras_invalidas.add(letra)

    return palavra_valida


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
        return sum(contador_posicional[i][letra] for i, letra in enumerate(palavra))

    # Retorna a palavra com a maior pontuação
    return max(palavras_possiveis, key=pontuar_palavra)


def jogar_wordle(ia_jogar=False):
    palavra_secreta = escolher_palavra()
    tentativas = []
    tentativas_restantes = 6
    palavras_possiveis = [p for p in palavras if len(p) == len(palavra_secreta)]

    while tentativas_restantes > 0:
        tentativa_atual = ""
        if ia_jogar:
            if tentativas_restantes == 6:
                tentativa_atual = melhores_palavras[0]
            elif palavras_possiveis:
                tentativa_atual = melhor_tentativa(palavras_possiveis)

        if tentativa_atual:
            resultado = verificar_palavra(palavra_secreta, tentativa_atual)
            tentativas.append((tentativa_atual, resultado))
            tentativas_restantes -= 1
            palavras_possiveis = filtrar_palavras(palavras_possiveis, tentativa_atual, resultado)

            if tentativa_atual == palavra_secreta:
                return 6 - tentativas_restantes

    return None  # Alterado para None quando houver derrota


def simular_jogos(n):
    start = time.time()
    vitorias_por_tentativas = []

    # Usando tqdm para mostrar a barra de progresso
    for _ in tqdm(range(n), desc="Simulando jogos", ncols=100):  # Barra de progresso com tqdm
        tentativas_usadas = jogar_wordle(ia_jogar=True)
        if tentativas_usadas is not None:  # Ignora derrotas
            vitorias_por_tentativas.append(tentativas_usadas)

    elapsed = time.time() - start
    tempo_medio = elapsed / n
    os.system('cls')  # Limpa a tela após o término da execução
    horas = elapsed // 3600
    minutos = (elapsed - (horas * 3600)) // 60
    segundos = (elapsed - ((horas * 3600) + (minutos * 60)))
    print(f"Tempo total: {int(horas)}h, {int(minutos)}min, {segundos:.5f}s")
    print(f"Tempo médio por jogo: {tempo_medio:.5f}s")
    return vitorias_por_tentativas


# Limpar a tela antes de iniciar a simulação
os.system('cls')

# Configurar o número de jogos para simular
numero_de_jogos = 4000
resultados = simular_jogos(numero_de_jogos)
media_melhores_palavras = sum(resultados) / len(resultados)
print(f'Jogos simulados: {numero_de_jogos}, Jogos ganhos: {len(resultados)}')
print(f'Média de tentativas da palavra {melhores_palavras[0]}: {media_melhores_palavras}')

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
