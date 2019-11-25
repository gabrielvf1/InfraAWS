import boto3
import os
import time



acessKey = os.environ["acessKeyCloud"]
secretAcessKey = os.environ["acessSecretKeyCloud"]
senhaDB1 = os.environ["senhaDB"]



nomeDaMaquina = "Gabriel Francato"
nomeDoOwner = "GabrielAps"

user_data_script2 = """#!/bin/bash
        export DEBIAN_FRONTEND=noninteractive
        sudo apt-get -yq update
        sudo apt-get -yq upgrade
        echo "Hello World" >> /tmp/data.txt
        cd /home/ubuntu
        sudo git clone https://github.com/gabrielvf1/Cloud2019.git
        sudo apt-get -yq install snapd
        sudo apt-get -yq install python3-pip
        sudo -H pip3 install flask
        sudo -H pip3 install flask-restful
        cd Cloud2019
        python3 Tarefas.py
        echo "Hello World" >> /tmp/data1.txt"""

class CriandoWebserver():
    def __init__(self):
        self.ec2 = boto3.client('ec2',region_name='us-east-1', aws_access_key_id = acessKey ,aws_secret_access_key=secretAcessKey)
        self.autoScale = boto3.client('autoscaling', region_name='us-east-1', aws_access_key_id = acessKey ,aws_secret_access_key=secretAcessKey)
        self.loadBalancer = boto3.client('elbv2', region_name='us-east-1', aws_access_key_id = acessKey ,aws_secret_access_key=secretAcessKey)
        self.nomeLB = 'ProjetoFrancatoLB'
        self.nomeKey = 'Gabriel_Projeto'
        self.securityGroupName = 'GabrielAPS'
        self.imageName = "ImageProjetoFrancato"
        self.launchConfigurationName = 'ProjetoFrancato'
        self.autoScalingGroupName = 'GrupoAutoScaleFrancato'
        self.nomeTarfetGroup = 'TargetGroupFrancato'

    def fechandoMaquinas(self, nomeMaquina, ownerMaquina):
        for i in range(len(self.ec2.describe_instances()['Reservations'])):
            try:
                nome = self.ec2.describe_instances()['Reservations'][i]['Instances'][0]['Tags'][0]['Value']
                estado = (self.ec2.describe_instances()['Reservations'][i]['Instances'][0]['State']['Name'])
            except:
                nome = "Sem Nome"
                estado = 'Invalido'
                print("Maquina sem Tag")

            if ((nome == nomeMaquina or nome == ownerMaquina) and (str(estado) == "running" or str(estado)=="shutting-down")):
                print("Maquina ja existe, deletando")
                lista = []
                # security_group_id = self.ec2.describe_instances()['Reservations'][i]['Instances'][0]['SecurityGroups'][0]['GroupId']
                lista.append(self.ec2.describe_instances()['Reservations'][i]['Instances'][0]['InstanceId'])
                waiter = self.ec2.get_waiter('instance_terminated')
                self.ec2.terminate_instances(InstanceIds=lista)
                print("Esperando maquina Terminar")
                waiter.wait(InstanceIds=lista)
                print("Maquina Terminada")

    def criandoKeys(self):
        chave = self.ec2.delete_key_pair(KeyName=self.nomeKey)
        chave = self.ec2.create_key_pair(KeyName=self.nomeKey)
        os.chmod("/home/gabrielvf/.ssh/privada_projeto.pem", 0o777)
        with open("/home/gabrielvf/.ssh/privada_projeto.pem", 'w+') as file:
            file.write(chave['KeyMaterial'])
        os.chmod("/home/gabrielvf/.ssh/privada_projeto.pem", 0o400)

    def criandoSecurityGroup(self):
        response = self.ec2.describe_vpcs()
        try:
            self.ec2.delete_security_group(GroupName=self.securityGroupName)
            print('Security Group Deleted')
            print("Security Group Nao existia, criando um novo")
            vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
            response = self.ec2.create_security_group(GroupName=self.securityGroupName,Description='Teste para o Projeto',VpcId=vpc_id)
            security_group_id = response['GroupId']
            print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
            self.ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {'IpProtocol': 'tcp',
                        'FromPort': 8080,
                        'ToPort': 8080,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                        {'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                        {'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                    ])
        except Exception as e:
            if ((str(e)[-22:-1]) == "has a dependent objec"):
                print("Ja existe o Security Group por algum motivo nao foi possivel deletar, vamos utilizar o mesmo portanto.")
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                security_group = self.ec2.describe_security_groups(GroupNames=[self.securityGroupName,])
                security_group_id = security_group['SecurityGroups'][0]['GroupId']
            else:
                print("Security Group Nao existia, criando um novo")
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                response = self.ec2.create_security_group(GroupName=self.securityGroupName,Description='Teste para o Projeto',VpcId=vpc_id)
                security_group_id = response['GroupId']
                print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
                self.ec2.authorize_security_group_ingress(
                        GroupId=security_group_id,
                        IpPermissions=[
                            {'IpProtocol': 'tcp',
                            'FromPort': 8080,
                            'ToPort': 8080,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                            {'IpProtocol': 'tcp',
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                            {'IpProtocol': 'tcp',
                            'FromPort': 80,
                            'ToPort': 80,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                        ])
                pass

        return security_group_id, vpc_id

    def criandoMaquina(self, idSecurityGroup, IP):
        user_data_script1 = """#!/bin/bash
        export DEBIAN_FRONTEND=noninteractive
        sudo apt-get -yq update
        sudo apt-get -yq upgrade
        echo "Hello World" >> /tmp/data.txt
        sudo bash -c 'echo "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> /etc/cron.d/startWebserver'
        sudo bash -c 'echo "@reboot root python3 /home/ubuntu/Cloud2019/Tarefas.py" >> /etc/cron.d/startWebserver'
        echo "ipPublicOhio: {}" >> /home/dados.txt
        cd /home/ubuntu
        sudo git clone https://github.com/gabrielvf1/Cloud2019.git
        sudo apt-get -yq install snapd
        sudo apt-get -yq install python3-pip
        sudo -H pip3 install flask
        sudo -H pip3 install flask-restful
        sudo -H pip3 install requests
        cd Cloud2019
        python3 Tarefas.py
        echo "Hello World" >> /tmp/data1.txt""".format(IP)

        print("Criando Maquina")
        waiter = self.ec2.get_waiter('instance_running')
        instancia = self.ec2.run_instances(ImageId='ami-04b9e92b5572fa0d1', MinCount=1, MaxCount=1,  InstanceType='t2.micro', KeyName='Gabriel_Projeto', SecurityGroupIds=[idSecurityGroup,], UserData = user_data_script1)
        self.ec2.create_tags(
            Resources=[
                instancia['Instances'][0]['InstanceId'],
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': nomeDoOwner
                },
                {
                    'Key': 'Owner',
                    'Value': nomeDaMaquina
                }
            ]
        )
        print("Esperando Maquina subir Totalmente")
        waiter.wait(InstanceIds=[instancia['Instances'][0]['InstanceId']])
        print("Maquina terminou de subir, STATUS: Running")
        return instancia['Instances'][0]['InstanceId']

    def release_address(self):
        try:
            resposta = self.ec2.describe_addresses(Filters=[{'Name': 'tag:Name',  'Values': ['GabrielFrancato',]}])
            AllocationID = resposta['Addresses'][0]['AllocationId']
            print('Deletou IP')
            self.ec2.release_address(AllocationId=AllocationID)
        except:
            print('Nao existia IP ainda, portanto nao foi deletado')

    def allocateIP(self, idInstancia):
        # try:
        print("Alocando IP")
        allocation = self.ec2.allocate_address(Domain='vpc')
        response = self.ec2.associate_address(AllocationId=allocation['AllocationId'],InstanceId=idInstancia)
        self.ec2.create_tags(
            Resources=[
                allocation['AllocationId'],
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': 'GabrielFrancato'
                },
            ]
        )
        # except:
        #     print("Erro Alocando IP")
        resposta = self.ec2.describe_instances(InstanceIds=[idInstancia,])
        ipInstancia = resposta['Reservations'][0]['Instances'][0]['PublicIpAddress']
        return ipInstancia

    def excluindoImage(self):
        try:
            images = self.ec2.describe_images(Filters =[{'Name': 'tag:Project',  'Values': ['Francato']}])
            id_image = images['Images'][0]['ImageId']
            self.ec2.deregister_image(ImageId=id_image)
            print("Imagem Excluida")
        except:
            print("Imagem nao existia")
            pass

    def criandoImage(self, idInstance):
        self.excluindoImage()
        image = self.ec2.create_image(InstanceId=idInstance, NoReboot=True, Name=self.imageName)
        id_image = image['ImageId']
        self.ec2.create_tags(
            Resources=[
                id_image,
            ],
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'Francato'
                }
            ]
        )
        images = self.ec2.describe_images(Filters =[{'Name': 'tag:Project',  'Values': ['Francato']}])
        estado = images['Images'][0]['State']
        if(estado == 'pending'):
            print("Esperando a imagem ser criada")
            while(estado != 'available'):
                images = self.ec2.describe_images(Filters =[{'Name': 'tag:Project',  'Values': ['Francato']}])
                estado = images['Images'][0]['State']
        print("Imagem Criada")
        lista = []
        lista.append(idInstance)
        print("Imagem criada")
        return id_image

    def criandoAutoScaling(self, imageId, securityId, subnetsId, IP):
        user_data_script1 = """#!/bin/bash
        export DEBIAN_FRONTEND=noninteractive
        sudo apt-get -yq update
        sudo apt-get -yq upgrade
        echo "Hello World" >> /tmp/data.txt
        sudo bash -c 'echo "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> /etc/cron.d/startWebserver'
        sudo bash -c 'echo "@reboot root python3 /home/ubuntu/Cloud2019/tarefasAutoScale.py" >> /etc/cron.d/startWebserver'
        echo "ipPublicWebserverVirigia: {}" >> /home/dados.txt
        cd /home/ubuntu
        sudo git clone https://github.com/gabrielvf1/Cloud2019.git
        sudo apt-get -yq install snapd
        sudo apt-get -yq install python3-pip
        sudo -H pip3 install flask
        sudo -H pip3 install flask-restful
        sudo -H pip3 install requests
        cd Cloud2019
        python3 tarefasAutoScale.py
        echo "Hello World" >> /tmp/data1.txt""".format(IP)

        print("Criando launch configuration")
        subnetsIdString = ",".join(subnetsId)
        autoScaleConfig = self.autoScale.create_launch_configuration(
            LaunchConfigurationName=self.launchConfigurationName,
            ImageId=imageId,
            KeyName=self.nomeKey,
            SecurityGroups=[securityId],
            InstanceType='t2.micro',
            EbsOptimized=False,
            UserData= user_data_script1
            # AssociatePublicIpAddress=False
        )
        print("Criando auto scale group")
        asGroup = self.autoScale.create_auto_scaling_group(
            AutoScalingGroupName=self.autoScalingGroupName,
            LaunchConfigurationName=self.launchConfigurationName,
            MinSize=1,
            MaxSize=3,
            DesiredCapacity=1,
            DefaultCooldown=120,
            HealthCheckType='EC2',
            HealthCheckGracePeriod=60,
            Tags=[
                {
                    'Key': 'Name',
                    'Value': nomeDoOwner
                },
                {
                    'Key': 'Owner',
                    'Value': nomeDaMaquina
                }
            ],
            VPCZoneIdentifier=subnetsIdString
        )

    def excluiAutoScale(self):

        try:
            arn = self.loadBalancer.describe_target_groups(Names=[self.nomeTarfetGroup,])['TargetGroups'][0]['TargetGroupArn']
            self.autoScale.detach_load_balancer_target_groups(AutoScalingGroupName=self.autoScalingGroupName, TargetGroupARNs=[arn,])
        except:
            print("O Auto Scaling nao tem target group adiconado, ignorando")
        autoScaleGroups = (self.autoScale.describe_auto_scaling_groups())
        for i in range(len(autoScaleGroups['AutoScalingGroups'])):
            if (autoScaleGroups['AutoScalingGroups'][i]['AutoScalingGroupName'] == 'GrupoAutoScaleFrancato'):
                a = True
                self.autoScale.delete_auto_scaling_group(AutoScalingGroupName='GrupoAutoScaleFrancato', ForceDelete =True,)
                self.autoScale.delete_launch_configuration(LaunchConfigurationName='ProjetoFrancato',)
                autoScaleGroups = (self.autoScale.describe_auto_scaling_groups())
                estado = autoScaleGroups['AutoScalingGroups'][i]['Status']
                while(estado == 'Delete in progress'):
                    if a:
                        print("Deletando Auto Scale")
                        a = False
                    try:
                        estado = self.autoScale.describe_auto_scaling_groups()['AutoScalingGroups'][i]['Status']
                    except:
                        estado = 'Deletado'
                print('Auto Scale deletado')
        # self.fechandoMaquinas(nomeDaMaquina, nomeDoOwner)

    def pegandoSubnets(self, idVPC):
        listaSubnets = []
        for i in self.ec2.describe_subnets()['Subnets']:
            if i['VpcId'] == idVPC:
                listaSubnets.append(i['SubnetId'])
        return listaSubnets

    def criandoLoadBalancer(self, securityId, SubnetsId):
        print("Criando Load Balancer")
        resposta = self.loadBalancer.create_load_balancer(
            Name=self.nomeLB,
            Subnets=SubnetsId,
            SecurityGroups = [securityId],
            Tags=[
                {
                    "Key": "Name",
                    "Value": nomeDoOwner
                },
                {
                    'Key': 'Owner',
                    'Value': nomeDaMaquina
                }]
        )
        endereco = (resposta['LoadBalancers'][0]['DNSName'])
        print("Esperando Load Balancer ficar Ativo")
        with open("DNSLoadBalancer.txt", 'w+') as file:
            file.write('DNSLoadBalancer: ' + 'http://' + endereco.lower())
        waiter = self.loadBalancer.get_waiter('load_balancer_available')
        waiter.wait(Names=[self.nomeLB,])
        print("Load Balancer Ativo")
        arn = self.loadBalancer.describe_load_balancers(Names=[self.nomeLB,])['LoadBalancers'][0]['LoadBalancerArn']
        return arn

    def deletandoLoadBalancer(self):
        try:
            arn = self.loadBalancer.describe_load_balancers(Names=[self.nomeLB,])['LoadBalancers'][0]['LoadBalancerArn']
            print("Deletando Load Balancer")
            self.loadBalancer.delete_load_balancer(LoadBalancerArn=arn)
            waiter =  self.loadBalancer.get_waiter('load_balancers_deleted')
            waiter.wait(Names=[self.nomeLB,])
        except:
            print('Load Balancer nao Existe ainda')

    def criandoTargetGroup(self, IDVpc):
        resposta = self.loadBalancer.create_target_group(
            Name=self.nomeTarfetGroup,
            Protocol='HTTP',
            Port=8080,
            VpcId=IDVpc,
            HealthCheckProtocol='HTTP',
            HealthCheckPort="8080",
            HealthCheckPath="/",
            Matcher={"HttpCode": "200"},
        )
        print("Targe Group Ativo")
        target_group = resposta.get("TargetGroups")[0]
        arn = target_group["TargetGroupArn"]
        self.loadBalancer.add_tags(ResourceArns=[arn], Tags=[{"Key": "Nome", "Value": "Francato"}])
        return arn

    def deletandoTargetGroup(self):
        try:
            arn = self.loadBalancer.describe_target_groups(Names=[self.nomeTarfetGroup,])['TargetGroups'][0]['TargetGroupArn']
            print("Deletando Target Group")
            self.loadBalancer.delete_target_group(TargetGroupArn=arn)
        except:
            print('Target Group nao Existe ainda')

    def criandoListener(self, arnLB, arnTG):
        resposta = self.loadBalancer.create_listener(
            LoadBalancerArn=arnLB,
            Protocol="HTTP",
            Port=80,
            DefaultActions=[
                {"Type": "forward", "TargetGroupArn": arnTG}
            ],
        )
        print("Listener Ativo")
        print("Adicinando Load Balancer no Auto Scaling")
        self.adicionandoLoadBalancerToAutoScaling(arnTG)

    def deletandoListener(self):
        try:
            arnLB = self.loadBalancer.describe_load_balancers(Names=[self.nomeLB,])['LoadBalancers'][0]['LoadBalancerArn']
            arnListener = self.loadBalancer.describe_listeners(LoadBalancerArn=arnLB)['Listeners'][0]['ListenerArn']
            print("Deletando Listener")
            self.loadBalancer.delete_listener(ListenerArn=arnListener)
        except:
            print('Listener nao Existe ainda')

    def adicionandoLoadBalancerToAutoScaling(self, arnTG):
        self.autoScale.attach_load_balancer_target_groups(AutoScalingGroupName=self.autoScalingGroupName, TargetGroupARNs=[arnTG,])


