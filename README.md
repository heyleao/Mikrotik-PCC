# Gerador Automático de Script para Load Balance com PCC e Netwatch

Este repositório contém um script em Python que gera automaticamente um script de configuração para dispositivos Mikrotik RouterOS. Através do script, é possível configurar:

- **Tabelas de Roteamento** para cada link.
- **Regras de Mangle** para marcar conexões e saídas.
- **Rotas Default** em tabelas específicas e na tabela `main`, com distâncias diferenciadas.
- **Rotas específicas** para teste de conectividade (usando um IP de teste).
- **Netwatch** para monitoramento dos links, com scripts de ativação/desativação de rotas.
- **Regras de PCC para LAN**, onde o número de buckets é calculado proporcionalmente à velocidade dos links.

## Funcionalidades

- **Automatização Completa:** Insira as informações dos links (nome, interface/PPPoE, gateway, IP de teste, status, distâncias, VRF e velocidade) e gere um script pronto para ser importado no RouterOS.
- **Cálculo de Buckets para PCC:** O script determina automaticamente o número de buckets para o PCC com base na velocidade dos links, permitindo um balanceamento proporcional.  
  _Exemplo:_ Se você informar um link de 700 Mbps e outro de 600 Mbps, o primeiro terá 2 buckets e o segundo 1 bucket, totalizando 3 buckets (ex.: `per-connection-classifier=src-address-and-port:3/0`, `3/1` e `3/2`).
- **Flexibilidade:** Adapte facilmente os parâmetros e a lógica de geração conforme sua infraestrutura e necessidades específicas.

## Pré-requisitos

- Python 3.x

## Uso

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
