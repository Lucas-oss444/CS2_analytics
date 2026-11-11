import math
import re
from dataclasses import dataclass

from .stats import METRICS

MAP_NAMES = {"de_mirage": "Mirage", "de_inferno": "Inferno", "de_dust2": "Dust II", "de_nuke": "Nuke",
             "de_ancient": "Ancient", "de_anubis": "Anubis", "de_vertigo": "Vertigo", "de_train": "Train",
             "de_overpass": "Overpass", "de_cache": "Cache", "de_office": "Office", "cs_italy": "Italy"}


WORKSHOP = "https://steamcommunity.com/sharedfiles/filedetails/?id={}"
SEARCH = "https://steamcommunity.com/workshop/browse/?appid=730&searchtext={}"

COMMUNITY_MAPS = {
    "aimbotz": ("Aim Botz - Aim Training", WORKSHOP.format(3070244462),
                "Bots parados ou andando, com distância, colete e velocidade ajustáveis. Ótimo para aquecer e para "
                "medir a evolução, porque o mesmo exercício pode ser repetido todo dia."),
    "aimhub": ("5E AimHub", SEARCH.format("5e_aimhub"),
               "Reúne flicks, tracking, reação e duelos contra bots em um só mapa. Bom para variar o treino sem "
               "trocar de servidor."),
    "recoil": ("Recoil Master - Spray Training", WORKSHOP.format(3100869952),
               "Desenha na parede o padrão de spray de cada arma. Você enxerga para onde as balas vão e aprende "
               "o movimento contrário do mouse."),
    "fastaim": ("Fast Aim / Reflex Training", WORKSHOP.format(3070758981),
                "Alvos surgem rápido em ângulos diferentes. Treina reagir com a mira já na altura certa, como num "
                "peek de verdade."),
    "aimrush": ("Aim_Rush", WORKSHOP.format(3105821815),
                "Vários bots atacam ao mesmo tempo. Simula retakes e trocas caóticas, onde é preciso escolher o "
                "alvo certo e trocar rápido."),
    "yprac": ("Yprac Hub", WORKSHOP.format(3070715607),
              "Rotas de prefire, posições comuns e granadas de cada mapa competitivo. É onde você treina o mapa "
              "em si, não só a mira."),
}


ESCORE = "https://escorenews.com/en/csgo/"
FALLEN_COURSE = "https://aimlabs.com/courses/7yqPu1LpF1g1Q0YYG1BKTf/lessons/2hLY2qIa2tUX5l0ttXFLfC"
COLD_TIPS = "https://www.elkjop.no/magazine/gaming-underholdning/coldzera-slik-blir-du-best-i-cs-go"


@dataclass
class ProTip:
    player: str
    text: str
    source: str
    url: str


