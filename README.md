# InfraAWS
Projeto da materia computacao em nuvem que visa subir uma arquitetura atraves de scripts na AWS. O script é 100% automatizado, ou seja, se voce quiser rodar eles varias vezes seguidas ele excluira tudo criado anteriormente e recriara.

# Tutorial

Adicione no seu .bashrc as seguintes variaveis:

export acessKeyCloud="[Ponha sua key aqui]" <br/><br/>
export acessSecretKeyCloud="[Ponha sua secret key aqui]" <br/><br/>
export senhaDB="[Ponha a senha do banco de dados da RDS aqui]" <br/><br/>

Enfim rode o script: InfraAWS-GabrielFrancato.py

Para testar apos o fim do script anterior utilize o arquivo clientTest.py, ele ja deve estar configurado com o DNS do loadbalancer para testar a conexao, basta rodar o arquivo com a funcionalidade desejada e ver o resultado.

Utilize: python3 clientTest.py [FUNCIONALIDADES DISPONIVEIS ABAIXO]

===================================== HELP =======================================

clientTest.py listar --LISTA AS TAREFAS DO DICIONARIO

clientTest.py adicionar [tarefa_a_ser_adicionada] --ADICIONA UMA TAREFA

clientTest.py buscar [id_tarefa_buscada] --BUSCA UMA TAREFA

clientTest.py apagar [id_tarefa_apagada] --APAGA UMA TAREFA

clientTest.py atualizar [id_tarefa_a_ser_atualizada] [nome_tarefa] --ATUALIZA UMA TAREFA DO DICIONARIO

# Explicacao

Os arquivos de inicializacao dos webservers desse projeto estao em dois gits diferentes, sao eles:

https://github.com/gabrielvf1/Cloud2019
e
https://github.com/gabrielvf1/Cloud2019-RDS.

Desenvolvido por Gabriel Francato