class RDSeInfra():
    def __init__(self):
        self.RDS =  boto3.client('rds' ,region_name='us-east-2', aws_access_key_id = acessKey ,aws_secret_access_key=secretAcessKey)
        self.ec2 = boto3.client('ec2',region_name='us-east-2', aws_access_key_id = acessKey ,aws_secret_access_key=secretAcessKey)
        self.securityGroupName = 'GabrielRDSProj'
        self.securityGroupNameInstancia = 'GabrielInstanciaOhio'
        self.dbIdentificador = 'bancocloud'
        self.DBName = 'RDSCloudFrancato'
        self.DBUser = 'AdminFrancato'
        self.nomeKey = 'Gabriel Francato Ohio'

    def criandoSecurityGroup(self):
        response =  self.ec2.describe_vpcs()
        try:
            self.ec2.delete_security_group(GroupName=self.securityGroupName)
            print('Security Group Deleted')
            print("Security Group Nao existia, criando um novo")
            vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
            response = self.ec2.create_security_group(GroupName=self.securityGroupName,Description='Teste para o Projeto',VpcId=vpc_id)
            security_group_id = response['GroupId']
            print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
            self.ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {'IpProtocol': 'tcp',
                        'FromPort': 3306,
                        'ToPort': 3306,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                    ])
            # print('Ingress Successfully Set %s' % data)

        except Exception as e:
            if ((str(e)[-22:-1]) == "has a dependent objec"):
                print("Ja existe o Security Group por algum motivo nao foi possivel deletar, vamos utilizar o mesmo portanto.")
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                security_group = self.ec2.describe_security_groups(GroupNames=[self.securityGroupName,])
                security_group_id = security_group['SecurityGroups'][0]['GroupId']
            else:
                print("Security Group Nao existia, criando um novo")
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                response = self.ec2.create_security_group(GroupName=self.securityGroupName,Description='Teste para o Projeto',VpcId=vpc_id)
                security_group_id = response['GroupId']
                print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
                self.ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {'IpProtocol': 'tcp',
                        'FromPort': 3306,
                        'ToPort': 3306,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                    ])
                pass

        return security_group_id, vpc_id

    def criandoInstaciaRDS(self, idSecurityGroup):
        rdsInstance = self.RDS.create_db_instance(DBInstanceIdentifier=self.dbIdentificador,
            AllocatedStorage=5,
            DBName=self.DBName,
            Engine='MySQL',
            Port=3306,
            # General purpose SSD
            StorageEncrypted=False,
            AutoMinorVersionUpgrade=False,
            # Set this to true later?
            MasterUsername=self.DBUser,
            MasterUserPassword=senhaDB1,
            DBInstanceClass='db.t2.micro',
            VpcSecurityGroupIds=[idSecurityGroup],
            Tags=[{'Key': 'Name', 'Value': 'FrancatoRDS'}])
        waiter = self.RDS.get_waiter('db_instance_available')
        print('Esperando o RDS Subir completamente')
        waiter.wait(DBInstanceIdentifier=self.dbIdentificador)
        descricao =self.RDS.describe_db_instances(DBInstanceIdentifier=self.dbIdentificador)
        endpoint = descricao['DBInstances'][0]['Endpoint']['Address']
        port = descricao['DBInstances'][0]['Endpoint']['Port']

        return endpoint, port
    def deletandoRDS(self):
        try:
            self.RDS.delete_db_instance(DBInstanceIdentifier=self.dbIdentificador, SkipFinalSnapshot=True)
            print("Esperando o RDS ser deletado")
            waiter=self.RDS.get_waiter('db_instance_deleted')
            waiter.wait(DBInstanceIdentifier=self.dbIdentificador)
        except:
            print("RDS nao existia, portanto nao foi possivel deleta-lo")

    def criandoMaquina(self, idSecurityGroup,endpoint,port):
        print("Criando Maquina")
        user_data_script = '''#!/bin/bash
        export DEBIAN_FRONTEND=noninteractive
        sudo apt-get -yq update
        sudo apt-get -yq upgrade
        echo "Hello World" >> /tmp/data.txt
        cd /home/ubuntu
        sudo git clone https://github.com/gabrielvf1/Cloud2019-RDS.git
        sudo apt-get -yq install snapd
        sudo apt-get -yq install python3-pip
        sudo -H pip3 install PyMySQL
        sudo -H pip3 install functools
        sudo -H pip3 install flask
        sudo -H pip3 install flask-restful
        cd Cloud2019-RDS
        sudo bash -c 'echo "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> /etc/cron.d/startWebserver'
        sudo bash -c 'echo "@reboot root python3 /home/ubuntu/Cloud2019-RDS/backEndOhio.py" >> /etc/cron.d/startWebserver'
        echo "endpoint: {}" >> /home/dados.txt
        echo "senha: {}" >> /home/dados.txt
        cd Cloud2019-RDS/
        python3 scriptFrancato.py
        python3 backEndOhio.py
        echo "Hello World" >> /tmp/data1.txt'''.format(endpoint,senhaDB1)

        waiter = self.ec2.get_waiter('instance_status_ok')
        instancia = self.ec2.run_instances(ImageId='ami-0d5d9d301c853a04a', MinCount=1, MaxCount=1,  InstanceType='t2.micro', KeyName=self.nomeKey, SecurityGroupIds=[idSecurityGroup,], UserData=user_data_script)
        self.ec2.create_tags(
            Resources=[
                instancia['Instances'][0]['InstanceId'],
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': nomeDoOwner
                },
                {
                    'Key': 'Owner',
                    'Value': nomeDaMaquina
                }
            ]
        )
        print("Esperando Maquina OHIO subir Totalmente")
        waiter.wait(InstanceIds=[instancia['Instances'][0]['InstanceId']])
        print("Maquina terminou de subir")
        return instancia['Instances'][0]['InstanceId']

    def criandoSecurityGroupInstacia(self):
        response =  self.ec2.describe_vpcs()
        try:
            self.ec2.delete_security_group(GroupName=self.securityGroupNameInstancia)
            print('Security Group Deleted')
            print("Security Group Nao existia, criando um novo")
            vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
            response = self.ec2.create_security_group(GroupName=self.securityGroupNameInstancia,Description='Teste para o Projeto',VpcId=vpc_id)
            security_group_id = response['GroupId']
            print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
            self.ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                    ])

        except Exception as e:
            if ((str(e)[-22:-1]) == "has a dependent objec"):
                print("Ja existe o Security Group por algum motivo nao foi possivel deletar, vamos utilizar o mesmo portanto.")
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                security_group = self.ec2.describe_security_groups(GroupNames=[self.securityGroupNameInstancia,])
                security_group_id = security_group['SecurityGroups'][0]['GroupId']
            else:
                print("Security Group Nao existia, criando um novo")
                vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
                response = self.ec2.create_security_group(GroupName=self.securityGroupNameInstancia,Description='Teste para o Projeto',VpcId=vpc_id)
                security_group_id = response['GroupId']
                print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
                self.ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                    ])
                pass

        return security_group_id, vpc_id

    def criandoKeys(self):
        chave = self.ec2.delete_key_pair(KeyName=self.nomeKey)
        chave = self.ec2.create_key_pair(KeyName=self.nomeKey)
        try:
            os.chmod("/home/gabrielvf/.ssh/privada_projeto_ohio.pem", 0o777)
            print("Chave ja existente, deletando")
        except:
            print("Chave inexistente, criando do zero")

        with open("/home/gabrielvf/.ssh/privada_projeto_ohio.pem", 'w+') as file:
            file.write(chave['KeyMaterial'])
        os.chmod("/home/gabrielvf/.ssh/privada_projeto_ohio.pem", 0o400)

    def deletandoInstancia(self):
        try:
            resposta = self.ec2.describe_instances(Filters=[{'Name': 'tag:Owner',  'Values': [nomeDaMaquina]},{'Name': 'instance-state-name','Values': ['running',]}])
            id = (resposta['Reservations'][0]['Instances'][0]['InstanceId'])
            self.ec2.terminate_instances(InstanceIds=[id])
            print("Esperando instancia ser Deletada")
            waiter = self.ec2.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=[id])
            print("Instacia deletada")
        except:
            print("Instacia inexistente, nao foi necessario deletar instancia")

    def autorizandoSecurityGroup(self, securityId,IP):
        print("Autorizando o IP: {} a acessar essa maquina".format(IP))
        self.ec2.authorize_security_group_ingress(
                    GroupId=securityId,
                    IpPermissions=[
                        {'IpProtocol': 'tcp',
                        'FromPort': 8080,
                        'ToPort': 8080,
                        'IpRanges': [{'CidrIp': IP + '/32'}]}
                    ])
    def release_address(self):
        try:
            resposta = self.ec2.describe_addresses(Filters=[{'Name': 'tag:Name',  'Values': ['GabrielFrancato',]}])
            AllocationID = resposta['Addresses'][0]['AllocationId']
            print('Deletou IP')
            self.ec2.release_address(AllocationId=AllocationID)
        except:
            print('Nao existia IP ainda, portanto nao foi deletado')

    def allocateIP(self, idInstancia):
        # try:
        print("Alocando IP")
        allocation = self.ec2.allocate_address(Domain='vpc')
        response = self.ec2.associate_address(AllocationId=allocation['AllocationId'],InstanceId=idInstancia)
        self.ec2.create_tags(
            Resources=[
                allocation['AllocationId'],
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': 'GabrielFrancato'
                },
            ]
        )
        # except:
        #     print("Erro Alocando IP")
        resposta = self.ec2.describe_instances(InstanceIds=[idInstancia,])
        ipInstancia = resposta['Reservations'][0]['Instances'][0]['PublicIpAddress']
        return ipInstancia

