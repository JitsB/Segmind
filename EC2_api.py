import boto3
import os
import botocore
import paramiko
import time
import subprocess
import datetime
import pytz

from flask import Flask, jsonify, request, Response

app = Flask(__name__)
ec2 = boto3.resource('ec2',region_name = 'us-west-2')

status = {}

@app.route("/status",methods=['GET'])
def get_status():
    return jsonify({"Status":status})

def create_instance(instance_name, size):
    global status

    instances = ec2.create_instances(
        ImageId="ami-013400284c3b666b4",
        MinCount=1,
        MaxCount=1,
        InstanceType=size,
        KeyName="ec2-key-pair1"
    )
    
    ec2.create_tags(Resources=[instances[0].id], Tags=[
        {
            'Key': 'Name',
            'Value': instance_name,
        },
    ])

    status['EC2 instance created;'] = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    return instances[0].id

#Get this from git clone
def copy_folder(address, username, password):

    p = subprocess.Popen(["scp", "-i", "./ec2-key-pair1.pem", "-r", "./Helloworld/", username+"@"+address+":."])
    sts = os.waitpid(p.pid, 0)

def wait_till_starts(instance):
    
    retries, max_retries = 0, 5
    
    while instance.state['Name'] != 'running' and retries < max_retries:
       time.sleep(10)
       instance.load()

    #Add validation in case max_retries is crossed but still the instance is not running, corner-case
    time.sleep(10)
    return

def execute_shell_cmd(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)

    if stderr != '':
        raise

def run_container(instanceId):
    global status

    key = paramiko.RSAKey.from_private_key_file("./ec2-key-pair1.pem")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())

    ec2 = initialize_ec2()
    instance = ec2.Instance(id=instanceId)

    wait_till_starts(instance)
    status['EC2 Instance started'] = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

    current_instance = list(ec2.instances.filter(InstanceIds=[instanceId]))
    
    ip_address = current_instance[0].public_ip_address
    
    client.connect(hostname=ip_address, username="ec2-user", pkey=key)

    print("Remote Server connected")
    
    copy_folder(public_dns, "ec2-user", key)
    #Validate if folder has been copied

    cmd = 'sudo yum update -y'
    execute_shell_cmd(cmd)
    
    cmd = 'sudo yum install -y docker'
    execute_shell_cmd(cmd)
    
    status["App copied, docker installed on remote machine"] = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    
    cmd = 'sudo docker --version'
    execute_shell_cmd(cmd)
    #Validate docker version

    cmd = 'sudo service docker start'
    execute_shell_cmd(cmd)
    
    cmd = 'cd Helloworld;sudo docker build -t helloworld:v3 .'
    execute_shell_cmd(cmd)

    status["Docker image built;"] = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    
    cmd = 'sudo docker run -d -p 80:80 helloworld:v3'
    execute_shell_cmd(cmd)

    #docker ps |  i.e. check if container is running

    print("Docker image run: ",stdout.read())

    status["Docker image running;"] = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

@app.route("/create_instance",methods=['POST'])
def create_instance_run_container():
    global status

    status = {}

    data = request.get_json()

    if 'name' not in data or 'size' not in data or data['name'] == "" or data['size'] == "":
        return Response(
        "Please specify both EC2 instance name and size",
        status=400
    )
    instance_name = data["name"]
    size = data["size"]
    try:
        instance_id = create_instance(instance_name, size)

        print("Instance created with id: ",instance_id)
        run_container(instance_id)

    except botocore.exceptions.ClientError as err:
        return Response(
        "Size requested for the ec2 instance is not available in the free-tier instance, Please change",
        status=400
    )

    except Exception as err:
        return Response(
        "Some Exception occured",
        status=503
    )
    else:
        return Response("Docker container is running", status = 200)

    
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, threaded= True)

    