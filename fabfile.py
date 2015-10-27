from fabric.api import*
import boto3
import time
import rlcompleter, readline
readline.parse_and_bind('tab:complete')
import sys
from spur import SshShell
from boto3 import session

env.key_filename = ["~/.ssh/fabtest.pem"]


def hook_ssh(class_attributes, **kwargs):
    def run(self, command):
        '''Run a command on the EC2 instance via SSH.'''

        userid = ['ec2-user','ubuntu','root']
        # Create the SSH client.
        while not hasattr(self, '_ssh_client'):
            this_user = userid.pop()
            try: 
               self._ssh_client = SshShell(self.public_ip_address, this_user)
            except :
               print "Unexpected error:", sys.exc_info()[0]
               raise

        print(self._ssh_client.run(command).output.decode())

    class_attributes['run'] = run



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


def get_ec2_client():
   client = boto3.client('ec2')

   if 'client' not in env:
      client = boto3.client('ec2')
      if client is not None: 
         env.client = client
         print "Connected to EC2" 
      else:
         msg = "Unable to connect to EC2 client "
         raise IOError(msg)
   return env.client

def get_ec2_res():
   res = boto3.resource('ec2')

   if 'res' not in env:
      res = boto3.resource('ec2')
      if res is not None: 
         env.res = res
         print "Connected to EC2 resource" 
      else:
         msg = "Unable to connect to EC2"
         raise IOError(msg)
   return env.res





def describe_instances():
   client = get_ec2_client()
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
   inst_summary()
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
def inst_key_detail():
   get_instance()
   get_key()
   print "\n\nInstance: %s:  %s" % (env.this_instance['Num'],env.this_instance['InstanceId'])
   print "Key: %s " % env.this_key
   print_dict(env.this_instance[env.this_key])


@task
def inst_full_all():
   instances = describe_instances()
   for inst in instances: 
      print inst

@task
def inst_full_info():
   get_instance()
   print "\n\nListing All Instance Information on Instance: %s:  %s" % (env.this_instance['Num'],env.this_instance['InstanceId'])
   print_dict(env.this_instance)


@task
def inst_summary():
   instances = describe_instances()
   
   summary = "Instances Summary: \n"
   summary += "Num\tInstance Id\tImage Id\tInst Type\tStatus\tPrivate IP\tPublic IP\tVPC Id      \tKey\tZone\n"
   for inst in instances :
      public="NULL     "
      private="NULL     "
      vpcId="NULL    "
      if 'PublicIpAddress' in inst:
         public=inst['PublicIpAddress']
      if 'PrivateIpAddress' in inst:
         private=inst['PrivateIpAddress']
      if 'VpcId' in inst:
         vpcId=inst['VpcId']

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
      
      summary += "%s\t" % (vpcId)
      summary += "%s\t%s\t" % (keys,inst['Placement']['AvailabilityZone'])
      summary +="\n"
   print summary

@task
def inst_tags():
   get_instance()
   print "\n\nListing Tags on Instance Num: %s:  %s" % (env.this_instance['Num'],env.this_instance['InstanceId'])
   for tag in env.this_instance['Tags']: 
      print "%s => %s" % (tag['Key'],tag['Value']) 

@task
def inst_sec_group():
   get_instance()
   print "\n\nListing Security Groups on Instance Num: %s:  %s " % (env.this_instance['Num'],env.this_instance['InstanceId'])
   for sec in env.this_instance['SecurityGroups']: 
      print "%s => %s" % (sec['GroupId'],sec['GroupName']) 

