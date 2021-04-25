import boto3
import os
import botocore
import paramiko
import time
import subprocess

from flask import Flask, jsonify, request, Response

app = Flask(__name__)

status = ""


# def create_key_pair():
#     ec2_client = boto3.client("ec2", region_name="us-west-2")
#     key_pair = ec2_client.create_key_pair(KeyName="ec2-key-pair1")

#     private_key = key_pair["KeyMaterial"]

#     # write private key to file with 400 permissions
#     with os.fdopen(os.open("./key_pair/aws_ec2_key.pem", os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
#         handle.write(private_key)

@app.route("/status",methods=['GET'])
def get_status():
    global status
    return jsonify({"Status":status})

def initialize_ec2():
    ec2 = boto3.resource('ec2',region_name = 'us-west-2')
    return ec2

def create_instance(instance_name, size):
    global status

    ec2 = initialize_ec2()

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

    status = 'EC2 instance created;'
    return instances[0].id

def copy_folder(address, username, password):

    p = subprocess.Popen(["scp", "-i", "./ec2-key-pair1.pem", "-r", "./Helloworld/", username+"@"+address+":."])
    sts = os.waitpid(p.pid, 0)

def wait_till_starts(instance):
    print("Inside wait till starts")
    while instance.state['Name'] != 'running':
       time.sleep(10)
       print('...instance is %s' % instance.state)
       instance.load()
    
    print("Instance state on return: ",instance.state)
    time.sleep(10)
    return

# def wait_for_ssh_to_be_ready(host):
#     client = paramiko.client.SSHClient()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     retry_interval = float(1)
#     timeout = int(20)
#     timeout_start = time.time()
#     while time.time() < timeout_start + timeout:
#         time.sleep(retry_interval)
#         try:
#             client.connect(host, allow_agent=False,look_for_keys=False)
#         except paramiko.ssh_exception.SSHException as e:
#         # socket is open, but not SSH service responded
#             if e.message == 'Error reading SSH protocol banner':
#                 print(e)
#         continue
#         print('SSH transport is available!')
#         break
#         except paramiko.ssh_exception.NoValidConnectionsError as e:
#             print('SSH transport is not ready...')
#     continue



def run_container(instanceId):
    global status

    key = paramiko.RSAKey.from_private_key_file("./ec2-key-pair1.pem")

    client = paramiko.SSHClient()
    # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.set_missing_host_key_policy()
    client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())


    ec2 = initialize_ec2()
    instance = ec2.Instance(id=instanceId)

    # wait_for_ssh_to_be_ready()

    wait_till_starts(instance)
    status = status + 'EC2 Instance started;'

    current_instance = list(ec2.instances.filter(InstanceIds=[instanceId]))
    
    ip_address = current_instance[0].public_ip_address
    public_dns = current_instance[0].public_dns_name

    # wait_for_ssh_to_be_ready("ec2-user"+ip_address)

    print("IP Address: ",ip_address)
    print("Public dns: ",public_dns)

    print("Trying to connect")

    client.connect(hostname=ip_address, username="ec2-user", pkey=key)

    print("Remote Server connected")
    
    copy_folder(public_dns, "ec2-user", key)

    cmd = 'sudo yum update -y'
    stdin, stdout, stderr = client.exec_command(cmd)    
    print("Yum update output: ",stdout.read())
    print("Yum update error: ",stderr.read())
    
    cmd = 'sudo yum install -y docker'
    stdin, stdout, stderr = client.exec_command(cmd)
    print("Docker install: ",stdout.read())
    print("Docker install error: ",stderr.read())

    status = status + "App copied, docker installed on remote machine;"

    print("Docker installed")
    
    cmd = 'sudo docker --version'
    stdin, stdout, stderr = client.exec_command(cmd)

    print("Docker version: ",stdout.read())
    print("Docker version error: ",stderr.read())
    cmd = 'sudo service docker start'
    stdin, stdout, stderr = client.exec_command(cmd)

    print("Docker service started: ",stdout.read())
    print("Docker service start error: ",stderr.read())
    
    cmd = 'cd Helloworld;sudo docker build -t helloworld:v3 .'
    stdin, stdout, stderr = client.exec_command(cmd)

    print("Docker image built: ",stdout.read())
    print("Docker image built error: ",stderr.read())

    status = status + "Docker image built"
    
    cmd = 'sudo docker run -p 80:80 helloworld:v3'
    stdin, stdout, stderr = client.exec_command(cmd)

    print("Docker image run: ",stdout.read())

    status = status + "Docker image running;"

    

    # print("Container started")
    

    # close the client connection once the job is done
    # client.close()



@app.route("/create_instance",methods=['POST'])
def create_instance_run_container():
    data = request.get_json()
    print("Data: ",data)

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
     
    else:
        return Response("Docker container is running", status = 200)

    

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, threaded= True)

    