PRO_TIPS = {
    "donk_dm": ProTip("donk", "No deathmatch, ele escolhe um ponto e segura a posição em vez de correr pelo mapa. Assim a mira só "
                      "faz ajustes curtos, como numa partida de verdade; correr em servidor cheio, segundo ele, só faz você "
                      "morrer o tempo todo.", "eScoreNews · vlog da Spirit na IEM Cologne 2026",
                      ESCORE + "news/78878-donk-explains-how-he-plays-deathmatch-to-practice"),
    "donk_real": ProTip("donk", "Para ele, uma partida contra pessoas ensina mais que uma hora de DM ou de bots: na partida você lê "
                        "o que está acontecendo e escolhe a posição, enquanto no DM os duelos são aleatórios.",
                        "eScoreNews · entrevista",
                        ESCORE + "article/53634-if-i-beat-someone-they-were-all-trolling-how-could-you-lose-to-a-schoolboy-"
                        "donk-on-his-childhood-in-siberia-first-events-and-training-routine"),
    "s1mple_mind": ProTip("s1mple", "Segundo ele, o que decide jogos de tiro é a cabeça: entender como o adversário pensa e toma "
                          "decisões, e ganhar dele assim, mais do que só na mira.", "eScoreNews · entrevista",
                          ESCORE + "article/45840-sometimes-i-m-curious-about-how-i-d-perform-in-an-international-team-"
                          "s1mple-about-key-to-success-in-fps-being-with-navi-till-the-end-and-his-ex"),
    "cold_review": ProTip("coldzera", "Mesmo no bootcamp, ele separa horas para treinar habilidades específicas, como a mira, e "
                          "revê as próprias partidas para achar os erros e trabalhar neles.", "Elkjøp · dicas do coldzera",
                          COLD_TIPS),
    "cold_team": ProTip("coldzera", "Ele lembra que no CS você não é melhor que o seu time: a posição de vocês juntos importa tanto "
                        "quanto a sua. Ouça os aliados e deixe o ego de fora.", "Elkjøp · dicas do coldzera", COLD_TIPS),
    "cold_flex": ProTip("coldzera", "O jogo muda a cada round: às vezes é preciso jogar passivo, às vezes explosivo. Para ele, essa "
                        "flexibilidade treinada é o que separa o nível profissional.", "Elkjøp · dicas do coldzera", COLD_TIPS),
    "fallen_aim": ProTip("FalleN", "No curso de mira, ele trata o movimento como parte da precisão e coloca dominar o recuo como "
                         "prioridade.", "Aim Lab · curso do FalleN", FALLEN_COURSE),
    "fallen_patience": ProTip("FalleN", "Nas aulas de posicionamento, ele fala em ter paciência para juntar informação e em resetar "
                              "a posição em vez de insistir no mesmo lugar.", "Aim Lab · curso do FalleN", FALLEN_COURSE),
    "fallen_util": ProTip("FalleN", "Ele ensina a usar granadas para controlar o mapa e no tempo certo para abrir espaço, começando "
                          "por lineups básicas de cada mapa.", "Aim Lab · curso do FalleN", FALLEN_COURSE),
    "fallen_comms": ProTip("FalleN", "Na comunicação, ele pede calls calmas e curtas, dizendo o que você vai fazer e para onde vai, "
                           "para o time conseguir te apoiar.", "Aim Lab · curso do FalleN", FALLEN_COURSE),
    "fallen_review": ProTip("FalleN", "Ao rever as próprias partidas, ele procura hábitos ruins, oportunidades perdidas e se a "
                            "jogada ajudou o time, e compara com o que os pros fazem.", "Aim Lab · curso do FalleN",
                            FALLEN_COURSE),
    "fallen_role": ProTip("FalleN", "Ele explica que cada função tem objetivos diferentes de TR e de CT; entender o seu papel em "
                          "cada lado é a base para jogar bem nele.", "Aim Lab · curso do FalleN", FALLEN_COURSE),
    "fer_aggro": ProTip("fer", "Quando passou a jogar agressivo de CT na Luminosity/SK, o ganho não era só a kill: ele trazia "
                        "informação lá da frente, e o time inteiro jogava melhor com isso.", "DRAFT5 · fer no Flow Podcast",
                        "https://draft5.gg/noticia/fer-relembra-problema-de-audicao-nos-tempos-de-sk-e-explica-como-mudou-o-"
                        "meta-do-csgo"),
    "fer_adv": ProTip("fer", "Comentando a FURIA, ele criticou sair do bomb para arriscar estando em vantagem, como 5x3 de CT; para "
                      "ele, isso vem de o time não conversar sobre qual é a melhor jogada.", "Dust2 Brasil · entrevista",
                      "https://www.dust2.com.br/noticias/54054/fer-diz-que-voltaria-ao-cs-com-oportunidade-bacana"),
    "fer_learn": ProTip("fer", "Ele diz que, para evoluir, é preciso ouvir o feedback e entrar com a cabeça de quem não sabe tudo, "
                        "aprendendo até com o mais novo do time.", "Dust2 Brasil · entrevista",
                        "https://www.dust2.com.br/noticias/64680/fer-diz-se-jogaria-por-outro-time-alem-da-furia-e-evita-"
                        "fechar-portas-no-cs"),
    "niko_goal": ProTip("NiKo", "Ele treina sempre com um objetivo definido: um dia só sprays no DM, outro só one-taps, além de "
                        "prefire no Refrag e de 500 a 1000 kills no Aim Botz.", "GGScore · vídeo de treino de mira",
                        "https://ggscore.com/en/csgo/news/60848"),
    "niko_dm": ProTip("NiKo", "Sempre que pode, ele encaixa um DM antes da partida; se não dá, vai de Aim Botz ou do mapa CS2 "
                      "Stats, onde consegue fazer os bots se mexerem.", "GGScore · podcast da ESL na IEM Cologne 2025",
                      "https://ggscore.com/en/csgo/news/70681"),
    "niko_intent": ProTip("NiKo", "Para ele, no nível mais alto o jogo é sobre minimizar erros e fazer tudo com intenção.",
                          "ProSettings · entrevista", "https://prosettings.net/blog/niko-cs2-interview-september-2025/"),
    "ropz_dm": ProTip("ropz", "Ele quase não joga FACEIT e mantém a forma principalmente no deathmatch; para ele, cuidar da "
                      "própria forma é responsabilidade do jogador.", "GGScore · podcast da ESL na IEM Cologne 2025",
                      "https://ggscore.com/en/csgo/news/70681"),
    "m0nesy_routine": ProTip("m0NESY", "Na época da NAVI Junior, ele aquecia 10–15 min em mapas como aim_botz e Fast Aim/Reflex e "
                             "depois passava cerca de 1h30 por dia assistindo demos.", "NAVI · entrevista",
                             "https://navi.gg/en/publications/5396-interview-with-m0nesy"),
    "m0nesy_balance": ProTip("m0NESY", "Ele fala em manter o equilíbrio na cabeça: não ficar confiante demais, mas usar o cérebro "
                             "para assustar e quebrar o adversário.", "eScoreNews · entrevista",
                             ESCORE + "news/57179-m0nesy-the-community-and-s1mple-had-set-expectations-too-high-expecting-"
                             "his-performance-to-be-great-in-first-match"),
    "zywoo_enjoy": ProTip("ZywOo", "Ele atribui o próprio nível a curtir o jogo com o time; segundo ele, quando não está se "
                          "divertindo, também não ganha.", "Hawk Live · IEM Rio 2026",
                          "https://hawk.live/posts/zywoo-revealed-the-secret-of-success-on-the-cs2-pro-scene"),
    "apex_donk": ProTip("apEX", "Analisando como parar o donk, ele disse que o rifler rende mais justamente quando os adversários "
                        "entram em duelos abertos com ele.", "esports.ru · apEX sobre o donk",
                        "https://esports.ru/counter-strike-2/news/apex-rasskazal-kak-protivostoyat-donk/"),
    "kscerato_focus": ProTip("KSCERATO", "Ele conta que o foco sempre foi melhorar no nível pessoal, sem pensar em ranking nem no futuro.",
                             "esports.gg · entrevista",
                             "https://esports.gg/br/news/cs-go-br/a-gente-vem-forte-esse-ano-kscerato-sobre-furia/"),
    "kscerato_team": ProTip("KSCERATO", "Sobre a FURIA, ele disse que perderam campeonatos que não podiam perder por falta de constância "
                            "e de tempo para o time evoluir junto.", "esports.gg · entrevista",
                            "https://esports.gg/br/news/cs-go-br/a-gente-vem-forte-esse-ano-kscerato-sobre-furia/"),
    "yuurih_change": ProTip("yuurih", "Às vezes você coloca na cabeça que precisa mudar tudo, quando na verdade não precisa.",
                            "Insider Gaming · BLAST Open Rotterdam 2026",
                            "https://insider-gaming.com/yuurih-blast-open-rotterdam-interview/"),
    "karrigan_self": ProTip("karrigan", "Ele admite que seu maior problema era a forma como falava consigo mesmo: aprendeu a separar "
                            "autocrítica útil de se julgar demais.", "eScoreNews · Major de Copenhague 2024",
                            ESCORE + "news/56951-karrigan-my-biggest-issue-about-four-years-ago-was-self-talk-i-think-my-wife-"
                            "fixed-that"),
    "karrigan_map": ProTip("karrigan", "Para ele, todo time precisa de um mapa de conforto, onde consegue vencer mesmo num dia ruim.",
                           "eScoreNews · Major de Xangai 2024",
                           ESCORE + "news/64345-karrigan-we-don-t-have-a-main-map-pick-at-shanghai-major-i-guess-we-have-"
                           "to-think-about-the-veto-constantly"),
    "device_health": ProTip("dev1ce", "Ele defende chegar preparado física e mentalmente antes de qualquer campeonato, como fazia a "
                            "Astralis.", "GuruGamer · OMEN Challenge",
                            "https://gurugamer.com/esports/dev1ce-shared-how-astralis-really-prepared-for-cs-go-6484/amp"),
    "cold_health": ProTip("coldzera", "Ele treina o corpo, se alimenta bem e cuida do lado mental para conseguir pensar com clareza "
                          "durante o jogo.", "Elkjøp · dicas do coldzera", COLD_TIPS),
    "magisk_psych": ProTip("Magisk", "Ele diz que é preciso treinar a mira e também aguentar o estresse da partida; como não tem a "
                           "mira de um s1mple ou NiKo, ganha vantagem no posicionamento e na parte mental.",
                           "eScoreNews · entrevista",
                           "https://escorenews.com/ru/csgo/news/22573-magisk-ob-ere-gambit-ya-hochu-uvidet-ih-v-toy-je-"
                           "forme-na-lan-zdes-ty-pod-davleniem-a-ne-doma-u-mamy"),
    "magisk_comms": ProTip("Magisk", "Analisando a BC.Game, ele disse que os jogadores têm muita habilidade individual, mas falta "
                           "comunicação eficiente no time.", "Hawk Live · entrevista à HLTV",
                           "https://hawk.live/posts/magisk-identifies-bcgames-main-problem"),
    "twistzz_stale": ProTip("Twistzz", "Ele conta que, na Liquid, depois do sucesso o time parou de testar coisas novas e estagnou.",
                            "AFK Gaming · entrevista",
                            "https://afkgaming.com/csgo/news/8379-twistzz-talks-about-his-time-on-team-liquid-and-reveals-"
                            "why-he-joined-faze-clan"),
    "sh1ro_stagnation": ProTip("sh1ro", "Ele saiu da Cloud9 porque sentia estagnação e queria evoluir e tentar algo novo.",
                               "GGScore · entrevista da Spirit",
                               "https://ggscore.com/en/csgo/news/54643-sh1ro-i-just-felt-stagnation-in-cloud9-so-i-had-a-"
                               "desire-to-improve-and-try-something-new"),
    "zywoo_improve": ProTip("ZywOo", "Ele diz que, a cada partida ruim, sente que ainda pode melhorar.", "eScoreNews · Pley.gg",
                            ESCORE + "news/37365-zywoo-every-time-i-play-every-time-i-have-a-shit-game-i-feel-that-i-can-still-"
                            "improve"),
    "zywoo_fresh": ProTip("ZywOo", "Antes de um torneio, a Vitality ficou uma semana sem treinar para voltar ao servidor com a cabeça "
                          "descansada.", "Hotspawn · BLAST Rivals Fort Worth 2026",
                          "https://www.hotspawn.com/counter-strike/news/zywoo-blast-rivals-fort-worth-2026-interview"),
    "s1mple_matches": ProTip("s1mple", "Para ele, sem jogar partidas você não evolui; foi o que sentiu ao passar meses parado, "
                             "sem jogos oficiais.", "Hawk Live · entrevista",
                             "https://hawk.live/posts/s1mple-honestly-responds-to-criticism-of-his-performance"),
    "m0nesy_discipline": ProTip("m0NESY", "Ele admite que gostaria de ter disciplina para seguir uma rotina fixa; o que consegue manter "
                                "é jogar FACEIT e DM antes de dormir.", "Hawk Live · live na Twitch",
                                "https://hawk.live/posts/m0nesy-offers-advice-young-cs2-players"),
}

