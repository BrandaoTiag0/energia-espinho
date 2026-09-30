# Previsão do consumo elétrico de Espinho (v1)

**Objetivo:** prever o consumo mensal de eletricidade de Espinho
com dados abertos, sem gastar dinheiro e sem dados individuais
de contadores.

**Dados:** consumos faturados mensais da E-Redes por freguesia
(66 meses completos, nov 2020 a abr 2026), temperatura diária do
Open-Meteo e consumo nacional da REN.

**Resultado:** o melhor método foi a média do mesmo mês nos 2 anos
anteriores, com erro de 2,48 % (30 meses de teste, cada mês
previsto só com dados anteriores) e de 1,62 % sem os 4 meses
anómalos. Bate a previsão simples (2,76 % e 1,86 %), mas por pouco:
ganha em 15 de 26 meses, por isso a vantagem pode ser sorte.

**O que não funcionou:** a correção pelo crescimento recente (pior
que o simples), a temperatura média mensal e os graus-dia de
aquecimento. Estes últimos só ajudam no inverno anómalo e
precisariam de previsões de temperatura.

**Achado:** no inverno de 2025/26 o consumo de Espinho subiu 8 % a
10,5 %. O frio explica entre 11 % e 29 % desse aumento. O resto
concentra-se nos contratos de tarifa simples, em Espinho e no país
inteiro. A causa não está identificada.

**Limites:** dados mensais e faturados, só 30 meses de teste, e os
dados horários de Espinho só vão até setembro de 2023, por isso
uma previsão horária não é viável com dados abertos.

**O que aprendi:** testar sem espreitar o futuro, verificar cada
número na fonte, e que um resultado honesto vale mais do que um
modelo que só parece bom.
