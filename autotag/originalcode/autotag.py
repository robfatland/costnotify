from __future__ import print_function
import json
import boto3
import logging
import time
import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    #logger.info('Event: ' + str(event))
    #print('Received event: ' + json.dumps(event, indent=2))

    ids = []
    idc = ''
    ide = ''

    try:
        region = event['region']
        detail = event['detail']
        eventname = detail['eventName']
        arn = detail['userIdentity']['arn']
        principal = detail['userIdentity']['principalId']
        userType = detail['userIdentity']['type']
        accountID = '509248752274'
        
        if userType == 'IAMUser':
            user = detail['userIdentity']['userName']

        else:
            user = principal.split(':')[1]


        logger.info('principalId: ' + str(principal))
        logger.info('region: ' + str(region))
        logger.info('eventName: ' + str(eventname))
        logger.info('detail: ' + str(detail))

        ec2 = boto3.resource('ec2')
        rds = boto3.client('rds')
        # s3 = boto3.resource('s3')
        client = boto3.client('s3')

        if eventname == 'CreateVolume':
            ids.append(detail['responseElements']['volumeId'])
            logger.info(ids)

        elif eventname == 'RunInstances':
            items = detail['responseElements']['instancesSet']['items']
            for item in items:
                ids.append(item['instanceId'])
            logger.info(ids)
            logger.info('number of instances: ' + str(len(ids)))

            base = ec2.instances.filter(InstanceIds=ids)

            #loop through the instances
            for instance in base:
                for vol in instance.volumes.all():
                    ids.append(vol.id)
                for eni in instance.network_interfaces:
                    ids.append(eni.id)

        elif eventname == 'CreateImage':
            ids.append(detail['responseElements']['imageId'])
            logger.info(ids)

        elif eventname == 'CreateSnapshot':
            ids.append(detail['responseElements']['snapshotId'])
            logger.info(ids)
        
        elif eventname == 'CreateDBInstance':
            idc = 'arn:aws:rds:' + region + ':' + accountID + ':db:' + detail['requestParameters']['dBInstanceIdentifier'].lower() #arn:aws:rds:us-east-1:509248752274:db:affafafafaa
            logger.info(idc)
            
        elif eventname == 'CreateBucket':
            ide = detail['requestParameters']['bucketName']
           # bucket_tagging = s3.BucketTagging(ide)
            logger.info(ide)
            
        else:
            logger.warning('Not supported action')

        if ids:
            for resourceid in ids:
                print('Tagging resource ' + resourceid)
            
            instances = []
            for status in ec2.meta.client.describe_instance_status()['InstanceStatuses']:
                instances.append(status['InstanceId'])

            def filterInstances(instances):
                filtertemplate = [{'Name': 'resource-id','Values': instances}]
                return filtertemplate

            for instance in instances:
                tags = ec2.meta.client.describe_tags(Filters=filterInstances(instances))
            
            print(tags)
            print(ids)
            # for index, item in enumerate(my_list):
            for index, tag in enumerate(tags['Tags']):
                if tag['Key'] != 'Project' or tag['Key'] != 'End_date' or tag['Key'] != 'Name':
                    print ('SNS ready')
                    sns = boto3.client('sns', aws_access_key_id='AKIAJ44UJ2M35FLFUJPQ', aws_secret_access_key='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')
                    response = sns.publish(
                        TopicArn='arn:aws:sns:us-east-1:509248752274:Autotag',
                        Message= user + '(' + principal + ') did not include Name, Project and End_date tags tags in ' + ','.join(ids) + '. Please add these tags asap. Thanks!',
                        Subject='AutoTag Alert'
                    )
                if index == 1:
                    break
            ec2.create_tags(Resources=ids, Tags=[{'Key': 'Owner', 'Value': user}, {'Key': 'PrincipalId', 'Value': principal}])
        elif idc:
            response = rds.list_tags_for_resource(ResourceName=idc)
            for index, tag in enumerate(response['TagList']):
                if tag['Key'] != 'Project' or tag['Key'] != 'End_date' or tag['Key'] != 'Name':
                    print ('SNS ready')
                    sns = boto3.client('sns', aws_access_key_id='AKIAJ44UJ2M35FLFUJPQ', aws_secret_access_key='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')
                    response = sns.publish(
                        TopicArn='arn:aws:sns:us-east-1:509248752274:Autotag',
                        Message= user + '(' + principal + ') did not include Name, Project and End_date tags in ' + idc + '. Please add these tags asap. Thanks!',
                        Subject='AutoTag Alert'
                    )
                if index == 1:
                    break
            print(response)
            rds.add_tags_to_resource(ResourceName=idc, Tags=[{'Key': 'Owner', 'Value': user}, {'Key': 'PrincipalId', 'Value': principal}])    
        elif ide:
            client.put_bucket_tagging(
                Bucket=ide,
                Tagging={
                    'TagSet': [
                        {
                            'Key': 'Owner',
                            'Value': user
                        },
                        {
                            'Key': 'PrincipalId',
                            'Value': principal
                        },
                    ]
                }
            )
            response = client.get_bucket_tagging(
                Bucket=ide
            )
            for index, tag in enumerate(response['TagSet']):
                if tag['Key'] != 'Project' or tag['Key'] != 'End_date' or tag['Key'] != 'Name':
                    print ('SNS ready')
                    sns = boto3.client('sns', aws_access_key_id='X', aws_secret_access_key='X')
                    response = sns.publish(
                        TopicArn='arn:aws:sns:us-east-1:509248752274:Autotag',
                        Message= user + '(' + principal + ') did not include Name, Project and End_date tags in ' + ide + '. Please add these tags asap. Thanks!',
                        Subject='AutoTag Alert'
                    )
                if index == 1:
                    break
        logger.info(' Remaining time (ms): ' + str(context.get_remaining_time_in_millis()) + '\n')
        return True
    except Exception as e:
        logger.error('Something went wrong: ' + str(e))
        return False