@task
def inst_start():
   get_instance()
   print "\n\nStarting Instance: %s:  %s " % (env.this_instance['Num'],env.this_instance['InstanceId'])
   if env.this_instance['State']['Name'] == 'stopped':
      client = get_ec2_client()
      resp = client.start_instances(InstanceIds=[env.this_instance['InstanceId']])
      if resp['ResponseMetadata']['HTTPStatusCode']==200 : 
         print "OK Response on Start Command: %s  " % (resp['ResponseMetadata']['HTTPStatusCode'])
         print "Instance is now: %s  " % (resp['StartingInstances'][0]['CurrentState']['Name'])
      else: 
         print "\n\nBad Response on Start Command: %s  " % (resp['ResponseMetadata']['HTTPStatusCode'])
   else :
      print "Commmand aborted - bad status on Instance Num: %s:  %s (%s) " % (env.this_instance['Num'],env.this_instance['InstanceId'], 
            env.this_instance['State']['Name'])
      print "Instance should be stopped before running start command."

@task
def inst_stop():
   get_instance()
   print "\n\nStopping Instance: %s:  %s " % (env.this_instance['Num'],env.this_instance['InstanceId'])
   if env.this_instance['State']['Name'] == 'running':
      client = get_ec2_client()
      resp = client.stop_instances(InstanceIds=[env.this_instance['InstanceId']])
      if resp['ResponseMetadata']['HTTPStatusCode']==200 : 
         print "OK Response on Start Command: %s  " % (resp['ResponseMetadata']['HTTPStatusCode'])
         print "Instance is now: %s  " % (resp['StoppingInstances'][0]['CurrentState']['Name'])
      else: 
         print "\n\nBad Response on Start Command: %s  " % (resp['ResponseMetadata']['HTTPStatusCode'])
   else :
      print "Commmand aborted - bad status on Instance Num: %s:  %s (%s) " % (env.this_instance['Num'],env.this_instance['InstanceId'], 
            env.this_instance['State']['Name'])
      print "Instance should be running to run stop command."

def get_login(inst) :
   b3s = session.Session()
   res = b3s.resource('ec2')
   # Hook the "run" method to the "ec2.Instance" resource class.
   b3s.events.register('creating-resource-class.ec2.Instance', hook_ssh)

   uname = res.Instance(inst['InstanceId']).run("uname -a")
   print "Uname is: %s " % uname
   return "stuff"



@task
def scp_to_inst():
   get_instance()
   if env.this_instance['State']['Name'] == 'running':

      priv_ip=""
      pub_ip=""
      nat=False
      for interfaces in env.this_instance['NetworkInterfaces'] :
         print_dict(interfaces)
         if 'PrivateIpAddresses' in interfaces:
            priv_ip = interfaces['PrivateIpAddresses'][0]['PrivateIpAddress']
         if 'Association' in interfaces:
            pub_ip = interfaces['Association']['PublicIp']
    
      def valid_choice(input):
         choice = int(input)
         if not choice in range(1, len(env.instances) + 1):
            raise ValueError("%d is not a valid choice" % choice)
         return choice -1

      if pub_ip == "":
         nat=True
         pub_prompt = "Please choose a public NAT instance: "
         choice=prompt(pub_prompt, validate=valid_choice)
         pub_instance  = env.instances[choice]
         for interface in pub_instance['NetworkInterfaces'] :
            print_dict(interface)
            if 'Association' in interface:
               pub_ip = interface['Association']['PublicIp']

      pub='ec2-user'
      priv = 'ubuntu'

      local_prompt = "Please enter local_dir: "
      remote_prompt = "Please enter remote_dir: "

      def validation(input): 
        dir=(input)
        return dir
        
      local_dir = prompt(local_prompt, validate=validation)
      remote_dir = prompt(remote_prompt, validate=validation)

      if nat: 
         cmd = 'scp -o ProxyCommand=\"ssh {pub}@{pub_ip} nc {priv_ip} 22\" -r {local_dir} {priv}@{priv_ip}:/{remote_dir}'.format(**vars())
      else: 
         cmd = 'scp -r {local_dir} {pub}@{pub_ip}:/{remote_dir}'.format(**vars())
      print cmd
      local(cmd)

   else :
      print "Commmand aborted - bad status on Instance Num: %s:  %s (%s) " % (env.this_instance['Num'],env.this_instance['InstanceId'], 
            env.this_instance['State']['Name'])
      print "Instance must be running to sync data."
   


