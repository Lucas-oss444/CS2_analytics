# Manual do CS2 Analytics

## Instalação

Requer Python 3.10+ (Windows, Linux ou macOS).

```
pip install -r requirements.txt
python main.py
```

Para gerar um `.exe` no Windows: `build_exe.bat` (o executável sai em `dist/CS2Analytics`).

Para criar o atalho: dê dois cliques em `criar_atalho.bat`. Ele coloca o CS2 Analytics no Menu Iniciar; de lá, clique com o botão direito e escolha **Fixar na barra de tarefas**. Ele usa o `.exe` se você já o gerou; senão, abre o app pelo Python sem janela de terminal. Se mover a pasta do app, rode de novo.

## Onde pegar as demos

- **Premier/Competitivo**: no CS2, *Assistir → Suas partidas → Baixar*. Os arquivos ficam em
  `Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\replays`.
- **FACEIT**: baixe a demo na página da partida (`.dem.zst` / `.dem.gz` são aceitos direto).

Abra uma ou várias demos pelo botão ou arrastando para a janela. Com várias, as estatísticas são somadas — o diagnóstico fica mais confiável com 3+ partidas.

## O que o app analisa

Na primeira demo o app pergunta qual jogador é você; depois ele sempre abre no seu jogador (marcado com ★). Para ver outro, use **Ver jogador** ou dê duplo clique em **Partida**; **← Voltar para mim** retorna. Cada seção mostra 4 números principais e um gráfico; o restante fica em **Mostrar detalhes**.

| Seção | Em destaque | Em "Mostrar detalhes" |
|---|---|---|
| Resumo | Rating, ADR, KAST, K/D, 3 focos principais, dano por round | Desempenho por lado (CT/TR), multi-kills |
| Treino | Treino de hoje e pontos a melhorar; minutos/dia, dias/semana, exportar plano, copiar config | Pontos fortes, semana completa, config de treino |
| Duelos | Aberturas, mortes tradadas, sobrevivência, clutches, comparação com o lobby | Trades, mortes cedo / sem dano / cego, clutches 1v1 e 1vX |
| Mira | HS%, tiros na cabeça, precisão geral e de rifle, onde os tiros acertam | Tabela por arma |
| Utilitárias | Flashes/round, inimigos cegos por flash, flashes no time, dano de granadas | Totais por granada |
| Evolução | Gráfico de qualquer métrica ao longo das partidas | Histórico de partidas |
| Partida | Placar de todos os jogadores | — |

Seu jogador e o histórico ficam salvos em `~/.cs2coach/`.

## Como o diagnóstico funciona

Cada regra em `cs2coach/coach.py` compara uma métrica com uma referência de "ok" e de "ruim" e calcula a prioridade (0–100%). Regras só disparam com amostra mínima (ex.: 8 mortes, 5 aberturas). Cada problema aponta para treinos específicos (Aim Botz, Recoil Master, prefire do mapa jogado, retakes, revisão de demo, lineups etc.), e o plano semanal distribui os treinos pelo peso dos problemas mais graves.

Para ajustar referências ou criar treinos, edite `RULES` e `DRILLS` em `coach.py`.

## Minhas demos

Toda demo adicionada fica salva em `~/.cs2coach/library` (só os dados da partida, alguns MB), mesmo que o CS2 apague o arquivo original. Em **Minhas demos**, marque as partidas e use **Analisar uma partida** ou **Analisar várias partidas** (sem nada marcado, ele oferece analisar todas). **Excluir selecionadas** manda para a **Lixeira**, onde dá para **Restaurar** ou **Excluir para sempre**. Demos excluídas saem da Evolução até serem restauradas.

## Replay e clipes

A aba **Replay** mostra a partida em 2D vista de cima: o formato do mapa é desenhado a partir das próprias posições dos jogadores, sem usar arquivos do jogo. Escolha a partida e o round, use **Play**, a velocidade e a barra de tempo; clicar numa kill da lista pula para o lance. As posições são lidas da demo original na primeira vez que você abre o replay de uma partida (precisa que o arquivo `.dem` ainda exista).

Em **Clipes**, ⭐ são as melhores jogadas detectadas pelo app (ACE, 4K, 3K, clutches 1v2+ e duas kills em até 3 s) e ✂ são os seus: pause no começo do lance, clique **✂ Início**, avance, clique **✂ Fim** e **💾 Salvar clipe**. Cada clipe pode ser visto no app ou aberto **No CS2**.

**Visão do jogador:** a visão em primeira pessoa só existe dentro do CS2. Em **👁 Visão do jogador** (ou **No CS2** num clipe), escolha o jogador e clique **Abrir no CS2**: o app cria `cs2analytics.cfg` na pasta `cfg` do CS2 e abre o jogo com a demo. Quando ela carregar, aperte **F8** para pular ao lance na tela do jogador. Se o CS2 já estiver aberto (ou abrir só no menu), cole `exec cs2analytics` no console — o comando já fica copiado.

