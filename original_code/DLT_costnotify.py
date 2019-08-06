# last update: September 11, 2018
# authors: Jin Qu, Amanda Tan, Rob Fatland
# programming environment: python3.6
#
# Modify this file for use with your own account by searching for the tag 'kilroy mod'
#
# Background
#   DLT is a distributor for AWS accounts. Assuming you have a DLT version of an AWS. DLT can be notified that you want your 
#   hourly costs written to an S3 bucket. This is done by appending lines/items to a billing file that spans one calendar month. 
#   This file is in zipped CSV format (CSV means comma-separated-values) and must be unzipped before reading its contents. Each 
#   line typically covers one hour.
#  
#   This code...
#     identifies files with relevant timestamped billing lines
#     opens those files and reads through every line looking for timestamps in a desired range (24-hour-period 2 days ago)
#         Each line includes a resource type (e.g. EC2 instance) and a cost
#         If the cost line includes an identified Owner of the resource: 
#             Add the cost to that owner's total
#         If not: 
#             Add the cost to a cumulative 'untagged' sum
#     creates an email message body with a readable summary of all of this
#         the first line is total = tagged + untagged costs
#     sense email via AWS Simple Notification Service (SNS)
# 
#   This code has been cleaned up: It does not make use of secret access keys; hence it can be shared as-is publicly. 
#     It does make use of an environment variable to recover the 12-digit account number.
#   
#   Do not set the time interval to the past 24 hours without verifying. In our experience there is some cost reporting latency
#     that will produce inaccurate results. Furthermore after you have allowed this Lambda to run for a few days you should check 
#     the output against the AWS Cost Explorer tool to make sure they are in close agreement (to within a few cents).
#

import json
import os
import boto3
import zipfile
import csv
import datetime
import urllib

print('my AWS cost notify lambda function is starting')

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
        if file_name[-1] == 'zip':
            file_list.append(con['Key'])
            update_dt.append(con['LastModified'].timestamp())
    update_dt = sorted(update_dt)
    current_d = datetime.datetime.utcnow().today().day
    if current_d <= 6:
        idx1, idx2 = update_dt.index(update_dt[-1]), update_dt.index(update_dt[-2])
        file_picked = [file_list[idx1], file_list[idx2]]
    else:
        idx = update_dt.index(update_dt[-1])
        file_picked = [file_list[idx]]
    return file_picked


# check if the line belongs to <time range>
def dayChecker(line_elements, idx_dt, lo_day_bdry, hi_day_bdry):
    '''
    when parsing through the cost info file, this function checks if a certain line contains info of the most recent 24 hrs
    ---
    arg:    
        array line_elements : a line of a csv file
        int idx_dt : the index of datetime
        int lo_day_bdry: days-ago of time range to consider
        int hi_day_bdry: days-ago of time range to consider, other extreme
    return:
        bool  
    '''
    line_dt = line_elements[idx_dt]
    now_dt = datetime.datetime.utcnow()
    time_elapsed = now_dt - datetime.datetime.strptime(line_dt, '%Y-%m-%d %H:%M:%S')
    if lo_day_bdry <= time_elapsed.days <= hi_day_bdry : return True
    return False

### check if the resource is untagged, if true, print a tag, if not, print False
def untaggedChecker(line_elements, idx_tag1, idx_tag2, idx_tag3, idx_tag4):
    '''
    grab tags
    ---
    arg:    
        array line_elements : a line of a csv file
        int idx_tag1-idx_tag4 : the index of tag
    return:
        if there is a tag, return a string of the tag
        if not return bool False
    '''
    # cassandra does not like this code returning mixed types
    if line_elements[idx_tag1]: return line_elements[idx_tag1]
    if line_elements[idx_tag2]: return line_elements[idx_tag2]
    if line_elements[idx_tag3]: return line_elements[idx_tag3]
    if line_elements[idx_tag4]: return line_elements[idx_tag4]
    return False


### aggregate cost by tag and product name
def Agg(line_elements, aggs, tag, idx_pname, idx_dollar_blend, idx_dollar_unblend):
    '''
    aggregate blended and unblended cost by product name
    ---
    arg:    
        array line_elements : a line of a csv file
        dict aggs : a dictionary like this: op op tag1: op cp cp , op tag2: op cp cp , op tag3: op cp cp cp 
        int idx_pname, idx_dollar_blend, idx_dollar_unblend : the index of product name, quantity of blended and unblended cost
    return:
        updated aggs with aggregated cost
    '''
    # product name
    pname = line_elements[idx_pname]
    # cost
    cost_blend = float(line_elements[idx_dollar_blend])
    cost_unblend = float(line_elements[idx_dollar_unblend])
    if tag in aggs:
        aggs[tag]['total_blended_cost'] += cost_blend
        aggs[tag]['total_unblended_cost'] += cost_unblend
        if pname in aggs[tag]:
            aggs[tag][pname]['blended_cost'] += cost_blend
            aggs[tag][pname]['unblended_cost'] += cost_unblend
        else:
            aggs[tag][pname] = {'blended_cost': cost_blend, 'unblended_cost': cost_unblend}
            
    else:
        aggs[tag] = { 'total_blended_cost': cost_blend, 'total_unblended_cost': cost_unblend, pname: { 'blended_cost': cost_blend, 'unblended_cost': cost_unblend } }

