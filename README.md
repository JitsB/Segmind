# Segmind
Flask application to spawn ec2 instances with configurable paramaters and running docker container on the spawned instance

The application has 2 endpoints:- 
1. POST /create_instance :- This endpoint spawns a new EC2 instance and runs a sample application as a **docker container** on the spawned EC2 instance.
It uses a **linux AMI(Amazon Machine Image)** to spawn the instance.

Mandatory Request Body Parameters for the route:-
1. name - Name of the EC2 instance to spawn
2. size - Type of the instance e.g. t4g.micro, t2.small, t2.large etc

Eg - http://localhost:80/create_instance

body - 
{
  'name':'test',
  'size':'t4g.micro'
}

2. GET /status :- This endpoint gives the status of the create request along with the timestamps of the various steps.
The different steps of the creation are:- 

  1. EC2 Instance Created
  2. EC2 Instance Started
  3. App copied, docker installed on remote machine
  4. Docker image built
  5. Docker container running

Eg - http://localhost:80/status

**Steps to run the application:-**

After cloning the repo, run python EC2_api.py to get the application running.
Once the app is up and running, you can go ahead with creating the instances and checking their statuses.

After running the app, you need to manually verify the authenticity of the remote host by entering 'yes'

Eg - 
The authenticity of host 'XXXX' can't be established.
ECDSA key fingerprint is SHA256:XXXX.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

Once the create_instance endpoint returns, the docker container should be running and you can query the ipaddress(printed in the logs) on port 80 to check the custom message