RULE_PRO = {"adr": ("fer_aggro",), "hs_pct": ("donk_dm", "niko_goal"), "head_hit_pct": ("donk_dm", "niko_goal"),
            "rifle_accuracy": ("fallen_aim", "niko_goal"), "opening_success": ("s1mple_mind", "apex_donk"),
            "traded_death_pct": ("cold_team", "magisk_comms"), "trade_kill_pct": ("fallen_comms", "magisk_comms"),
            "early_death_pct": ("fallen_patience", "niko_intent", "magisk_psych"), "nodmg_death_pct": ("donk_real", "apex_donk"),
            "blind_death_pct": ("fallen_patience",), "kast": ("cold_flex", "kscerato_team"), "survival": ("fer_adv", "niko_intent", "magisk_psych"),
            "clutch_rate": ("s1mple_mind", "m0nesy_balance"), "flashes_pr": ("fallen_util",), "flash_eff": ("fallen_util",),
            "team_flash_pct": ("fallen_comms",), "util_dmg": ("fallen_util",), "adr_t": ("fallen_role", "karrigan_map"),
            "adr_ct": ("fallen_role", "karrigan_map")}

DRILL_PRO = {"warmup": ("donk_dm", "niko_dm", "ropz_dm"), "aimbotz_static": ("niko_goal",), "reflex": ("m0nesy_routine",),
             "duels": ("donk_real",), "demo_deaths": ("cold_review", "m0nesy_routine"), "demo_teamplay": ("fallen_review",),
             "lineups": ("fallen_util",), "play": ("fer_learn", "zywoo_enjoy", "s1mple_matches")}

CONSISTENCY = [
    ("Pouco todo dia vence muito de vez em quando",
     "O cérebro grava o movimento que você repete. 30–45 min quase todo dia rendem mais que 4 h no fim de semana.",
     ("m0nesy_discipline",)),
    ("Mesma rotina, mesmas configurações",
     "Aqueça sempre igual e não troque sensibilidade, mira ou resolução depois de uma partida ruim: assim dá para saber o que "
     "realmente melhorou.", ("yuurih_change",)),
    ("Descanso também é treino",
     "Os dias de folga do plano servem para fixar o que você treinou. Treinar cansado grava erro.", ("zywoo_fresh",)),
    ("Corpo e cabeça em dia",
     "Sono, comida e um pouco de exercício mudam o quanto você reage e decide bem. Jogar muito cansado, de madrugada, costuma piorar tudo isso.",
     ("cold_health", "device_health")),
    ("Fale consigo de forma justa",
     "Depois de uma partida ruim, anote 1 erro concreto para corrigir em vez de se xingar. Autocrítica útil aponta o que fazer.",
     ("karrigan_self",)),
    ("Partida ruim faz parte",
     "Até os melhores têm jogos ruins. O que pesa é a média de várias partidas; o app mostra isso em 📈 Evolução.",
     ("zywoo_improve",)),
    ("Foque na evolução, não no rank",
     "O rank acompanha a habilidade com atraso. Meça o progresso nas metas do app, uma de cada vez.", ("kscerato_focus",)),
    ("Tenha um mapa de conforto",
     "Jogar sempre o mesmo mapa principal deixa você confortável o bastante para render bem até nos dias ruins.", ("karrigan_map",)),
    ("Jogue partidas de verdade",
     "Treino isolado ajuda, mas é jogando contra pessoas que você aplica e testa o que treinou.", ("s1mple_matches", "donk_real")),
    ("Evite a estagnação",
     "Quando um ponto já estiver bom, troque o foco do treino para o próximo, em vez de repetir sempre o mesmo.", ("twistzz_stale", "sh1ro_stagnation")),
]