A aba **🎞 Clipes** junta os clipes de todas as demos, com filtro para os seus clipes, as melhores jogadas ou todos. A tecla F8 fica ligada a esse atalho até você trocá-la nas configurações do jogo.

## Evolução e Social

- **Evolução:** além do gráfico por partida, mostra o desempenho por mapa (vitórias, rating, ADR, KAST, HS%) e compara a média das partidas antes e depois de uma partida que você escolher.
- **Treino:** metas da semana montadas a partir do diagnóstico, que marcam sozinhas quando você bate o alvo, e um checklist dos treinos do dia com a sua sequência de dias.
- **Social:** compare dois jogadores das partidas carregadas, gere um cartão da partida ou um cartão do perfil (avatar, arma favorita, carreira e qualidades) em PNG e acompanhe as conquistas.

## Perfil

Clique na sua foto no menu lateral para escolher foto, nome, cor e borda. As bordas Veterano (10 partidas analisadas), Ouro (rating 1.30+ numa partida) e Ace (um ACE numa partida) são desbloqueadas pelo seu histórico. Marque **Modo administrador** para liberar todas. Também dá para escolher a arma favorita (mostrada com um adesivo próprio do app), a fonte do nome e os estilos **Neon** (com cor à sua escolha) ou **Neon arco-íris** (animado). A foto é recortada, reduzida para 256 px e salva sem metadados em `~/.cs2coach/avatar.png`.

## Atualizações

1. Peça a melhoria ao Claude e **anexe o `cs2coach.zip` atual** na conversa (ou diga a versão, mostrada no rodapé do menu).
2. Baixe o novo `cs2coach.zip` que ele enviar.
3. No app: **v… · Atualizações → Escolher pacote → Instalar → Reiniciar**.

Antes de instalar, o app confere se o pacote é do CS2 Analytics, recusa caminhos perigosos, links e tipos de arquivo não permitidos (só `.py`, `.md`, `.txt`, `.png`, `.ico`, `.json` e os dois `.bat` do projeto), testa a sintaxe de todo o código e só então guarda um backup da versão atual e substitui os arquivos. Se algo der errado, **Voltar à versão anterior** restaura o backup (as 5 últimas versões ficam em `~/.cs2coach/backups`). Seu histórico, perfil e configurações nunca são tocados. Se a atualização trouxer bibliotecas novas, elas são instaladas automaticamente.

Instale apenas pacotes que o Claude enviou para você: uma atualização contém código que roda no seu PC. O "código de verificação" mostrado antes de instalar deve bater com o informado junto do pacote.

## Segurança

- **Conta Steam e VAC**: o app não pede login, não lê arquivos da Steam além das demos e não interage com o processo do CS2 (sem injeção, leitura de memória ou overlay). Ele só lê arquivos `.dem` já salvos, como um player de vídeo.
- **Sem internet**: nenhum código acessa a rede; os testes bloqueiam a rede e rodam o app inteiro.
- **Demos de terceiros**: o arquivo precisa ter o cabeçalho de demo do CS2; limite de 2 GB (também após descompactar); arquivos corrompidos ou maliciosos são recusados com aviso, sem travar o app; o temporário da descompactação é sempre apagado.
- **Conteúdo da demo**: nomes de jogadores, armas e mapa são limpos e escapados antes de aparecer na tela, então um nick com HTML não altera a interface.
- **Dados locais**: só ficam SteamIDs públicos, nomes e estatísticas em `~/.cs2coach/`. Consultas SQL são parametrizadas; banco ou config corrompidos são ignorados/recriados.
- **Dependências**: versões fixadas em `requirements.txt` e auditadas com `pip-audit`.
- **A config de treino** (`sv_cheats 1`) só funciona em partida privada/offline e não gera risco de VAC.

## Testes

Dê dois cliques em `rodar_testes.bat` ou rode `python -m pytest tests`. Os testes usam uma pasta temporária e nunca mexem nas suas demos, no perfil ou nas configurações.

- `test_engine.py`: cálculo das estatísticas, diagnóstico, plano de treino, dicas de pros e temas
- `test_robustness.py`: números extremos, partidas sem kills, histórico e biblioteca corrompidos, todas as bordas e avatares
- `test_ui_smoke.py`: abre todas as abas para vários jogadores, o replay, os clipes, os diálogos e o app em cada tema
- `test_progress.py`: desempenho por mapa, antes e depois, metas, checklist, conquistas, comparação com amigo e cartão
- `test_library.py`, `test_security.py`, `test_updater.py`: biblioteca de demos, arquivos maliciosos e instalador de atualizações