### cost aggregation parser for days-ago-based time range
def dailyAgg(file_path, lo_day_bdry, hi_day_bdry):
    '''
    parse through the csv file and generate daily cost summary
    ---
    arg:    
        str file_path : path to the cost file
        lo_day_bdry: days-ago time range to consider
        hi_day_bdry: days-ago time range to consider, other limit
    return:
        an array contains daily cost summary
        1, dict untagged : op op 'resource id 1': $$$ cp , 'resource id 2': $$$ cp;
        2, dict aggs : op op tag1: op cp cp , op tag2: op cp cp , op tag3: op cp cp cp ;
        3, float total_blend;
        4, float total_unblend;
        5, float total_tagged_blend;
        6, float total_tagged_unblend;
        7, float total_untagged_blend;
        8, float total_untagged_unblend
    '''
    untagged, aggs = {}, {}
    total_blend, total_unblend, total_tagged_blend, total_tagged_unblend, \
    total_untagged_blend, total_untagged_unblend = 0, 0, 0, 0, 0, 0
    #start_date = 0

    with open('/tmp/' + file_path, 'r', newline = '\n') as csvfile:
        lines = csv.reader(csvfile, delimiter=',', quotechar='"')
        for idx, line in enumerate(lines):
            if idx == 0:
                col_dict = {}
                for i, n in enumerate(line):
                    col_dict.update({n.strip(): i})
                # get index for tags (user:Name, user:Project)
                idx_tag1, idx_tag2, idx_tag3, idx_tag4 = col_dict['user:Owner'], col_dict['user:Project'], col_dict['user:ProjectName'], col_dict['user:Name']
                # get index for datetime
                idx_dt = col_dict['UsageEndDate']
                # get index for ProductName
                idx_pname = col_dict['ProductName']
                # 'use quantity' has two types: blended and unblended
                idx_dollar_blend = col_dict['BlendedCost']
                idx_dollar_unblend = col_dict['UnBlendedCost']
                # for untagged resources
                idx_resource = col_dict['ResourceId']
            else:
                # avoid parse the last few lines
                if line[idx_pname]:
                    # day boundaries refer to some interval in the past, as in days-ago
                    # lo_day_bdry and hi_day_bdry were traditionally 0 and 0 to give one day of recent results
                    # make them 3 and 4 to look at a two-day range 3 days ago for example
                    if dayChecker(line, idx_dt, lo_day_bdry, hi_day_bdry):
                        tag = untaggedChecker(line, idx_tag1, idx_tag2, idx_tag3, idx_tag4)
                        total_blend += float(line[idx_dollar_blend])
                        total_unblend += float(line[idx_dollar_unblend])
                        if tag:
                            Agg(line, aggs, tag, idx_pname, idx_dollar_blend, idx_dollar_unblend)
                            total_tagged_blend += float(line[idx_dollar_blend])
                            total_tagged_unblend += float(line[idx_dollar_unblend])
                        else:
                            total_untagged_blend += float(line[idx_dollar_blend])
                            total_untagged_unblend += float(line[idx_dollar_unblend])

                            if line[idx_resource] in untagged:
                                untagged[line[idx_resource]]['total_blended_cost'] += float(line[idx_dollar_blend])
                                untagged[line[idx_resource]]['total_unblended_cost'] += float(line[idx_dollar_unblend])
                            else:
                                untagged[line[idx_resource]] = {}
                                untagged[line[idx_resource]]['total_blended_cost'] = float(line[idx_dollar_blend])
                                untagged[line[idx_resource]]['total_unblended_cost'] = float(line[idx_dollar_unblend])
    return [untagged, aggs, total_blend, total_unblend, \
            total_tagged_blend, total_tagged_unblend,total_untagged_blend, total_untagged_unblend]