def num(js, key):
    try:
        v = float(js.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0
    return v if math.isfinite(v) else 0.0


def consistency(rows, last=10):
    ratings = [num(js, "rating") for *_, js in rows if num(js, "rounds") >= 10 and num(js, "rating") > 0][-last:]
    if len(ratings) < 3:
        return None
    mean = sum(ratings) / len(ratings)
    sd = (sum((r - mean) ** 2 for r in ratings) / len(ratings)) ** 0.5
    return {"n": len(ratings), "min": min(ratings), "max": max(ratings), "mean": mean, "sd": sd}


TEAMS = {
    "Spirit": ["donk", "sh1ro", "magixx", "zont1x", "tN1R"],
    "Vitality": ["ZywOo", "ropz", "flameZ", "mezii", "jL"],
    "FURIA": ["FalleN", "KSCERATO", "yuurih", "YEKINDAR", "molodoy"],
    "MOUZ": ["torzsi", "Spinx", "xertioN", "PR", "xelex"],
    "Falcons": ["NiKo", "m0NESY", "karrigan", "TeSeS", "kyousuke"],
    "Aurora": ["XANTARES", "woxic", "Jimpphat", "kyxsan", "Wicadia"],
    "Natus Vincere": ["Aleksib", "iM", "b1t", "w0nderful", "makazze"],
    "G2": ["huNter-", "NertZ", "r1nkle", "HeavyGod", "MATYS"],
    "FaZe": ["frozen", "Twistzz", "Neityu", "jcobbb", "JBOEN"],
    "The MongolZ": ["bLitz", "Techno", "910", "nin9", "cobrazera"],
    "BC.Game": ["s1mple", "Magisk", "Senzu", "mzinho", "asap"],
    "Virtus.pro": ["mir", "Patsi", "b1st", "AquaRS", "tO0RO"],
    "Nemiga": ["KaiR0N-", "Xant3r", "robo", "khaN", "syph0"],
    "Astralis": ["HooXi", "jabbi", "Staehr", "phzy", "ryu"],
    "Legacy": ["arT", "dumau", "latto", "n1ssim", "try"],
    "MIBR": ["insani", "venomzera", "LNZ", "nqz", "tomaszin"],
    "paiN": ["snow", "biguzera", "saffee", "Tatu", "Rkzinho"],
    "Imperial": ["VINI", "chelo", "decenty", "noway", "saadzin"],
    "Liquid": ["EliGE", "NAF", "malbsMd", "JT", "Jorko"],
    "NRG": ["nitr0", "Sonic", "hallzerk", "Grim", "Jeorge"],
    "Envy": ["Maka", "Lucky", "misutaaa", "Kursy", "Graviti"],
    "DENDELE": ["gafolo", "koala", "maxxkor", "rdnzao", "doc"],
    "FlyQuest": ["jks", "aliStair", "INS", "Vexite", "nettik"],
    "Lynn Vision": ["Westmelon", "z4KR", "Starry", "EmiliaQAQ", "C4LLM3SU3"],
    "TYLOO": ["JamYoung", "Mercury", "Moseyuh", "Zero", "zhokiNg"],
    "Chinggis Warriors": ["cool4st", "fury5k", "ROUX", "sk0R", "tikuak"],
    "Lendas do Brasil": ["FalleN", "coldzera", "fer", "fnx", "TACO", "felps", "boltz", "HEN1", "LUCAS1", "kNgV-", "steelega",
                         "zews", "cogu"],
    "Lendas": ["apEX", "dev1ce", "GeT_RiGhT", "f0rest", "olofmeister", "kennyS", "shox", "NEO", "TaZ", "pasha", "Snax",
               "GuardiaN", "Edward", "markeloff", "flusha", "JW", "KRIMZ", "dupreeh", "Xyp9x", "gla1ve", "Kjaerbye",
               "Stewie2K", "electroNic", "Boombl4", "HeatoN", "SpawN", "Potti"],
}
TEAMS_UPDATED = "elencos de nov/2026"

favorite = ""


def set_favorite(name):
    global favorite
    favorite = (name or "").lower()


def pro_tip(keys):
    tips = [PRO_TIPS[k] for k in keys or ()]
    return next((t for t in tips if t.player.lower() == favorite), tips[0] if tips else None)


def has_tips(name):
    return any(t.player.lower() == (name or "").lower() for t in PRO_TIPS.values())



@dataclass
class Drill:
    key: str
    name: str
    where: str
    how: str
    minutes: int
    workshop: str = ""


DRILLS = {d.key: d for d in [
    Drill("warmup", "Aquecimento em Deathmatch", "Deathmatch oficial ou servidor FFA da comunidade",
          "Só rifle. Nos primeiros 5 min, dê 1 tiro por vez e pare totalmente antes de cada um; depois jogue livre. "
          "Não conte kills: a ideia é chegar na partida com a mão acordada e o hábito de atirar parado ativo, "
          "que é o que mais cai quando a mão está fria.", 10),
    Drill("aimbotz_static", "Flicks de cabeça no Aim Botz", "Oficina: Aim Botz - Aim Training",
          "Bots parados: 100 kills só na cabeça, alternando curta, média e longa distância. Anote o tempo e tente "
          "bater o recorde a cada dia. Se errar mais de 1 em cada 4, desacelere: o cérebro grava o movimento que "
          "você repete, então precisão vem antes da velocidade.", 10, "aimbotz"),
    Drill("counter_strafe", "Counter-strafe + 1º tiro", "Oficina: Aim Botz (bots em movimento)",
          "Ande para o lado, aperte a tecla oposta para frear e dê 1 tiro. Com cl_showpos 1 no console, confira se "
          "a velocidade chegou a 0 no momento do tiro. No CS2, tiro em movimento espalha muito; é por isso que "
          "duelos parecem perdidos \"do nada\" quando você atira andando.", 10, "aimbotz"),
    Drill("aimhub_flicks", "Flicks e tracking no AimHub", "Oficina: 5E AimHub",
          "Faça o modo de flicks (alvo pequeno, só cabeça) e depois o de tracking em alvos que andam. "
          "Só aumente a velocidade quando acertar 80%. O flick ensina a chegar na cabeça; o tracking, a manter a "
          "mira nela quando o inimigo se mexe no meio do duelo.", 10, "aimhub"),
    Drill("aimhub_duels", "Duelos contra bots no AimHub", "Oficina: 5E AimHub",
          "No modo de duelo/reação, o bot aparece e atira de volta. Entre com counter-strafe e a mira já na altura "
          "da cabeça, para só precisar clicar. É a mesma situação da abertura de round: quem chega parado e "
          "com a mira no lugar atira primeiro.", 10, "aimhub"),
    Drill("recoil", "Controle de spray AK/M4", "Oficina: Recoil Master - Spray Training",
          "Siga o padrão da parede: 10 balas a 10 m, depois 15 balas num bot a 15 m. Alterne AK, M4A4 e M4A1-S "
          "e termine passando o spray de um bot para outro. O padrão de cada arma nunca muda, então é memória "
          "muscular pura: 10 min por dia rendem mais que 1 h no fim de semana.", 12, "recoil"),
    Drill("burst", "Tap e burst em longa distância", "Oficina: Aim Botz - Aim Training",
          "Bots a longa distância, rajadas de 2–3 balas com uma pausa curta entre elas para a mira voltar ao "
          "centro. Acima de ~20 m o spray espalha mais do que o corpo do inimigo; tap e burst ganham esses "
          "duelos e economizam o pente para o próximo.", 8, "aimbotz"),
    Drill("prefire", "Prefire e crosshair placement ({map})", "Oficina: Yprac Hub → Prefire → {map}",
          "Faça as rotas de prefire com a mira na altura da cabeça e colada nas quinas. Repita a mesma rota até "
          "zerar sem errar o primeiro tiro. Como é o seu mapa principal, você aprende de cabeça onde cada "
          "inimigo costuma estar, e o duelo vira só um clique.", 15, "yprac"),
    Drill("reflex", "Reação em peeks", "Oficina: Fast Aim / Reflex Training",
          "Alvos aparecem em ângulos diferentes; reaja movendo a mira só para o lado, sem subir nem descer. "
          "Se você precisa corrigir a altura, o tempo perdido não é de reação, é de mira mal posicionada; "
          "observe isso durante o treino.", 8, "fastaim"),
    Drill("aimrush", "Trocas rápidas no Aim_Rush", "Oficina: Aim_Rush",
          "Vários bots ao mesmo tempo: mate primeiro o mais perto ou o que já está mirando em você, recarregue só "
          "atrás de cobertura e se mexa entre os tiros. Simula retakes e executes, em que o dano vem de "
          "decidir rápido quem atacar, não só de mira.", 10, "aimrush"),
    Drill("duels", "Duelos 1v1", "Servidores 1v1 Arena / Aim duels da comunidade",
          "15 min de duelos contra pessoas reais. Varie o peek (curto, largo, jiggle) e nunca fique parado num "
          "ângulo aberto. Bots não blefam nem mudam de ritmo; pessoas sim, e é aí que você aprende a ler o "
          "adversário além de mirar.", 15),
    Drill("retake", "Retakes e clutches", "Servidores de Retake da comunidade",
          "Jogue retakes isolando duelos: limpe um ângulo por vez, use o som e conte o tempo da bomba "
          "(desarme leva 10 s, ou 5 s com kit). Num clutch, quem se apressa enfrenta dois de uma vez; quase sempre "
          "há mais tempo do que parece.", 20),
    Drill("lineups", "Lineups de utilitária ({map})", "Oficina: Yprac Hub → Utilitárias → {map}",
          "Aprenda 3 smokes e 2 molotovs de execução por bomb e 2 de defesa por lado. Repita cada uma 5x até sair "
          "igual sem olhar o guia. Uma smoke certa fecha um ângulo inteiro e uma molotov tira o inimigo do "
          "canto, sem você precisar vencer duelo nenhum.", 15, "yprac"),
    Drill("popflash", "Pop flashes", "Partida privada com a config de treino",
          "Treine 2 pop flashes por bomb que estouram logo ao passar a parede, sem dar tempo de o inimigo virar. "
          "Coloque um bot no ângulo e confira o tempo de cegueira: abaixo de 1 s ele ainda reage; acima de 2 s "
          "você entra no ângulo praticamente de graça.", 10),
    Drill("demo_deaths", "Revisão das próprias mortes", "Aba Replay deste app ou demo no CS2 (Shift+F2)",
          "Assista cada morte e pergunte: eu estava sozinho? A mira estava na altura certa? Eu precisava estar "
          "ali? Anote os 3 erros que mais se repetem. Errar é normal; repetir o mesmo erro toda partida é o "
          "que trava a evolução.", 15),
    Drill("demo_teamplay", "Revisão de spacing e trades", "Aba Replay deste app (visão 2D)",
          "Em cada morte, veja a que distância estava o aliado mais próximo. O ideal é estar a 1–2 s de "
          "alguém: se você cair, ele mata quem te matou e o round segue 4v4. Longe disso, sua morte é "
          "só um jogador a menos.", 15),
    Drill("antiflash", "Reação a flashes", "Partida privada com bots + flashes",
          "Ao ouvir o pino ou ver a granada, vire de costas ou saia do ângulo em vez de segurar cego. "
          "Depois volte por outra posição: quem jogou a flash vai entrar mirando no lugar onde você estava.", 8),
    Drill("side_study", "Estudo do lado mais fraco", "Demo pro / vídeos do mapa {map}",
          "Assista 5 rounds de um time profissional no seu lado mais fraco. Repare onde cada um começa o round, "
          "quando usa a utilitária e como rotaciona, e copie um setup ou uma execução para testar na próxima "
          "partida.", 15),
]}

PRACTICE_CFG = """sv_cheats 1
mp_warmup_end
mp_limitteams 0
mp_autoteambalance 0
mp_roundtime_defuse 60
mp_freezetime 0
mp_buy_anywhere 1
mp_maxmoney 60000
mp_startmoney 60000
sv_infinite_ammo 1
ammo_grenade_limit_total 5
sv_grenade_trajectory_prac_pipreview 1
sv_showimpacts 1
bot_kick
mp_restartgame 1"""

CONSOLE_CFG = "; ".join(PRACTICE_CFG.splitlines())

COMMANDS = {
    "cfg": ("Config de treino", CONSOLE_CFG,
            "Liga cheats, munição infinita, compra em qualquer lugar, dinheiro máximo, rastro das granadas e marca dos tiros."),
    "showpos": ("Mostrar velocidade", "cl_showpos 1",
                "Mostra sua velocidade no canto da tela: no counter-strafe ela precisa chegar a 0 na hora do tiro."),
    "rethrow": ("Repetir última granada", "sv_rethrow_last_grenade",
                "Joga de novo a última granada do mesmo ponto, para você ver onde ela cai sem precisar repetir o movimento."),
    "noclip": ("Voar pelo mapa", "noclip", "Atravessa paredes e voa, para ir rápido até o ponto da lineup. Use de novo para desligar."),
    "bot": ("Colocar bot onde você mira", "bot_add; bot_stop 1; bot_place",
            "Adiciona um bot parado no ponto que você está mirando, para testar flashes e ângulos."),
    "demoui": ("Mostrar/esconder controle da demo", "demoui", "Abre ou fecha a barra de controle da demo, o mesmo que o atalho Shift+F2. Feche antes de gravar a tela."),
}

DRILL_CMD = {"counter_strafe": ("showpos",), "popflash": ("cfg", "bot", "rethrow"), "lineups": ("cfg", "rethrow", "noclip"),
             "antiflash": ("cfg", "bot"), "demo_deaths": ("demoui",)}


@dataclass
class Rule:
    metric: str
    area: str
    ok: float
    bad: float
    title: str
    why: str
    tip: str
    drills: tuple
    sample: str = "rounds"
    min_sample: int = 10


RULES = [
    Rule("adr", "Impacto", 75, 55, "Dano baixo por round",
         "Você causa {value} de dano por round; um jogador sólido fica perto de 75. Dano baixo quase sempre "
         "significa duelos perdidos no primeiro tiro ou rounds em que você nem chegou a trocar tiro.",
         "Mesmo sem matar, deixe dano: um inimigo com 30 de vida cai com um tiro de qualquer aliado. Em "
         "retakes, entre junto com o time em vez de chegar por último. No Resumo, os rounds com dano zero no "
         "gráfico mostram onde você sumiu.", ("aimbotz_static", "aimrush", "duels")),
    Rule("hs_pct", "Mira", 0.45, 0.28, "Poucas kills na cabeça",
         "{value} das suas kills são na cabeça (referência ~45%). Com rifle, um tiro na cabeça mata; no corpo "
         "são 3 ou 4. Poucas HS indicam mira entrando baixa no duelo, o que te dá menos tempo para reagir.",
         "Ande com a mira na altura da cabeça de quem estaria na próxima quina, nunca apontada para o chão. "
         "Em subidas e escadas, ajuste a altura antes de chegar. Assim o duelo vira um ajuste curto para o lado, "
         "em vez de um flick para cima.", ("prefire", "aimhub_flicks", "aimbotz_static"),
         "kills", 8),
    Rule("head_hit_pct", "Mira", 0.22, 0.12, "Mira fora da altura da cabeça",
         "Só {value} dos seus acertos pegam na cabeça (referência ~22%). Ou seja: você até acerta, mas no peito "
         "ou nas pernas, e precisa de mais balas, dando tempo para o inimigo responder.",
         "Antes de cada peek, deixe a mira onde a cabeça vai aparecer; o movimento no duelo deve ser só para o "
         "lado. Se perceber que corrige para cima, a mira estava baixa. Para conferir, abra uma morte em "
         "👁 No CS2 e veja onde a mira estava antes do inimigo aparecer.", ("prefire", "aimbotz_static"), "hits", 30),
    Rule("rifle_accuracy", "Mira", 0.20, 0.12, "Spray e precisão de rifle",
         "Seus tiros de rifle acertam {value} das vezes (referência ~20%). As causas mais comuns são atirar "
         "andando, que no CS2 espalha muito, ou segurar o spray de longe sem controlar o recuo.",
         "Pare antes de atirar (counter-strafe). De perto, spray controlado; de média ou longa distância, "
         "rajadas de 2–3 balas. Se você erra mais o primeiro tiro, o problema é parar; se erra do 4º em diante, "
         "é o controle do spray.", ("recoil", "counter_strafe", "burst"), "rifle_shots", 80),
    Rule("opening_success", "Duelos", 0.50, 0.35, "Perde os duelos de abertura",
         "Você venceu {value} dos primeiros duelos dos rounds. Quem perde a abertura deixa o time em 4v5, e a "
         "chance de ganhar o round cai para cerca de um terço. Perder muitas é o erro que mais custa rounds.",
         "Se você não é o entry, deixe outro abrir e fique pronto para o trade. Se é, nunca dê peek seco: "
         "entre com flash ou com um aliado logo atrás. A abertura vale mais que qualquer outra kill do round, "
         "então vale gastar uma granada nela.", ("prefire", "aimhub_duels", "reflex", "duels"),
         "opening_attempts", 5),
    Rule("traded_death_pct", "Trabalho em equipe", 0.25, 0.10, "Morre isolado (sem trade)",
         "Só {value} das suas mortes foram vingadas por um aliado em até 5 s. Morte vingada vira troca 1 por 1; "
         "morte isolada é só um jogador perdido. Isso indica que você está jogando longe do time.",
         "Antes de dar peek, olhe o radar: se nenhum aliado está perto o bastante para punir quem te matar, "
         "espere ou mude de posição. A regra prática é ter alguém a no máximo 1–2 s de você, vendo o mesmo "
         "ângulo.", ("demo_teamplay", "demo_deaths"), "deaths", 8),
    Rule("trade_kill_pct", "Trabalho em equipe", 0.18, 0.06, "Pouco trade dos aliados",
         "Só {value} das suas kills vingam um aliado que acabou de morrer. Quando o entry cai e ninguém responde, "
         "o time perde um jogador sem troca. Ou você está longe de quem entra, ou demora para reagir.",
         "Ande 1–2 s atrás de quem vai entrar e, quando ele morrer, dê o peek na hora: o inimigo ainda está "
         "virando a mira ou recarregando. Combinar no voice quem entra primeiro deixa o segundo já pronto.", ("demo_teamplay",), "kills", 8),
    Rule("early_death_pct", "Posicionamento", 0.25, 0.45, "Morre muito cedo nos rounds",
         "{value} das suas mortes acontecem nos primeiros 30 s, antes de o time ter informação ou usar "
         "utilitária. Costumam ser peeks secos ou posições que o inimigo já conhece e espera.",
         "Varie a posição inicial entre os rounds e só dispute ângulos com flash ou com apoio. Aos 30 s ainda "
         "sobra 1:25 de round, então não há pressa. Morrer no início tira você do round inteiro; a mesma morte "
         "no fim, depois de passar informação, ainda ajudou.", ("demo_deaths", "prefire"), "deaths", 8),
    Rule("nodmg_death_pct", "Duelos", 0.35, 0.55, "Morre sem causar dano",
         "Em {value} das suas mortes você não deu nenhum dano. Ou foi pego desprevenido (por trás, rotação, "
         "lurk), ou o primeiro tiro saiu em movimento ou fora da cabeça.",
         "Confira essas mortes no Replay: se o inimigo veio de onde você não olhava, é posicionamento; "
         "se você atirou primeiro e errou, é mira. Saber qual é o seu caso muda o treino: posição se corrige "
         "revendo demos, mira se corrige no Aim Botz.", ("counter_strafe", "aimhub_duels", "reflex", "demo_deaths"),
         "deaths", 8),
    Rule("blind_death_pct", "Utilitária", 0.12, 0.25, "Morre cego",
         "{value} das suas mortes foram com você cego. O inimigo joga a flash justamente para entrar no seu "
         "ângulo, e quem fica no mesmo lugar vira alvo fácil.",
         "Ao ouvir a flash, vire de costas ou saia da linha de visão; depois volte por outro ângulo ou recue "
         "para perto do time. Quem jogou a flash vai entrar mirando exatamente onde você estava.", ("antiflash",), "deaths", 8),
    Rule("kast", "Consistência", 0.70, 0.58, "Muitos rounds sem contribuição",
         "Seu KAST é {value} (referência ~70%): em muitos rounds você não matou, não deu assistência, não "
         "sobreviveu e não foi vingado. Nesses rounds o time jogou, na prática, com quatro.",
         "Quando a kill não sair, contribua de outro jeito: uma flash para o entry, informação no rádio ou "
         "ficar vivo para salvar a arma. KAST alto é o que torna um jogador confiável, mesmo com poucas kills.", ("demo_deaths", "lineups")),
    Rule("survival", "Posicionamento", 0.32, 0.20, "Sobrevive pouco",
         "Você termina vivo só {value} dos rounds. Cada morte custa a arma (US$ 2.700–3.100 num rifle) e pesa na "
         "economia do time; parte delas vem de duelos que nem precisavam ser jogados.",
         "Com o round perdido (ex.: 1v3 com pouco tempo), guarde a arma em vez de buscar uma kill improvável. "
         "Um rifle salvo pode ser o que deixa o time comprar completo no round seguinte.",
         ("demo_deaths", "retake")),
    Rule("clutch_rate", "Clutch", 0.20, 0.05, "Clutches",
         "Você venceu {value} das vezes em que ficou sozinho contra um ou mais inimigos. Clutch depende mais de "
         "calma, som e tempo do que de mira, e perder a maioria é normal.",
         "Isole os duelos: lute contra um inimigo por vez e use o barulho deles (passos, desarme) para escolher "
         "a hora de aparecer. Olhe o tempo antes de agir: com a bomba plantada, quem precisa vir até você são os CTs.", ("retake",), "clutch_att", 3),
    Rule("flashes_pr", "Utilitária", 0.45, 0.20, "Usa poucas flashes",
         "Você joga em média {value} flashes por round. Uma flash custa US$ 200 e transforma um duelo 50/50 num "
         "duelo em que o inimigo nem enxerga você.",
         "Compre ao menos uma flash por round com arma completa e use antes de entrar num bomb ou de disputar "
         "um ângulo. Mesmo sem lineup, uma flash por cima da quina antes do peek já ajuda.", ("popflash", "lineups")),
    Rule("flash_eff", "Utilitária", 0.6, 0.25, "Flashes pouco efetivas",
         "Cada flash sua cega em média {value} inimigos. Flash que estoura tarde, atrás da parede ou à vista "
         "do inimigo dá tempo de ele virar o rosto.",
         "Prefira flashes que estouram logo ao passar a quina ou por cima do inimigo. Jogue e entre na hora, "
         "não 2 segundos depois. Teste numa partida privada com um bot: se ele fica cego menos de 1 s, a flash "
         "estourou tarde.", ("popflash",), "flash_thrown", 6),
    Rule("team_flash_pct", "Utilitária", 0.25, 0.45, "Cega muito o próprio time",
         "{value} das pessoas que suas flashes cegam são aliados. Isso tira o seu time do duelo bem na hora em "
         "que ele mais precisa enxergar.",
         "Avise no voice (\"flash saindo\") antes de jogar e prefira flashes que estouram no alto, longe da "
         "linha de visão do time. Combinar quem flasha e quem entra evita que os dois se ceguem.", ("popflash", "lineups"), "blinded_total", 6),
    Rule("util_dmg", "Utilitária", 6, 2, "Pouco dano de granadas",
         "Suas HE e molotovs causam em média {value} de dano por round. Granada em lugar que o inimigo sempre "
         "usa tira vida ou o expulsa da posição sem você se expor.",
         "Use a molotov para limpar cantos antes de entrar e guarde a HE para inimigos agrupados ou já "
         "machucados. Comece por uma molotov de execução por bomb no seu mapa principal.", ("lineups",)),
]

SAMPLE_NAMES = {"rounds": "rounds", "kills": "kills", "hits": "acertos", "rifle_shots": "tiros de rifle",
                "opening_attempts": "duelos de abertura", "deaths": "mortes", "clutch_att": "clutches",
                "flash_thrown": "flashes", "blinded_total": "jogadores cegados"}


@dataclass
class Issue:
    rule: Rule
    value: float
    severity: float
    lobby: float | None
    count: int = 0

    @property
    def text(self):
        fmt = METRICS[self.rule.metric][1]
        return self.rule.why.format(value=fmt.format(self.value))

    @property
    def pro(self):
        return pro_tip(RULE_PRO.get(self.rule.metric))

    @property
    def higher_better(self):
        return self.rule.ok > self.rule.bad

    @property
    def compare(self):
        if self.lobby is None or not self.rule.ok:
            return ""
        fmt = METRICS[self.rule.metric][1]
        worse = self.value < self.lobby if self.higher_better else self.value > self.lobby
        if worse:
            return (f"Você também ficou pior que a média deste lobby ({fmt.format(self.lobby)}), então não é só o nível "
                    "das partidas: é um ponto seu.")
        return (f"Mesmo assim você ficou igual ou melhor que a média do lobby ({fmt.format(self.lobby)}): as partidas "
                "estavam difíceis nisso, mas ainda vale treinar para chegar à referência.")

    @property
    def goal(self):
        if not self.rule.ok:
            return ""
        fmt = METRICS[self.rule.metric][1]
        return (f"Meta para as próximas partidas: {fmt.format(self.value + (self.rule.ok - self.value) / 2)} "
                f"(metade do caminho até a referência de {fmt.format(self.rule.ok)}).")

    @property
    def context(self):
        fmt = METRICS[self.rule.metric][1]
        parts = [f"Você: {fmt.format(self.value)}"]
        if self.rule.ok:
            parts.append(f"referência: {fmt.format(self.rule.ok)}")
        if self.lobby is not None:
            parts.append(f"lobby: {fmt.format(self.lobby)}")
        if self.count:
            parts.append(f"base: {self.count} {SAMPLE_NAMES.get(self.rule.sample, self.rule.sample)}")
        return " · ".join(parts)


def _severity_raw(rule, value):
    return (rule.ok - value) / (rule.ok - rule.bad)


def _severity(rule, value):
    return max(0.0, min(1.0, _severity_raw(rule, value)))


def diagnose(p, lobby=None):
    lobby = lobby or {}
    issues, strengths = [], []
    for rule in RULES:
        if p.get(rule.sample, 0) < rule.min_sample:
            continue
        v = p[rule.metric]
        sev = _severity(rule, v)
        if sev > 0:
            issues.append(Issue(rule, v, sev, lobby.get(rule.metric), int(p.get(rule.sample, 0))))
        elif -_severity_raw(rule, v) >= 0.5:
            strengths.append((METRICS[rule.metric][0], METRICS[rule.metric][1].format(v)))
    if p.get("rounds_ct", 0) >= 8 and p.get("rounds_t", 0) >= 8:
        gap = p["adr_ct"] - p["adr_t"]
        if abs(gap) >= 25 and min(p["adr_ct"], p["adr_t"]) < 75:
            weak = "TR" if gap > 0 else "CT"
            rule = Rule("adr_t" if weak == "TR" else "adr_ct", "Lados", 0, 0, f"Lado {weak} bem mais fraco",
                        f"Seu dano por round é {p['adr_ct']:.0f} de CT e {p['adr_t']:.0f} de TR. Uma diferença tão grande "
                        f"costuma indicar que, no lado {weak}, você ainda não tem um plano claro: onde começar, quando "
                        "agir e qual utilitária usar.",
                        "Escolha um papel fixo nesse lado (uma posição de CT ou uma função no ataque de TR) e repita por "
                        "algumas partidas até ficar natural.", ("side_study", "lineups"))
            issues.append(Issue(rule, min(p["adr_ct"], p["adr_t"]), min(1.0, abs(gap) / 50), None))
    issues.sort(key=lambda i: -i.severity)
    return issues, strengths


def drill_text(key, map_name):
    d = DRILLS[key]
    m = MAP_NAMES.get(map_name, map_name)
    return Drill(d.key, d.name.format(map=m), d.where.format(map=m), d.how.format(map=m), d.minutes, d.workshop)


WEEK = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
MINUTES = (20, 30, 45, 60, 75, 90, 120, 150, 180)


def training_days(days):
    return {round(i * 7 / days) for i in range(days)}


def suggest_schedule(issues, rounds):
    load = sum(i.severity for i in issues[:6])
    high = [i for i in issues if i.severity >= 0.66]
    minutes = 30 if load < 0.6 else 45 if load < 1.4 else 60 if load < 2.4 else 75 if load < 3.4 else 90
    days = 3 if load < 0.6 else 4 if load < 1.4 else 5 if load < 3 else 6
    if rounds < 15:
        minutes, days = min(minutes, 45), min(days, 4)
    if not issues:
        why = "Nenhum número ficou abaixo da referência, então o treino é de manutenção: aquecer e manter o mapa em dia."
    else:
        names = ", ".join(i.rule.title.lower() for i in high[:2])
        n, rest = len(issues), 7 - days
        why = (f"Você tem {n} {'ponto' if n == 1 else 'pontos'} a melhorar"
               + (f", {len(high)} de prioridade alta ({names})" if high else "")
               + f". {minutes} min dão tempo para o aquecimento e para "
               + ("um treino focado" if minutes < 45 else "dois ou três treinos focados")
               + f"; {rest} {'dia' if rest == 1 else 'dias'} de descanso ajudam a fixar o movimento e evitam treinar "
               "cansado, que grava erro.")
    if rounds < 15:
        why += " Como há poucos rounds analisados, a sugestão é mais leve até o diagnóstico ficar confiável."
    return minutes, days, why


def weekly_plan(issues, map_name, minutes_per_day=60, days=7):
    weight = {}
    for issue in issues[:5]:
        for rank, key in enumerate(issue.rule.drills):
            weight[key] = weight.get(key, 0) + issue.severity / (rank + 1)
    pool = sorted(weight, key=lambda k: -weight[k]) or ["aimbotz_static", "aimhub_flicks", "prefire", "lineups"]
    active = training_days(days)
    plan = []
    for day_idx, day in enumerate(WEEK):
        if day_idx not in active:
            plan.append((day, []))
            continue
        items = [drill_text("warmup", map_name)]
        left = minutes_per_day - items[0].minutes
        rest = pool[1:]
        shift = day_idx % len(rest) if rest else 0
        for key in [pool[0]] + rest[shift:] + rest[:shift]:
            d = drill_text(key, map_name)
            if d.minutes <= left:
                items.append(d)
                left -= d.minutes
        if left >= 10:
            items.append(Drill("play", "Partida competitiva/Premier", "CS2",
                               "Use na partida o que treinou hoje. Escolha só 1 ponto do diagnóstico para prestar atenção "
                               "e depois confira no app se ele melhorou; tentar corrigir tudo de uma vez divide o foco e "
                               "nada muda.", left))
        plan.append((day, items))
    return plan


def plan_markdown(player, issues, strengths, plan):
    player = player.replace("<", "").replace(">", "")
    out = [f"# Plano de treino — {player}", "", "## Diagnóstico"]
    for i in issues:
        out.append(f"- **{i.rule.title}** ({i.rule.area}, prioridade {i.severity:.0%}): {i.text} {i.compare} "
                   f"Dica: {i.rule.tip} {i.goal}" + f" _({i.context})_")
        if i.pro:
            out.append(f"  - 🏆 {i.pro.player}: {i.pro.text} [{i.pro.source}]({i.pro.url})")
    if strengths:
        out += ["", "## Pontos fortes"] + [f"- {n}: {v}" for n, v in strengths]
    for day, items in plan:
        out += ["", f"## {day}"] + ([] if items else ["- Descanso"])
        out += [f"- {d.minutes} min — **{d.name}** ({d.where}): {d.how}"
                + (f" [Abrir na Oficina]({COMMUNITY_MAPS[d.workshop][1]})" if d.workshop in COMMUNITY_MAPS else "")
                for d in items]
    out += ["", "_As dicas de pros são resumos em nossas palavras do que cada jogador disse nas fontes indicadas._"]
    out += ["", "## Mapas da comunidade"] + [f"- [{n}]({u}): {t}" for n, u, t in COMMUNITY_MAPS.values()]
    out += ["", "## Comandos para o console (só em partida privada)"]
    out += [f"- **{n}**: `{c}` — {e}" for n, c, e in COMMANDS.values()]
    return "\n".join(out)


HELP = {
    "rating": "Nota geral da partida, juntando kills, mortes, dano e sobrevivência. 1.00 é a média do jogo; acima "
              "disso você ajudou o time mais do que um jogador comum. Abaixo de 0.85 vale revisar as mortes.",
    "adr": "Dano médio por round, contando também o dano que não virou kill. Perto de 75 é bom e acima de 90 é de "
           "quem carrega. É o número que melhor mostra impacto, mesmo quando as kills não saem.",
    "kpr": "Kills por round, em média. Perto de 0.70 é bom; 1 kill a cada 2 rounds já é o mínimo esperado de um rifler.",
    "dpr": "Mortes por round, em média. Quanto menor, melhor: perto de 0.65 é bom. Cada morte deixa o time com um a "
           "menos e custa a arma.",
    "kd": "Kills divididas por mortes. Acima de 1.00 você mata mais do que morre. Use junto com o ADR: um K/D alto "
          "com dano baixo pode vir de kills fáceis no fim do round.",
    "kast": "Porcentagem de rounds em que você ajudou de algum jeito: matou, deu assistência, sobreviveu ou foi "
            "vingado. Perto de 70% é bom; abaixo de 60% você some em muitos rounds.",
    "hs_pct": "Parte das suas kills que foi na cabeça. Perto de 45% é bom com rifle. Mais HS significa mira na altura "
              "certa e duelos que acabam antes de o inimigo reagir.",
    "accuracy": "Parte dos seus tiros, com qualquer arma, que acertou um inimigo. Sprays longos e tiros de "
                "pressão através de smoke derrubam esse número.",
    "rifle_accuracy": "Precisão só com rifles (AK, M4, FAMAS, Galil, AUG, SG). Perto de 20% é bom. Mostra se você para "
                      "antes de atirar e se controla o spray.",
    "head_hit_pct": "Dos tiros que acertaram, quantos foram na cabeça. Perto de 22% é bom. Mostra se a mira já está "
                    "na altura certa antes de o duelo começar.",
    "opening_success": "Quando você participa do primeiro duelo do round, quantas vezes vence. Ganhar a abertura "
                       "deixa o time em 5v4 e aumenta muito a chance de levar o round.",
    "opening_rate": "Em quantos rounds você participa do primeiro duelo. Alto é normal para entry e AWP; para suporte, "
                    "alto demais pode indicar peeks desnecessários.",
    "trade_kill_pct": "Parte das suas kills que vingou um aliado morto há poucos segundos. Mostra se você joga perto do "
                      "time e reage rápido quando o entry cai.",
    "traded_death_pct": "Quando você morreu, quantas vezes um aliado matou quem te matou em até 5 s. Morte vingada vira "
                        "troca 1 por 1, e o round segue equilibrado.",
    "early_death_pct": "Parte das suas mortes nos primeiros 30 s do round, quando o time ainda não tem informação. Acima "
                       "de 30% costuma indicar peeks secos ou posição previsível.",
    "nodmg_death_pct": "Parte das suas mortes em que você não deu nenhum dano. Normalmente é inimigo vindo de onde você "
                       "não olhava ou primeiro tiro errado.",
    "blind_death_pct": "Parte das suas mortes em que você estava cego por flash. Acima de 15% mostra que você costuma "
                       "segurar o ângulo depois da flash, em vez de sair.",
    "survival": "Rounds em que você terminou vivo. Perto de 30% é normal. Sobreviver salva a arma e o dinheiro do "
                "próximo round.",
    "clutch_rate": "Quando ficou sozinho contra um ou mais inimigos, quantas vezes venceu. Mesmo bons jogadores ficam "
                   "perto de 20%, então use só com várias partidas somadas.",
    "multikill_rate": "Rounds em que você fez 2 kills ou mais. São esses rounds que viram partidas, porque abrem "
                      "vantagem numérica grande.",
    "util_dmg": "Dano médio por round com HE e molotov. Perto de 6 é bom; mostra se suas granadas acertam lugares que o "
                "inimigo realmente usa.",
    "flashes_pr": "Flashes que você joga por round, em média. Perto de 0.5 é saudável; muito abaixo disso você disputa "
                  "duelos sem ajuda.",
    "flash_eff": "Inimigos cegos por cada flash sua, em média. Acima de 0.6 suas flashes estão ajudando de verdade; "
                 "abaixo de 0.3 elas estouram tarde ou no lugar errado.",
    "avg_blind": "Tempo médio que cada inimigo fica cego com a sua flash. Abaixo de 1 s ele ainda reage; acima de 2 s "
                 "dá para entrar no ângulo com vantagem.",
    "team_flash_pct": "Das pessoas que você cegou, quantas eram do seu time. Quanto menor, melhor; acima de 30% suas "
                      "flashes atrapalham mais do que ajudam.",
    "smokes_pr": "Smokes que você joga por round. A smoke bloqueia a visão por cerca de 20 s e ajuda a entrar num bomb "
                 "ou atrasar o inimigo.",
    "adr_ct": "Dano médio por round jogando de CT, o lado que defende os bombs. Comparar com o TR mostra em qual lado "
              "você está mais confortável.",
    "adr_t": "Dano médio por round jogando de TR, o lado que ataca e planta a bomba. Comparar com o CT mostra em qual "
             "lado você está mais confortável.",
    "kast_ct": "KAST jogando de CT: em quantos rounds de defesa você contribuiu de algum jeito.",
    "kast_t": "KAST jogando de TR: em quantos rounds de ataque você contribuiu de algum jeito.",
}

GLOSSARY = [
    (("deathmatch", "dm"), "Deathmatch (DM)",
     "Modo em que você renasce na hora e enfrenta todo mundo, sem rounds nem objetivo. Serve para aquecer e treinar mira em "
     "duelos de verdade; o placar não importa."),
    (("pop flash",), "Pop flash",
     "Flash que estoura logo depois de passar a parede ou a quina, quase sem dar tempo de o inimigo virar o rosto. É a que mais cega."),
    (("lineup",), "Lineup",
     "Jeito fixo de jogar uma granada: você para num ponto exato, mira numa marca do mapa e joga sempre igual, para ela cair "
     "no mesmo lugar toda vez."),
    (("prefire",), "Prefire",
     "Atirar no lugar onde o inimigo costuma ficar no instante em que você abre o ângulo, antes mesmo de enxergá-lo."),
    (("counter-strafe",), "Counter-strafe",
     "Apertar a tecla do lado oposto ao que você anda (A ↔ D) para parar na hora. No CS2 só o tiro dado parado sai preciso."),
    (("crosshair placement", "altura da cabeça"), "Crosshair placement",
     "Manter a mira na altura da cabeça e onde o inimigo vai aparecer, para o duelo virar só um ajuste pequeno do mouse."),
    (("spray",), "Spray",
     "Atirar segurando o botão. Cada arma tem um padrão de recuo fixo, que dá para decorar e compensar puxando o mouse."),
    (("tap", "burst", "rajada"), "Tap e burst",
     "Tap é um tiro por vez; burst é uma rajada curta de 2–3 balas com uma pausa para a mira voltar ao centro."),
    (("flick",), "Flick", "Movimento rápido do mouse para levar a mira até um alvo que apareceu."),
    (("tracking",), "Tracking", "Manter a mira em cima de um alvo que está se movendo."),
    (("trade",), "Trade",
     "Matar quem acabou de matar seu aliado, em poucos segundos. A troca deixa o round equilibrado em vez de você ficar com um a menos."),
    (("entry", "abertura"), "Entry e abertura",
     "O primeiro duelo do round. Entry é o jogador que entra primeiro no bomb para abrir espaço para o time."),
    (("clutch",), "Clutch", "Quando você fica sozinho contra um ou mais inimigos e precisa ganhar o round."),
    (("retake",), "Retake", "Quando os CTs voltam ao bomb para tirar os TRs depois que a bomba foi plantada."),
    (("peek",), "Peek",
     "Sair de trás de uma cobertura para olhar ou atirar num ângulo. Jiggle peek é aparecer e sumir rápido só para ver ou puxar um tiro."),
    (("utilitária", "smoke", "molotov", "he"), "Utilitária",
     "As granadas: smoke (bloqueia a visão), flash (cega), molotov/incendiária (queima uma área) e HE (explode e tira vida)."),
    (("oficina", "aim botz", "aimhub", "yprac", "aim_rush", "recoil master", "fast aim"), "Mapas da Oficina",
     "Mapas de treino feitos pela comunidade (Oficina Steam). Rodam offline: você se inscreve e abre em Jogar → Mapas da Oficina, "
     "sem afetar seu rank."),
    (("premier",), "Premier", "Modo ranqueado do CS2, com CS Rating e veto de mapas entre os times."),
]


def glossary_for(text):
    t = text.lower()
    return [(name, desc) for keys, name, desc in GLOSSARY
            if any(re.search(rf"(?<![\w-]){re.escape(k)}" + (r"(?!\w)" if len(k) <= 3 else ""), t) for k in keys)]


DISPLAY_REFS = {"rating": (1.0, 0.8), "kd": (1.0, 0.75), "kpr": (0.7, 0.55), "dpr": (0.66, 0.8),
                "accuracy": (0.18, 0.12), "avg_blind": (2.0, 1.0), "smokes_pr": (0.4, 0.2),
                "adr_ct": (75, 55), "adr_t": (75, 55), "kast_ct": (0.70, 0.58), "kast_t": (0.70, 0.58)}


def verdict(key, value, p=None):
    rule = next((r for r in RULES if r.metric == key), None)
    if rule and p is not None and p.get(rule.sample, 0) < rule.min_sample:
        return "Poucos dados", "muted"
    ok, bad = (rule.ok, rule.bad) if rule else DISPLAY_REFS.get(key, (None, None))
    if ok is None:
        return None
    x = (ok - value) / (ok - bad)
    if x <= -0.5:
        return "Ótimo", "good"
    if x <= 0:
        return "Bom", "good"
    if x < 0.6:
        return "Atenção", "warn"
    return "Precisa melhorar", "bad"
