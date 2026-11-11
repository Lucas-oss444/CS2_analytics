# Histórico de versões

## 2.18.1
- Corrige a recuperação de um histórico corrompido no Windows: o arquivo ficava preso e o app não conseguia substituí-lo

## 2.18.0
- Perfil: escolha sua arma favorita; ela aparece com um mini adesivo ao lado do nome no menu lateral
- Social: "Cartão do perfil" gera uma imagem PNG com avatar e borda, favoritos, arma com adesivo e seus abates com ela, números de carreira, melhor mapa e qualidades

## 2.17.0
- Buscar jogador por nick: digite parte do nome em "Ver jogador" (e nas caixas de comparação da aba Social) e escolha na lista filtrada; a lista completa continua na setinha

## 2.16.2
- Rolagem suave e mais rápida com a roda do mouse, acumulando quando você gira rápido
- A roda não fica mais presa em cima dos gráficos nem muda caixas de seleção sem querer

## 2.16.1
- Caixinhas de checklist maiores, com borda e ✓ na cor do tema; metas cumpridas ficam verdes

## 2.16.0
- Evolução: desempenho por mapa e comparação antes e depois de uma partida escolhida, com gráfico e tabela
- Treino: metas da semana que marcam sozinhas e checklist diário com sequência de dias
- Nova aba 👥 Social: comparar com um amigo, cartão da partida em PNG e 14 conquistas com progresso
- O histórico passa a guardar vitória ou derrota de cada partida
- Tabela da Partida segue as cores do tema
- 99 testes automatizados

## 2.15.1
- FalleN também aparece em Lendas do Brasil

## 2.15.0
- Perfil: 28 times e 169 jogadores para escolher, com elencos de nov/2026 (novos: Virtus.pro, Nemiga, NRG, Envy, DENDELE, FlyQuest, Lynn Vision, TYLOO, Chinggis Warriors)
- Grupos de lendas: "Lendas do Brasil" (coldzera, fer, fnx, TACO, felps…) e "Lendas" (GeT_RiGhT, f0rest, olofmeister, kennyS, dev1ce…)
- Favorito salvo num time antigo é movido sozinho para o time atual do jogador

## 2.14.0
- Testes automatizados novos (84 no total): todas as abas e diálogos, o app em cada tema, dados extremos e arquivos corrompidos
- Os testes rodam numa pasta temporária e nunca tocam nos seus dados; atalho rodar_testes.bat (aceito pelo instalador de atualizações)
- Correção: histórico com valores inválidos não quebra mais as bordas por objetivo nem a seção de constância

## 2.13.2
- 🎥 Gravar: instrução corrigida, a barra da demo se esconde com Shift+F2

## 2.13.1
- 🎥 Gravar também esconde a barra de controle da demo (demo_ui_mode 0); F9 traz de volta

## 2.13.0
- Botão 🎥 Gravar nos clipes: abre o lance no CS2 sem HUD, na visão do jogador, 3 s antes da jogada; P pausa e F9 traz o HUD de volta

## 2.12.0
- Mais pros com dicas de fonte: KSCERATO, yuurih, karrigan, dev1ce, Magisk, Twistzz e sh1ro (17 jogadores, 38 dicas)
- Treino: nova seção 📅 Constância, com a variação do seu rating entre partidas e 10 dicas de constância apoiadas em falas de pros

## 2.11.1
- Aba Clipes: botão ⭐ Melhores jogadas em destaque, aberto por padrão

## 2.11.0
- Temas: Escuro, Claro, Meia-noite, OLED, Roxo, Floresta, Vermelho e Areia, escolhidos em 🎨 Tema na barra lateral

## 2.10.0
- 12 bordas novas: Oceano, Pôr do sol e Matrix liberadas; Quad, Clutch, Muralha, Carregador, Abridor, Flashbang, Maratonista e Lenda por objetivo
- O perfil mostra o objetivo de cada borda bloqueada e o progresso das que contam partidas
- 10 avatares novos: C4, Granada, Capacete, Faca, Gato, Raposa, Panda, Chama, Estrela e Joia

## 2.9.0
- Botões para copiar comandos do console do CS2: config de treino (agora em uma linha só), velocidade, repetir granada, noclip, bot e controle da demo
- Os treinos que usam comandos (counter-strafe, pop flash, lineups, flashes, revisão de demo) ganharam o botão de copiar ao lado

## 2.8.0
- Botões "?" com explicação ao passar o mouse: estatísticas (Rating, ADR, KAST, K/D…) e termos dos treinos e dicas (deathmatch, pop flash, lineup, prefire, counter-strafe, trade, clutch…)

## 2.7.0
- Mais pros nas dicas, todos com fonte: ZywOo, NiKo, m0NESY, ropz e apEX, além de donk, s1mple, FalleN, coldzera e fer
- Perfil: escolha seu time favorito e depois o jogador favorito do elenco (elencos de out/2026)
- Quando existe uma dica do seu jogador favorito, ela aparece primeiro

## 2.6.0
- Dicas de pros com fonte: cada ponto a melhorar e os principais treinos trazem o que donk, s1mple, FalleN, coldzera ou fer disseram sobre aquilo em entrevistas, vlogs e cursos, com link para o original

