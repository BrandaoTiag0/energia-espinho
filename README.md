# Previsão de consumo elétrico de Espinho (v1)

Objetivo: prever o consumo mensal de eletricidade de Espinho com dados abertos da E-Redes.

## Resultado

Método final: média do mesmo mês nos 2 anos anteriores.

Erro médio (percentagem, mês a mês, só com dados anteriores ao mês previsto):

    método            todos (30 meses)   sem 4 meses anómalos (26)
    simples (1 ano)   2,76 %             1,86 %
    média 2 anos      2,48 %             1,62 %
    média 3 anos      2,67 %             1,80 %

A média de 2 anos bate o método simples, mas por pouco: ganha em 15 de 26 meses.
Com tão poucos meses, a diferença pode ser sorte.

## Meses anómalos (nov 2025 a fev 2026)

A baixa tensão subiu 12 % a 16 % face ao ano anterior e voltou ao normal em março.
- Acontece nas 4 freguesias de Espinho e na mediana dos 278 concelhos de Portugal continental, sem os agregados "OUTROS" (+11,7 % em nov, +12,4 % em dez, +13,1 % em jan, +8,7 % em fev, -2,6 % em mar; src/diagnostico_nacional.py).
- A REN mostra o mesmo padrão no consumo nacional (variação face ao mesmo mês do ano anterior: nov +6,6 %, dez +6,9 %, jan +7,6 %, fev +3,7 %, mar -0,7 %; valores do Data Hub consultados em 30 set 2026, a REN revê-os). Com a correção de temperatura e dias úteis que a própria REN publica (não calculada aqui), a variação é de +2,3 % em nov, +4,8 % em dez, +5,3 % em jan e +4,4 % em fev, acima do crescimento de fundo de cerca de +2,7 % ao ano que a REN indica para 2026. A REN liga o consumo nacional de janeiro ao frio e às tempestades, e o de novembro a uma base baixa em nov 2024. Isto sugere que em boa parte é consumo real e não um erro de faturação, porque a REN mede o consumo na rede e não a faturação: o total de Espinho (todos os níveis de tensão) subiu +8,0 % a +10,5 % em nov-fev contra +3,7 % a +7,6 % no país, pelo que o consumo nacional explica cerca de dois terços a três quartos do salto em nov-jan e menos de metade em fev (comparação aproximada). O resto fica por explicar.
- Em Espinho o frio explica só parte do salto (src/graus_dia.py, graus-dia de aquecimento pela definição do Eurostat): dez teve 227 graus-dia contra 228 e fev 180 contra 177, e o consumo subiu 10,3 % e 8,0 %; só nov (143 contra 51) e jan (242 contra 206) tiveram mais frio. Estimativas do peso do frio no aumento de nov-fev (3,06 GWh): 11 % (0,33 GWh; ajuste ano contra ano só com dados anteriores a nov 2025, 2,5 MWh por grau-dia) e 29 % (0,90 GWh; regressão do consumo contra graus-dia em todos os meses, 7,0 MWh por grau-dia, que inclui os meses de 2025/26 e mistura frio com outros efeitos sazonais, por isso é uma estimativa por cima). Dados faturados suavizam os meses. A maior parte do aumento (cerca de 70 % a 90 %) fica por explicar.
- Por período tarifário (src/tarifario_espinho.py, src/tarifario_salto.py, src/tarifario_pais.py; conjunto "consumos faturados por período tarifário" da E-Redes, que só vai até dez 2025): o aumento de Espinho está quase todo na tarifa simples (80 % em nov e 89 % em dez; +14,8 % e +17,4 %), enquanto os consumos com horário sobem +3,5 % e +2,4 %. O país inteiro mostra o mesmo padrão (simples +14,3 % e +15,2 %; com horário +1,0 % e +1,1 %). Por isso não é específico de Espinho, e não parece vir de clientes a passar de tarifa com horário para simples (os consumos com horário não caíram), mas o que o concentra na tarifa simples não está identificado.
- A média mensal de temperatura de Espinho não explicou o salto (dezembro teve a mesma temperatura e subiu 14 %), mas esta média é grosseira.
- Parte do salto ficou por explicar: a baixa tensão sobe mais do que o total nacional.
- Nenhum modelo treinado só com Espinho o previa. Reportamos os dois números (com e sem estes meses).

## O que testámos e não ajudou

- Correção por crescimento dos últimos 12 meses (src/avaliar.py, 42 meses de teste, 2022-11 a 2026-04): 3,41 % contra 2,69 % do simples. Ganha em 15 de 42 meses. A janela de teste é diferente da tabela acima (30 meses), por isso os números do método simples não coincidem.
- Temperatura (correlação -0,81 é sobretudo sazonalidade): ano contra ano, 1 grau mais frio dá só cerca de 0,8 % mais consumo. Não bateu a média de 2 anos.
- Graus-dia de aquecimento (src/graus_dia.py, usa a temperatura real do mês): com tendência erra 2,29 % (todos os meses), 1,62 % (sem os 4 anómalos) e 6,65 % em nov-fev 2025/26; a média de 2 anos erra 2,48 %, 1,62 % e 8,05 %. Fora do inverno anómalo o ganho é nulo (1,62 % nos dois); no inverno 2025/26 o erro desce de 8,05 % para 6,65 %. Precisaria de previsões de temperatura, por isso o método final continua a ser a média de 2 anos.

## Limitações

- Dados mensais e faturados (não é consumo instantâneo).
- Só 30 meses de teste, com um inverno atípico.
- O teste com temperatura usa a temperatura real do mês, que na prática não se conhece antes.
- Maio de 2026 foi excluído por estar incompleto.

## Como repetir (por esta ordem)

    py src/download_eredes.py
    py src/limpar_espinho.py
    py src/temperatura.py
    py src/avaliar.py                     (correção por crescimento, 42 meses)
    py src/avaliar4.py                    (efeito da temperatura)
    py src/avaliar6.py                    (tabela final, 30 meses)
    py src/diagnostico.py                 (salto por nível de tensão)
    py src/diagnostico_freguesias.py      (salto por freguesia)
    py src/diagnostico_nacional.py        (salto nos concelhos do país)
    py src/graus_dia.py                  (graus-dia de aquecimento)
    py src/tarifario_espinho.py           (Espinho por período tarifário)
    py src/tarifario_salto.py             (aumento por período tarifário)
    py src/tarifario_pais.py              (comparação com o país)

Dados: E-Redes Open Data (consumos faturados por município) e Open-Meteo (temperatura).
REN Data Hub, evolução do consumo: https://datahub.ren.pt/pt/eletricidade/evolucao-do-consumo/
REN, novembro 2025: https://www.ren.pt/media/noticias/consumo-com-recorde-historico-ate-novembro
REN, dezembro 2025: https://www.ren.pt/media/noticias/consumo-de-energia-eletrica-atinge-valor-mais-elevado-de-sempre-em-2025

## Dados explorados

- Consumo horário por código postal (4500 é Espinho): só cobre 2022-11 a 2023-09 e não foi atualizado desde 2024, por isso não serve para prever.
- API da REN (servicebus.ren.pt, sem chave): devolve o consumo nacional diário em GWh inteiros (src/ren_teste.py); não tem dados de Espinho.