RDS = RDSeInfra()
objeto = CriandoWebserver()
RDS.deletandoInstancia()
RDS.deletandoRDS()
RDS.release_address()
securityID, VPCID = RDS.criandoSecurityGroup()
endpointRDS, portaRDS = RDS.criandoInstaciaRDS(securityID)
RDS.criandoKeys()
securityIDInstancia, VPCIDInstacia = RDS.criandoSecurityGroupInstacia()
instanceIdOhio = RDS.criandoMaquina(securityIDInstancia, endpointRDS, portaRDS)
ipInstaciaOhio = RDS.allocateIP(instanceIdOhio)

objeto.excluiAutoScale()
objeto.deletandoListener()
objeto.deletandoLoadBalancer()
objeto.deletandoTargetGroup()
objeto.fechandoMaquinas(nomeDaMaquina, nomeDoOwner)
objeto.criandoKeys()
objeto.release_address()
securityGroupId, vpcID = objeto.criandoSecurityGroup()
subnets = objeto.pegandoSubnets(vpcID)
instanceId = objeto.criandoMaquina(securityGroupId, ipInstaciaOhio)
ipWEbserverVirginia = objeto.allocateIP(instanceId)
RDS.autorizandoSecurityGroup(securityIDInstancia, ipWEbserverVirginia)
idImage = objeto.criandoImage(instanceId)
objeto.criandoAutoScaling(idImage, securityGroupId, subnets, ipWEbserverVirginia)
arnLoadBalancer = objeto.criandoLoadBalancer(securityGroupId, subnets)
arnTargetGroup = objeto.criandoTargetGroup(vpcID)
objeto.criandoListener(arnLoadBalancer, arnTargetGroup)
objeto.adicionandoLoadBalancerToAutoScaling(arnTargetGroup)



