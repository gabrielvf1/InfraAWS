#!/usr/bin/python
import sys
import requests


f= open("DNSLoadBalancer.txt","r")
dados = f.readlines()

for i in dados:
    linha = i.split()
    if linha[0] == 'DNSLoadBalancer:':
        DNSLoadBalancer = linha[1]

try:
    palavra1 = sys.argv[1].lower()
except :
    palavra1 = 0
    pass

try:
    palavra2 = sys.argv[2]
except :
    palavra2 = 0
    pass

try:
    palavra3 = sys.argv[3]
except :
    palavra3 = 0
    pass


if (palavra1 == 'listar'):
    tarefas = requests.get((DNSLoadBalancer + '/Tarefa'))
    print(tarefas.json())

elif (palavra1 == 'adicionar' and palavra2 != 0):
    a = requests.post(DNSLoadBalancer + '/Tarefa/', json={'Tarefa': palavra2})
    tarefas = requests.get(DNSLoadBalancer + '/Tarefa/')
    print(tarefas.json())

elif (palavra1 == 'buscar' and palavra2 != 0):
    tarefas = requests.get(DNSLoadBalancer + '/Tarefa/' + palavra2)
    print(tarefas.json())

elif (palavra1 == 'apagar' and palavra2 != 0):
    tarefas = requests.delete(DNSLoadBalancer + '/Tarefa/' + palavra2)
    print(tarefas.json())

elif (palavra1 == 'atualizar' and palavra2 != 0 and palavra3 != 0):
    requests.delete(DNSLoadBalancer + '/Tarefa/' + palavra2)
    tarefa = requests.put(DNSLoadBalancer + '/Tarefa/' + palavra2, json={'Tarefa': palavra3} )
    tarefas = requests.get(DNSLoadBalancer + '/Tarefa')
    print(tarefas.json())

else:
    print('===================================== '+ 'HELP' + ' =======================================' + "\n")
    print('tarefa '+ 'listar' + ' --LISTA AS TAREFAS DO DICIONARIO' + "\n")
    print('tarefa '+ 'adicionar' + " [tarefa_a_ser_adicionada]" + ' --ADICIONA UMA TAREFA' + "\n")
    print('tarefa '+ 'buscar' + " [id_tarefa_buscada]"  + ' --BUSCA UMA TAREFA' + "\n")
    print('tarefa '+ 'apagar' + " [id_tarefa_apagada]"  + ' --APAGA UMA TAREFA' + "\n")
    print('tarefa '+ 'atualizar' + " [id_tarefa_a_ser_atualizada]" + " [nome_tarefa]"  + ' --ATUALIZA UMA TAREFA DO DICIONARIO' + "\n")