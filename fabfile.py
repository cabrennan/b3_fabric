from fabric.api import run
from fabric.api import env
from fabric.api import prompt
from fabric.api import execute
from fabric.api import sudo

import boto3
import time

env.aws_region='us-east-1'
env.key_filename = ["~/.ssh/fabtest.pem"]

def get_ec2_client():
   client = boto3.client('ec2')

   if 'client' not in env:
      client = boto3.client('ec2')
      if client is not None: 
         env.client = client
         print "Connected to EC2 region %s" % client
      else:
         msg = "Unable to connect to EC2 region %s"
         raise IOError(msg % env.aws_region)
   return env.client