## 2.5.0
- Diagnóstico mais contextualizado: compara você com a referência e com o lobby, explica o que isso significa e dá uma meta para as próximas partidas
- Dicas com mais explicação de por que funcionam e de como conferir no app
- O app sugere quantos minutos por dia e quantos dias por semana treinar com base nas suas estatísticas; você pode ajustar para mais ou menos e voltar à sugestão com um clique
- Dias de descanso espalhados pela semana

## 2.5.0
- Explicações, dicas e treinos reescritos com mais contexto
- Cada ponto do diagnóstico mostra em quantos dados se baseia e a média do lobby

## 2.4.3
- O mapa 2D do Replay marca os bombs A e B

## 2.4.2
- No Replay, a lista de partidas mostra vitórias em azul e derrotas em vermelho

## 2.4.1
- Removida a exportação de clipes em GIF

## 2.4.0
- Removida a importação automática: as demos entram só quando você escolhe, pelo botão Adicionar demos

## 2.3.1
- Importação automática mais cuidadosa: espera 30 s sem mudanças no arquivo e ignora arquivos .bz2 na pasta do CS2 (o próprio jogo descompacta)

## 2.3.0
- Importação automática: o app vigia a pasta de replays do CS2 (e outras que você escolher) e adiciona cada demo nova sozinho, assim que o download termina
- Aviso na tela quando uma demo nova chega, com botão "Analisar agora"

## 2.2.0
- Nova aba Clipes: todos os clipes salvos (e as melhores jogadas) de todas as demos, com Ver no Replay, GIF, No CS2, renomear e apagar
- Visão do jogador: o CS2 agora é aberto pela Steam já com a demo; se o jogo já estiver aberto, o app avisa e copia o comando

## 2.1.0
- Replay com alternância entre Visão 2D e Visão do jogador: o app abre a demo no CS2 no lance escolhido, na tela do jogador (tecla F8)
- Clique num jogador no mapa 2D para segui-lo
- Clipes mais simples: botão ✂ em cada kill, "Criar clipe deste momento" com faixa na linha do tempo, botão Testar e cartões com Ver / GIF / No CS2
- Linha do tempo com as kills marcadas e botões de voltar/avançar 5 s
- Textos maiores em todo o app

## 2.0.0
- Nova aba Replay: assista a partida em 2D, visto de cima, com jogadores coloridos, direção da mira, vida e kills
- Melhores jogadas detectadas automaticamente (ACE, 4K, 3K, clutches e kills duplas rápidas)
- Clipes próprios: marque início e fim no replay e salve
- Clipes podem ser exportados como GIF ou abertos no CS2 no momento certo
- 5 bordas novas (Galáxia, Elétrico, Sakura, Tóxico e Diamante), efeitos animados (Girar, Pulsar, Faíscas) e 8 avatares

## 1.9.3
- O app agora se chama CS2 Analytics

## 1.9.2
- O app agora se chama CS Analytics

## 1.9.1
- Listas de opções com seta mais visível e visual mais limpo; minutos e dias viraram listas (sem botões de subir/descer)
- Lista de jogadores com faixa colorida: dourado para você, azul para aliados, vermelho para inimigos

## 1.9.0
- O app identifica seu time e o time inimigo, considerando a troca de lado
- Placar da Partida separado em Seu time e Time inimigo, com resumo de cada time
- Mostra quem mais te matou e quem você mais matou
- Jogadores marcados como aliado ou inimigo na lista e no topo
- Treinos com mapas da comunidade (Aim Botz, 5E AimHub, Recoil Master, Fast Aim, Aim_Rush, Yprac Hub) e botão para abrir cada um na Oficina

## 1.8.0
- Nova seção Minhas demos: toda demo adicionada fica salva no app
- Dois modos: analisar uma partida ou várias partidas juntas
- Excluir demos (vão para a lixeira), restaurar e apagar de vez
- Ao abrir, o app já mostra a partida mais recente

## 1.7.0
- Cada número mostra uma avaliação simples (Ótimo, Bom, Atenção, Precisa melhorar) e explica o que significa ao passar o mouse
- Cada ponto fraco mostra a prioridade e o treino que ajuda
- Botão "Gerar meu treino" no Resumo
- Botões com mais contraste e menu com ícones

## 1.6.1
- Corrige a leitura das demos atuais de Premier/Competitivo (rounds reconstruídos pelo placar)
- Placar de vitória/derrota calculado por time, considerando a troca de lado

## 1.6.0
- Neon do nome mais nítido, com brilho suave por trás das letras
- Escolha da cor do neon (8 cores prontas ou qualquer cor)
- Seleção de fontes em botões, com opção de escolher outra
- Bordas redesenhadas com enfeites: chamas, cristais de gelo, estrelas, rebites e brilho

## 1.5.0
- Modo administrador no perfil: libera todas as bordas
- Fonte do nome personalizável e estilos Neon e Neon arco-íris (animado)

## 1.4.1
- A janela do app abre no mesmo ícone fixado na barra de tarefas, sem criar um segundo ícone

## 1.4.0
- Instalador de atualizações dentro do app (com backup e opção de voltar à versão anterior)
- Perfil com foto, cor e bordas; algumas bordas são desbloqueadas pelo seu desempenho

## 1.3.0
- Ícone do app e script para criar atalho na área de trabalho

## 1.2.0
- Revisão de segurança: demos corrompidas/maliciosas, limites de tamanho, nomes escapados, dependências auditadas

## 1.1.0
- Interface minimalista com menu lateral, centrada no seu jogador

## 1.0.0
- Primeira versão: análise de demos, diagnóstico e plano de treino
