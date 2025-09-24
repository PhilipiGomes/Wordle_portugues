import random
import pygame
import time
from collections import Counter
from lista import palavras, melhor_palavra


# Funções auxiliares
def escolher_palavra():
    return random.choice(palavras)


def verificar_palavra(palavra_secreta, tentativa):
    resultado = ["⬜"] * len(tentativa)
    palavra_secreta_lista = list(palavra_secreta)
    tentativa_lista = list(tentativa)

    # Primeira passada: marca os acertos exatos (🟩)
    for i in range(len(tentativa)):
        if tentativa[i] == palavra_secreta[i]:
            resultado[i] = "🟩"
            palavra_secreta_lista[i] = None
            tentativa_lista[i] = None

    # Segunda passada: marca os acertos parciais (🟨)
    for i in range(len(tentativa)):
        if tentativa_lista[i] is not None and tentativa_lista[i] in palavra_secreta_lista:
            resultado[i] = "🟨"
            palavra_secreta_lista[palavra_secreta_lista.index(tentativa_lista[i])] = None

    return "".join(resultado)


def melhor_tentativa(palavras_possiveis):
    if not palavras_possiveis:
        return ""  # Retorna uma string vazia se não houver palavras possíveis

    # Contador de letras ponderado por posição
    contador_posicional = [Counter() for _ in range(len(palavras_possiveis[0]))]

    for palavra in palavras_possiveis:
        for i, letra in enumerate(palavra):
            contador_posicional[i][letra] += 1

    # Função para pontuar a palavra
    def pontuar_palavra(palavra):
        score = sum(contador_posicional[i][letra] for i, letra in enumerate(palavra))
        # Penaliza palavras com letras repetidas para variar mais as tentativas
        score -= len(set(palavra)) - len(palavra)
        return score

    # Escolhe a palavra com maior pontuação baseada na frequência ponderada por posição
    return max(palavras_possiveis, key=pontuar_palavra)


def filtrar_palavras(palavras, tentativa, resultado):
    palavras_filtradas = []

    for palavra in palavras:
        palavra_valida = True
        letras_confirmadas = {}

        # Primeira passada: validar 🟩 e contar letras confirmadas
        for i, letra in enumerate(tentativa):
            if resultado[i] == "🟩":
                if palavra[i] != letra:
                    palavra_valida = False
                    break
                letras_confirmadas[letra] = letras_confirmadas.get(letra, 0) + 1

        if not palavra_valida:
            continue

        # Segunda passada: validar 🟨 e garantir que estão em outras posições
        for i, letra in enumerate(tentativa):
            if resultado[i] == "🟨":
                if letra not in palavra or palavra[i] == letra:
                    palavra_valida = False
                    break
                letras_confirmadas[letra] = letras_confirmadas.get(letra, 0) + 1

        if not palavra_valida:
            continue

        # Terceira passada: validar ⬜ (não deve estar presente ou contar corretamente se for letra repetida)
        for i, letra in enumerate(tentativa):
            if resultado[i] == "⬜":
                if letra in palavra:
                    if palavra.count(letra) > letras_confirmadas.get(letra, 0):
                        palavra_valida = False
                        break

        if palavra_valida:
            palavras_filtradas.append(palavra)

    return palavras_filtradas


