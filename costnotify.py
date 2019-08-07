import json
import os
import boto3
import zipfile
import csv
import datetime
import urllib

accountnumber = os.environ['accountnumber']
bucketname = os.environ['bucketname']
snstopic = os.environ['snstopic']
dayintervalStart = os.environ['dayintervalStart']
dayintervalEnd = os.environ['dayintervalEnd']

'''
Here is the indexing for the 25 columns of the CSV billing file:

'InvoiceID': 0
'PayerAccountId': 1
'LinkedAccountId': 2
'RecordType': 3
'RecordId': 4
'ProductName': 5
'RateId': 6
'SubscriptionId': 7
'PricingPlanId': 8
'UsageType': 9
'Operation': 10
'AvailabilityZone': 11
'ReservedInstance': 12
'ItemDescription': 13
'UsageStartDate': 14
'UsageEndDate': 15
'UsageQuantity': 16
'BlendedRate': 17
'BlendedCost': 18
'UnBlendedRate': 19
'UnBlendedCost': 20
'ResourceId': 21
'user:Name': 22
'user:Owner': 23
'user:Project': 24
'''

### choose which file(s) to parse
def FileChoice(contents_list):
    
    # "now" is datetime.datetime.now()
    
    # establish two lists: filenames and the time that each was last updated (seconds since 1970!)
    filelist, updateTime = [], []
    for element in contents_list:
        filename = element['Key'].split('.')    # a printable 3-element list: <long-filename>, '.csv', '.zip'
        filetime = element['LastModified']
        if filename[-1] == 'zip':
            filelist.append(element['Key'])
            updateTime.append(element['LastModified'].timestamp())     # Verified: len(filelist) is equal to len(updateTime)

    # this could be expanded to a list of files if we are at a month or year boundary right now
    return filelist[-1]




# this function is the "main program", called whenever the Lambda runs.
def lambda_handler(event, context):
    '''
    parse cost info and send cost summary to SNS > email notifications
    ---
    arg:    
        1, list event
        2, list context
    return:
        report string
    '''
    print('costnotify lambda event handler start')

    # a bucket object we will use to access the billing log files
    s3 = boto3.client('s3')

    try:
        # the S3 bucket 'bucketname' contains the billing files
        csv_file_list = s3.list_objects(Bucket = bucketname) # ...a list of dictionaries, one per monthly log file
        s3_resource = boto3.resource('s3')
        key = csv_file_list['Contents'][1]['Key']    # this is a string
        
        # flag this will need attention on month/year boundaries
        fileChosen = FileChoice(csv_file_list['Contents'])
        
        yearOfFile = '2019'
        monthOfFile = '08'
        fileDesignated = accountnumber +                                      \
            '-aws-billing-detailed-line-items-with-resources-and-tags-' +     \
            yearOfFile + '-' + monthOfFile + '.csv.zip'
            
        # copy the billing file and unzip it so it can be read
        s3_resource.Object(bucketname, fileDesignated).download_file('/tmp/' + fileDesignated)   # copy from S3 to local
        zip_ref = zipfile.ZipFile('/tmp/'+ fileDesignated, 'r')
        zip_ref.extractall('/tmp/')
        csv_filename = fileDesignated.split('.')[0]+'.csv'
        
        # prepare to get the column headers by creating an empty dictionary
        column_dictionary = {}
        blended_cost = []
        bill_timestamps = []
        bill_sum = 0.
        
        with open('/tmp/' + csv_filename, 'r', newline = '\n') as csvfile:
            lines = csv.reader(csvfile, delimiter=',', quotechar='"')
            
            for idx, line in enumerate(lines):
                
                # this code pulls out the column names and maps them to integers
                #   refer to the comment at the top of this file for the results
                if idx == 0:
                    for i, n in enumerate(line): column_dictionary.update({n.strip(): i})
                    
                    # This is old code from the prior version...
                    #
                    # get index for tags (user:Name, user:Project)
                    # idx_tag1, idx_tag2, idx_tag3, idx_tag4 = \
                    #     column_dictionary['user:Owner'], column_dictionary['user:Project'], column_dictionary['user:ProjectName'], column_dictionary['user:Name']
                    # get index for datetime
                    # idx_dt = column_dictionary['UsageEndDate']
                    # get index for ProductName
                    # idx_pname = column_dictionary['ProductName']
                    # 'use quantity' has two types: blended and unblended
                    # idx_dollar_blend = column_dictionary['BlendedCost']
                    # idx_dollar_unblend = column_dictionary['UnBlendedCost']
                    # for untagged resources
                    # idx_resource = column_dictionary['ResourceId']
                    
                else:
                    # Here we should be using "yesterday" logic: Only add up items billed to yesterday
                    bill_sum += float(line[18])
                    if idx < 6:
                        blended_cost.append(float(line[18]))
                        bill_timestamps.append(line[15])
        
        # Use ComposeMessage() to assemble the body of the email message
        email_subject = '$' + str(bill_sum) + ' AWS Czar'
        email_body    = '...parsing ' + fileDesignated + '\n'
        email_body   += 'bill total is ' + str(bill_sum) + '\n'
        email_body   += str(bill_timestamps) + '\n\n\n'
        
        # This is a faster way to debug (you don't wait for email_body to arrive via email)
        print(email_body)
        
        # "publish to SNS Topic" translates to "send email to the SNS distribution list"    
        sns           = boto3.client('sns')
        arnstring     = 'arn:aws:sns:us-east-1:' + accountnumber + ':' + snstopic
        response      = sns.publish(TopicArn=arnstring, Message=email_body, Subject=email_subject)

        return 'costnotify lambda completed (' + \
               str(response['ResponseMetadata']['HTTPStatusCode']) + \
               ') on ' + \
               response['ResponseMetadata']['HTTPHeaders']['date']
    
    # ...this runs if something went wrong  
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}'.format(key, bucketname))
        raise e
