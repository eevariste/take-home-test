#!/usr/bin/env python3

import boto3
import yaml
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='Launch single EC2 Instance according to config file.')
    parser.add_argument('--config','-c',required=False,help='YAML formatted config file. If not specified defaults to config.yml',default="config.yml")
    parser.add_argument('--subnetid','-s',required=False,help='Launches EC2 into specified subnet. If not specified will attempt to use the default VPC if one is present')
    args = parser.parse_args()
    stream = open(args.config,"r")
    config = yaml.load(stream,Loader = yaml.FullLoader)
    
    session = boto3.session.Session()
    ec2_client = session.client('ec2')
    
    ami_name = '{}-ami-hvm-*'.format(config['server']['ami_type'])
    ami_arch = config['server']['architecture']
    ami_root = config['server']['root_device_type']
    ami_virt = config['server']['virtualization_type']
    
    response = ec2_client.describe_images(
            Owners=['amazon'],
            Filters=[
                {
                    'Name': 'name',
                    'Values': [ami_name]
                },
                {
                    'Name': 'architecture',
                    'Values': [ami_arch]
                },
                {
                    'Name': 'root-device-type',
                    'Values': [ami_root]
                },
                {
                    'Name': 'virtualization-type',
                    'Values': [ami_virt]
                }
            ]
            )
    sorted_images = sorted(response['Images'],key=lambda x: x['CreationDate'])
    image_id = sorted_images[-1]['ImageId']
    
    ec2_resource = session.resource('ec2')
    
    instance_type = config['server']['instance_type']
    min_count = config['server']['min_count']
    max_count = config['server']['max_count']
    logins = ["'" + i['login'] + "'" for i in config['server']['users']]
    ssh_keys = ["'" + i['ssh_key'] + "'" for i in config['server']['users']]
    
    # remove root volume if specified
    
    idx = 0
    for i in range(len(config['server']['volumes'])):
        if config['server']['volumes'][i]['mount'] == '/':
            idx = i
    del config['server']['volumes'][idx]
    
    devices = ["'" + i['device'] + "'" for i in config['server']['volumes']]
    sizes = ["'" + str(i['size_gb']) + "'"  for i in config['server']['volumes']]
    fstypes = ["'" + i['type'] + "'" for i in config['server']['volumes']]
    mounts = ["'" + i['mount'] + "'" for i in config['server']['volumes']]
    
    userdata = """#!/bin/bash -x 
    
    logins=({})
    ssh_keys=({})
    
    for i in ${{!logins[@]}}; do
        user=${{logins[$i]}}
        key=${{ssh_keys[$i]}}
        
        useradd -m $user
        mkdir /home/$user/.ssh
        chown $user:$user /home/$user/.ssh
        chmod 700 /home/$user/.ssh
        echo "$key $user" >> /home/$user/.ssh/authorized_keys
    done
    
    devices=({})
    sizes=({})
    fstypes=({})
    mounts=({})
    
    for i in ${{!devices[@]}}; do
        device=${{devices[$i]}}
        size=${{sizes[$i]}}
        fstype=${{fstypes[$i]}}
        mountpath=${{mounts[$i]}}
    
        mkdir -p $mountpath
        mkfs -t $fstype $device
        echo "$device $mountpath $fstype defaults 0 0" >> /etc/fstab
        mount $mountpath
    done""".format(
            " ".join(logins), 
            " ".join(ssh_keys),
            " ".join(devices),
            " ".join(sizes),
            " ".join(fstypes),
            " ".join(mounts)
            )

    blockdevicemappings = list()
    for i in range(len(devices)):
        dev_dict = { 
                'DeviceName': devices[i].strip("'"), 
                'Ebs': { 
                    'VolumeSize': int(sizes[i].strip("'")),
                    'DeleteOnTermination': True
                    }
                }
        blockdevicemappings.append(dev_dict)
    
    if args.subnetid:
        instance = ec2_resource.create_instances(
                ImageId=image_id,
                MinCount=min_count,
                MaxCount=max_count,
                InstanceType=instance_type,
                UserData=userdata,
                BlockDeviceMappings=blockdevicemappings,
                SubnetId=args.subnetid)
    else:
        instance = ec2_resource.create_instances(
                ImageId=image_id,
                MinCount=min_count,
                MaxCount=max_count,
                InstanceType=instance_type,
                UserData=userdata,
                BlockDeviceMappings=blockdevicemappings)
    
    print("EC2 instance with id {} created".format(instance))

if __name__ == "__main__":
    sys.exit(main())