def jogar_wordle(ia_jogar=False):
    pygame.init()

    # Definir cores
    BRANCO = (255, 255, 255)
    PRETO = (0, 0, 0)
    VERDE = (0, 255, 0)
    AMARELO = (255, 255, 0)
    CINZA = (128, 128, 128)

    # Configurações da janela
    largura, altura = 400, 600
    tela = pygame.display.set_mode((largura, altura))
    pygame.display.set_caption("Wordle em Português")

    # Configuração da fonte
    fonte = pygame.font.Font(None, 60)
    fonte_pequena = pygame.font.Font(None, 40)

    # Função para desenhar a tela do jogo
    def desenhar_tela():
        tela.fill(PRETO)

        # Desenhar tentativas anteriores
        for i, tentativa in enumerate(tentativas):
            for j, letra in enumerate(tentativa[0]):
                if tentativa[1][j] == "🟩":
                    cor = VERDE
                elif tentativa[1][j] == "🟨":
                    cor = AMARELO
                else:
                    cor = CINZA
                pygame.draw.rect(tela, cor, (j * 60 + 50, i * 80 + 50, 50, 50))
                texto = fonte.render(letra.upper(), True, BRANCO)
                tela.blit(texto, (j * 60 + 60, i * 80 + 50))

        # Desenhar a tentativa atual
        for i, letra in enumerate(tentativa_atual):
            pygame.draw.rect(tela, CINZA, (i * 60 + 50, len(tentativas) * 80 + 50, 50, 50))
            texto = fonte.render(letra.upper(), True, BRANCO)
            tela.blit(texto, (i * 60 + 60, len(tentativas) * 80 + 50))

        pygame.display.flip()

    # Função para reiniciar o jogo
    def reiniciar_jogo():
        nonlocal palavra_secreta, tentativas, tentativa_atual, tentativas_restantes, fim_de_jogo, palavras_possiveis
        palavra_secreta = escolher_palavra()
        tentativas = []
        tentativa_atual = ""
        tentativas_restantes = 6
        fim_de_jogo = False
        palavras_possiveis = [p for p in palavras if len(p) == len(palavra_secreta)]
        if ia_jogar:
            print(f"A IA está jogando. Palavra secreta: {palavra_secreta}")

    # Inicializar variáveis do jogo
    palavra_secreta = escolher_palavra()
    tentativas = []
    tentativa_atual = ""
    tentativas_restantes = 6
    fim_de_jogo = False
    palavras_possiveis = [p for p in palavras if len(p) == len(palavra_secreta)]

    if ia_jogar:
        print(f"A IA está jogando. Palavra secreta: {palavra_secreta}")

    # Loop principal do jogo
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            # Processar entrada de teclado durante o jogo
            if not ia_jogar and evento.type == pygame.KEYDOWN and not fim_de_jogo:
                if evento.key == pygame.K_BACKSPACE:
                    tentativa_atual = tentativa_atual[:-1]
                elif evento.key == pygame.K_RETURN and len(tentativa_atual) == len(palavra_secreta):
                    resultado = verificar_palavra(palavra_secreta, tentativa_atual)
                    tentativas.append((tentativa_atual, resultado))
                    tentativas_restantes -= 1
                    print(tentativas)
                    if tentativa_atual == palavra_secreta:
                        fim_de_jogo = True
                        print("Parabéns! Você acertou!")
                    elif tentativas_restantes == 0:
                        fim_de_jogo = True
                        print(f"Fim de jogo! A palavra era {palavra_secreta}.")
                    tentativa_atual = ""
                elif len(tentativa_atual) < len(palavra_secreta) and evento.unicode.isalpha():
                    tentativa_atual += evento.unicode.lower()

        if ia_jogar and not fim_de_jogo:
            if tentativas_restantes == 6:
                time.sleep(0.1)
                tentativa_atual = melhor_palavra[0]
                resultado = verificar_palavra(palavra_secreta, tentativa_atual)
                tentativas.append((tentativa_atual, resultado))
                tentativas_restantes -= 1
                palavras_possiveis = filtrar_palavras(palavras_possiveis, tentativa_atual, resultado)

            else:
                if palavras_possiveis:
                    time.sleep(0.1)
                    tentativa_atual = melhor_tentativa(palavras_possiveis)
                    resultado = verificar_palavra(palavra_secreta, tentativa_atual)
                    tentativas.append((tentativa_atual, resultado))
                    tentativas_restantes -= 1
                    palavras_possiveis = filtrar_palavras(palavras_possiveis, tentativa_atual, resultado)

                    if tentativa_atual == palavra_secreta:
                        fim_de_jogo = True
                        print(f"A IA acertou a palavra em {6 - tentativas_restantes} tentativas.")
                    elif tentativas_restantes == 0:
                        fim_de_jogo = True
                        print(f"A IA não acertou a palavra, que era {palavra_secreta}.")
                    tentativa_atual = ""
                else:
                    fim_de_jogo = True
                    print("A IA ficou sem palavras possíveis.")

        desenhar_tela()

        if fim_de_jogo:
            print("Pressione a barra de espaço para reiniciar ou 'q' para sair.")
            esperando_entrada = True
            while esperando_entrada:
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        pygame.quit()
                        return
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_SPACE:
                            reiniciar_jogo()
                            esperando_entrada = False
                        elif evento.key == pygame.K_q:
                            pygame.quit()
                            return

    pygame.quit()


# Escolha entre jogar manualmente ou com IA
jogar_wordle(ia_jogar=True)  # True: IA joga, False: Humano joga