### method composes an email message body 'msg' to be sent to the cost monitoring team
def ComposeMessage(aggs, untagged, *all_costs):
    '''
    give the cost summary generated by func dailyAgg or weeklyAgg, 
    output a reader-friendly string 
    ---
    arg:    
        1, dict aggs : ...
        2, dict untagged : ...
        3, *all_costs : float total_blend, float total_unblend, float total_tagged_blend, 
                        float total_tagged_unblend, float total_untagged_blend, float total_untagged_unblend
    return:
        str cost_summary
    '''
    total_blend, total_unblend, total_tagged_blend, total_tagged_unblend, \
    total_untagged_blend, total_untagged_unblend = [*all_costs]
    cur_time = datetime.datetime.utcnow()
    
    # dictionary for substituting full name with shorter name
    resource_name_map = {'Amazon Elastic Compute Cloud': 'EC2', 'Amazon Simple Storage Service': 'S3'}
    
    msg = ' '
    msg += 'TOTAL: ${} / ${} / ${} (All/Tagged/Untagged)\n'.format(str(round(total_blend, 2)),\
      str(round(total_tagged_blend, 2)), str(round(total_untagged_blend, 2)))
    
    ### Get usage summary Owner tag:Total
    msg += '\nSUMMARY: \n'
    for k1, v1 in aggs.items():
        msg += '{ID}{spend}\n'.format(ID=k1 + ',', spend='\t$' + str(round(v1['total_blended_cost'], 2)))
    msg += '~ ' * 20 + '\n'
    
    ### Get usage details
    msg += '\n DETAILS: \n'
    for k1, v1 in aggs.items():
        msg += '{tag}{blend}\n'.format(tag=k1 + ',', blend='\t $' + str(round(v1['total_blended_cost'], 2)))
        for k2, v2 in v1.items():
            if k2 not in ['total_blended_cost', 'total_unblended_cost']:
                msg += '{resource} '.format(resource = resource_name_map[k2] if resource_name_map.get(k2) else k2)
                kv3 = list(v2.items())
                msg += '{cost1}\n'.format(cost1 = ': $'+str(round(kv3[0][1], 2)))
    msg += '\nCost with untagged resources: \n' + '~ ' * 10 + '\n'
    for k, v in untagged.items():
        msg += '{id:}'.format(id = k + ',')
        msg += '{blend}\n'.format(blend=' $' + str(round(v['total_blended_cost'], 2)))
    return msg

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
    
    s3 = boto3.client('s3')
    bucketName = accountnumber + '-dlt-utilization'

    try:
        csv_file_list = s3.list_objects(Bucket = bucketName)
        s3_resource = boto3.resource('s3')
        key = csv_file_list['Contents'][1]['Key']
        
        # files_to_parse will be a list of relevant files to scan through
        files_to_parse = FilePicker(csv_file_list['Contents'])
        
        # Take a look at the logs to see if we chose the right files to parse from!
        print(files_to_parse)

        # unzip all the files we need
        for f in files_to_parse:
            s3_resource.Object(bucketName, f).download_file('/tmp/' + f)
            zip_ref = zipfile.ZipFile('/tmp/'+ f, 'r')
            zip_ref.extractall('/tmp/')

        # read and process the most recently updated file
        file_for_daily_agg = files_to_parse[0]

        # set day boundaries form a time range. These are environment variables dayintervalStart and dayintervalEnd.
        #   If they are equal they define a 24-hour period: days-ago, i.e. in the past. As of July 2018 the DLT updates
        #   to the cost-log files in the S3 bucket have some latency; so going closer than 2 days in the past can produce
        #   very inaccurate (low) estimates of daily spend.
        
        # dailyAgg() returns a big tuple of 2 dictionaries and 6 floats (in that order)
        daily_untagged, daily_aggs, daily_total_blend, daily_total_unblend, daily_total_tagged_blend, \
          daily_total_tagged_unblend, daily_total_untagged_blend, daily_total_untagged_unblend = \
          dailyAgg(file_for_daily_agg.split('.')[0]+'.csv', int(dayintervalStart), int(dayintervalEnd))
        
        # Use ComposeMessage() to assemble the body of the email message
        email_body = ComposeMessage(daily_aggs, daily_untagged, daily_total_blend, daily_total_unblend, daily_total_tagged_blend, 
               daily_total_tagged_unblend, daily_total_untagged_blend, daily_total_untagged_unblend)

        sns = boto3.client('sns')

        #   SNS topic should match what is set up in SNS
        #   Import your account number as the external variable accountnumber
        #   Customize your email Subject using the external variable emailsubject
        #   Customize your return value (string)
        arnString = 'arn:aws:sns:us-east-1:' + accountnumber + ':burn_notify_sns'
        response = sns.publish(
            TopicArn=arnString,
            Message=email_body,
            Subject=emailsubject)
        return 'eSci AWS burn notify lambda fn completed'
    
    # Last piece of the event handler: something went wrong  
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucketName))
        raise e
