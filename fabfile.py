from fabric.api import*
# run
#jifrom fabric.api import env
#jfrom fabric.api import prompt
#jfrom fabric.api import execute
#from fabric.api import sudo

import boto3
import time
import sys

env.key_filename = ["~/.ssh/fabtest.pem"]

def print_dict(obj, nested_level=0, output=sys.stdout):
    spacing = '   '
    if type(obj) == dict:
        print >> output, '%s{' % ((nested_level) * spacing)
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print >> output, '%s%s:' % ((nested_level + 1) * spacing, k)
                print_dict(v, nested_level + 1, output)
            else:
                print >> output, '%s%s: %s' % ((nested_level + 1) * spacing, k, v)
        print >> output, '%s}' % (nested_level * spacing)
    elif type(obj) == list:
        print >> output, '%s[' % ((nested_level) * spacing)
        for v in obj:
            if hasattr(v, '__iter__'):
                print_dict(v, nested_level + 1, output)
            else:
                print >> output, '%s%s' % ((nested_level + 1) * spacing, v)
        print >> output, '%s]' % ((nested_level) * spacing)
    else:
        print >> output, '%s%s' % (nested_level * spacing, obj)


def _get_ec2_client():
   client = boto3.client('ec2')

   if 'client' not in env:
      client = boto3.client('ec2')
      if client is not None: 
         env.client = client
         print "Connected to EC2" 
      else:
         msg = "Unable to connect to EC2"
         raise IOError(msg)
   return env.client

def _describe_instances():
   client = _get_ec2_client()
   resp = client.describe_instances()
   i=1 
   instances=[] 
   for res in resp['Reservations'] : 
      res['Instances'][0]['Num']=i
      instances.append(res['Instances'][0])
      i+=1
   env.instances = instances
   return instances

def get_instance():
   instances_summary()
   prompt_text = "Choose instance from the above list: "    

   def valid_choice(input):
      choice = int(input)
      if not choice in range(1, len(env.instances) + 1):
         raise ValueError("%d is not a valid choice" % choice)
      return choice -1

   choice = prompt(prompt_text, validate=valid_choice)
   env.this_instance = env.instances[choice]

def inst_keys_summary():
   
   summary = "Top Level Key Summary: \n"
   summary += "Num\tKey\n"
   i=1
   keys=[]
   for res in env.this_instance:
      key = {i:res}
      keys.append(key)
      summary += "%s\t%s\n" % (i,res)
      i+=1
   env.inst_keys = keys
   print summary
   

def get_key():
   print "\n\nInstance: %s:  %s" % (env.this_instance['Num'],env.this_instance['InstanceId'])
   inst_keys_summary()
   prompt_text = "Choose key that you'd like see details on from the above list: "    
   def valid_choice(input):
      choice = int(input)
      if not choice in range(1, len(env.inst_keys) + 1):
         raise ValueError("%d is not a valid choice" % choice)
      return choice -1
   choice = prompt(prompt_text, validate=valid_choice)
   key_name=choice+1
   env.this_key = env.inst_keys[choice][key_name]

   
@task
def list_inst_detail():
   get_instance()
   get_key()
   print "\n\nInstance: %s:  %s" % (env.this_instance['Num'],env.this_instance['InstanceId'])
   print "Key: %s " % env.this_key
   print_dict(env.this_instance[env.this_key])

   

@task
def instances_full():
   instances = _describe_instances()
   for inst in instances: 
      print inst

@task
def list_inst_full():
   get_instance()
   print "\n\nListing All Instance Information on Instance: %s:  %s" % (env.this_instance['Num'],env.this_instance['InstanceId'])
   print_dict(env.this_instance)


@task
def instances_summary():
   instances = _describe_instances()
   
   summary = "Instances Summary: \n"
   summary += "Num\tInstance Id\tImage Id\tInst Type\tStatus\tPrivate IP\tPublic IP\tVPC Id      \tKey\tZone\n"
   for inst in instances :
      public="NULL     "
      private="NULL     "
      if 'PublicIpAddress' in inst:
         public=inst['PublicIpAddress']
      if 'PrivateIpAddress' in inst:
         private=inst['PrivateIpAddress']
      sec_groups=""
      for group in inst['SecurityGroups']:
         sec_groups+=group['GroupName']
      keys=""
      for key in inst['KeyName']:
         keys+=key

      summary += "%s\t" % (inst['Num'])
      summary += "%s\t%s\t" % (inst['InstanceId'], inst['ImageId'])
      summary += "%s\t%s\t" % (inst['InstanceType'], inst['State']['Name'])
      summary += "%s\t%s\t" % (private, public)
      summary += "%s\t" % (inst['VpcId'])
      summary += "%s\t%s\t" % (keys,inst['Placement']['AvailabilityZone'])
      summary +="\n"
   print summary

@task
def list_inst_tags():
   get_instance()
   print "\n\nListing Tags on Instance: %s:  %s" % (env.this_instance['Num'],env.this_instance['InstanceId'])
   for tag in env.this_instance['Tags']: 
      print "%s => %s" % (tag['Key'],tag['Value']) 

@task
def list_inst_sec():
   get_instance()
   print "\n\nListing Security Groups on Instance: %s:  %s " % (env.this_instance['Num'],env.this_instance['InstanceId'])
   for sec in env.this_instance['SecurityGroups']: 
      print "%s => %s" % (sec['GroupId'],sec['GroupName']) 

