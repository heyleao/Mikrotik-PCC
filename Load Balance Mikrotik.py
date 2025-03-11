#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador Automático de Script para Load Balance com PCC, Tabelas de Roteamento,
Rotas Default (com distâncias diferenciadas), Netwatch, Regras Mangle e PCC para LAN.
===========================================================================================

Para cada link, serão solicitados os seguintes dados:
  - Nome do link (ex.: LINK1)
  - Interface ou PPPoE (ex.: ether2-LINK1-COPEL ou pppoe-out1)
  - Gateway IP (ex.: 192.168.18.1)
  - IP de teste para o Netwatch (ex.: 8.8.8.8)
  - Status do link ("yes" para ativo, "no" para inativo)
  - Distância para rota default na tabela do link (ex.: 1)
  - Distância para rota default na tabela main (ex.: 1 ou 2)
  - (Opcional) VRF Interface para rota na main (caso necessário)
  - Velocidade do link em Mbps (ex.: 1000, 700, 600, etc.)

O script gera um arquivo “generated_script.rsc” com as configurações necessárias.
"""

import math

def main():
    print("Gerador de Script para Load Balance com PCC, Tabelas de Rotas e Netwatch")
    try:
        n_links = int(input("Digite o número de links a serem configurados: "))
    except ValueError:
        print("Valor inválido. Informe um número inteiro.")
        return

    links = []
    for i in range(n_links):
        print(f"\nConfiguração para o Link {i+1}:")
        nome     = input("  Nome do link (ex.: LINK1): ").strip()
        iface    = input("  Interface ou PPPoE (ex.: ether2-LINK1-COPEL ou pppoe-out1): ").strip()
        gateway  = input("  Gateway IP (ex.: 192.168.18.1): ").strip()
        ip_teste = input("  IP de teste para Netwatch (ex.: 8.8.8.8): ").strip()
        ativo    = input("  O link está ativo? (yes/no): ").strip().lower()
        dist_link= input("  Distância para rota default na tabela do link (ex.: 1): ").strip()
        dist_main= input("  Distância para rota default na tabela main (ex.: 1 ou 2): ").strip()
        vrf      = input("  VRF Interface para rota na main (opcional, deixe em branco se não houver): ").strip()
        try:
            velocidade = float(input("  Velocidade do link em Mbps (ex.: 1000, 700, 600): ").strip())
        except ValueError:
            print("  Velocidade inválida, use um número. Usando 1 Mbps por padrão.")
            velocidade = 1.0

        links.append({
            "nome": nome,
            "iface": iface,
            "gateway": gateway,
            "ip_teste": ip_teste,
            "ativo": ativo,
            "dist_link": dist_link,
            "dist_main": dist_main,
            "vrf": vrf,
            "velocidade": velocidade
        })
        
    script_lines = []
    script_lines.append("# Script de automação gerado")
    script_lines.append("# Configurações dinâmicas para Load Balance com PCC, Tabelas de Roteamento,")
    script_lines.append("# Rotas Default, Netwatch, Regras Mangle e PCC para LAN")
    script_lines.append("")
    
    # 1. Criação das tabelas de roteamento para cada link
    script_lines.append("# Criação das Tabelas de Roteamento")
    for link in links:
        script_lines.append(f"/routing table add disabled=no fib name={link['nome']}")
    script_lines.append("")
    
    # 2. Configurações individuais para cada link (Mangle, Rotas, Netwatch)
    for link in links:
        nome     = link["nome"]
        iface    = link["iface"]
        gateway  = link["gateway"]
        ip_teste = link["ip_teste"]
        ativo    = link["ativo"]
        dist_link= link["dist_link"]
        dist_main= link["dist_main"]
        vrf      = link["vrf"]
        
        disabled_str = "disabled=yes" if ativo == "no" else "disabled=no"

        # Regras de Mangle: marcar conexão e saída
        script_lines.append(f"/ip firewall mangle add action=mark-connection chain=prerouting comment=\"Marcar conexão de {nome}\" connection-mark=no-mark connection-state=new in-interface={iface} new-connection-mark={nome} {disabled_str}")
        script_lines.append(f"/ip firewall mangle add action=mark-routing chain=output comment=\"Marca saída de {nome}\" connection-mark={nome} new-routing-mark={nome} {disabled_str}")
        script_lines.append("")

        # Rotas default:
        # a) Rota na tabela específica do link
        script_lines.append(f"/ip route add check-gateway=ping {disabled_str} distance={dist_link} dst-address=0.0.0.0/0 gateway={gateway} routing-table={nome} scope=30 suppress-hw-offload=no target-scope=10 comment={nome}")
        # b) Rota na tabela main (incluindo vrf-interface se informado)
        vrf_str = f" vrf-interface={vrf}" if vrf != "" else ""
        script_lines.append(f"/ip route add check-gateway=ping comment={nome} {disabled_str} distance={dist_main} dst-address=0.0.0.0/0 gateway={gateway} pref-src=\"\" routing-table=main scope=30 suppress-hw-offload=no target-scope=10{vrf_str}")
        script_lines.append("")

        # Rota específica para o host de teste, usando a tabela do link
        script_lines.append(f"/ip route add disabled=no dst-address={ip_teste}/32 gateway={gateway} routing-table={nome} suppress-hw-offload=no")
        script_lines.append("")

        # Netwatch para monitoramento do link
        script_lines.append(f"/tool netwatch add {disabled_str} host={ip_teste} http-codes=\"\" name=\"TESTE {nome}\" type=simple down-script=\"/ip route set [find comment=\\\"{nome}\\\"] disabled=yes\" up-script=\"/ip route set [find comment=\\\"{nome}\\\"] disabled=no\"")
        script_lines.append("")
    
    # 3. Regras para LAN utilizando PCC com base na velocidade dos links
    # Calcula o número de buckets para cada link proporcional à sua velocidade
    velocidades = [link["velocidade"] for link in links if link["velocidade"] > 0]
    if len(velocidades) == 0:
        min_vel = 1.0
    else:
        min_vel = min(velocidades)
    
    total_buckets = 0
    for link in links:
        # Utiliza math.ceil para sempre arredondar para cima
        buckets = math.ceil(link["velocidade"] / min_vel)
        if buckets < 1:
            buckets = 1
        link["buckets"] = buckets
        total_buckets += buckets

    script_lines.append("# Regras de balanceamento para LAN utilizando PCC")
    script_lines.append(f"# Total de buckets: {total_buckets}")
    current_offset = 0
    for link in links:
        for b in range(link["buckets"]):
            script_lines.append(f"/ip firewall mangle add action=mark-connection chain=prerouting comment=\"Marcar conexão da LAN para {link['nome']} (bucket {b})\" connection-state=new dst-address-type=!local in-interface-list=LAN new-connection-mark={link['nome']} packet-mark=no-mark per-connection-classifier=src-address-and-port:{total_buckets}/{current_offset}")
            current_offset += 1
    script_lines.append("")
    
    # 4. (Opcional) Outras regras para LAN, se necessário
    script_lines.append("# Regras adicionais para LAN (exemplo)")
    script_lines.append("/ip firewall mangle add action=mark-routing chain=prerouting comment=\"Marcar rota da LAN para LINK1\" connection-mark=LINK1 in-interface-list=LAN new-routing-mark=LINK1")
    script_lines.append("/ip firewall mangle add action=mark-routing chain=prerouting comment=\"Marcar rota da LAN para LINK2\" connection-mark=LINK2 in-interface-list=LAN new-routing-mark=LINK2")
    
    # Escrita do script no arquivo
    output_file = "generated_script.rsc"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for line in script_lines:
                f.write(line + "\n")
        print(f"\nScript gerado com sucesso! Verifique o arquivo '{output_file}'.")
    except Exception as e:
        print(f"Erro ao escrever o arquivo: {e}")

if __name__ == "__main__":
    main()
