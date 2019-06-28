# original
# import json
# def lambda_handler(event, context):
    # TODO implement
    # print('test 1')
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps('Hello from Lambda!')
    # }


import json
import os
import boto3
import zipfile
import csv
import datetime
import urllib

accountnumber = os.environ['accountnumber']
dayintervalStart = os.environ['dayintervalStart']
dayintervalEnd = os.environ['dayintervalEnd']
emailsubject = os.environ['emailsubject']

### choose which file(s) to parse
'''
    Pick up the most recently updated file
    cassandra says there is some broken logic here: Which files based on day of month and time-ago range
    should be fixed to reflect an arbitrary time range
'''
def FilePicker(contents_list):
    file_list, update_dt = [], []
    for con in contents_list:
        file_name = con['Key'].split('.')
        file_time = con['LastModified']
        print(file_name)
        if file_name[-1] == 'zip':
            file_list.append(con['Key'])
            update_dt.append(con['LastModified'].timestamp())
        if len(file_list) > 0: break
    # update_dt = sorted(update_dt)
    # current_d = datetime.datetime.utcnow().today().day
    # if current_d <= 6:
    #     idx1, idx2 = update_dt.index(update_dt[-1]), update_dt.index(update_dt[-2])
    #     file_picked = [file_list[idx1], file_list[idx2]]
    # else:
    #     idx = update_dt.index(update_dt[-1])
    #     file_picked = [file_list[idx]]
    return file_list[0]




# this method is called by the outside world. The original 'event' was used to fuel the logic but it is better
#   to have no dependency so it is autonomous and easy to test
def lambda_handler(event, context):
    '''
    parse cost info and send cost summary to SNS > email notifications
    ---
    arg:    
        1, list event
        2, list context
    return:
        None
    '''
    print('dailyspendemail lambda event handler starting')
    s3 = boto3.client('s3')
    bucketName = 'copydbr-czar'

    try:
        csv_file_list = s3.list_objects(Bucket = bucketName)
        s3_resource = boto3.resource('s3')
        key = csv_file_list['Contents'][1]['Key']
        print(type(key))
        
        # flag should return a list not a string!
        some_test_file = FilePicker(csv_file_list['Contents'])
        
        
        yearOfFile = '2019'
        monthOfFile = '02'
        bucketName = 'copydbr-czar'

        s3_resource = boto3.resource('s3')
        f = accountnumber +                                                   \
            '-aws-billing-detailed-line-items-with-resources-and-tags-' +     \
            yearOfFile + '-' + monthOfFile + '.csv.zip'
        s3_resource.Object(bucketName, f).download_file('/tmp/' + f)        # copy of file local to the lambda environment
        zip_ref = zipfile.ZipFile('/tmp/'+ f, 'r')
        zip_ref.extractall('/tmp/')
        csv_filename = f.split('.')[0]+'.csv'
        # with open('/tmp/' + csv_filename, 'r', newline = '\n') as csvfile:
            # lines = csv.reader(csvfile, delimiter=',', quotechar='"')
            # for idx, line in enumerate(lines):
                # if idx == 0:
                    # col_dict = {}
                    # for i, n in enumerate(line): col_dict.update({n.strip(): i})
                    # get index for tags (user:Name, user:Project)
                    # idx_tag1, idx_tag2, idx_tag3, idx_tag4 = \
                    #     col_dict['user:Owner'], col_dict['user:Project'], col_dict['user:ProjectName'], col_dict['user:Name']
                    # get index for datetime
                    # idx_dt = col_dict['UsageEndDate']
                    # get index for ProductName
                    # idx_pname = col_dict['ProductName']
                    # 'use quantity' has two types: blended and unblended
                    # idx_dollar_blend = col_dict['BlendedCost']
                    # idx_dollar_unblend = col_dict['UnBlendedCost']
                    # for untagged resources
                    # idx_resource = col_dict['ResourceId']
                # else:
                    # parse a line of the file...
                    # x = 0 # and so on         
        
        # Use ComposeMessage() to assemble the body of the email message
        # Using the external var: email_subject = emailsubject
        email_subject = '$1,000,000 ' + emailsubject
        email_body = 'dirt cheap! check out ' + some_test_file + '\n'
        email_body += csv_filename + '\n'
        email_body += str(os.listdir('/tmp/'))
        sns = boto3.client('sns')
        #   SNS topic should match what is set up in SNS
        #   Customize your email Subject using the external variable emailsubject
        #   Customize your return value (string)
        arnString = 'arn:aws:sns:us-east-1:' + accountnumber + ':burn_notify_sns'
        response = sns.publish(TopicArn=arnString, Message=email_body, Subject=email_subject)
        return 'daily spend email lambda completed'
    
    # Last piece of the event handler: something went wrong  
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucketName))
        raise e
