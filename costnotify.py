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
friendlyaccountname = os.environ['friendlyaccountname']
daysbackfromtoday = os.environ['daysbackfromtoday']

# for monthly analysis
override = os.environ['override']
monthOverride = os.environ['monthOverride']
yearOverride = os.environ['yearOverride']


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
    BlendedCostIndex  = 18
    UsageEndDateIndex = 15
    ProductNameIndex  =  5
    costByDay     = []                           # Day 0 = 1st dat of the month, etcetera
    datetimeByDay = []                           # datetimes at midnight (Zulu?) for days of the month
    costByService = []                           # Not implemented and should probably be a dictionary, not a list
    nameByService = []

    leapyears = [2000, 2004, 2008, 2012, 2016, 2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048]
    daysPerMonth = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    try:
        
        # the S3 bucket 'bucketname' contains the billing files
        csv_file_list = s3.list_objects(Bucket = bucketname) # ...a list of dictionaries, one per monthly log file
        s3_resource = boto3.resource('s3')
        key = csv_file_list['Contents'][1]['Key']            # this is a string

        # boolean override tells the Lambda to run an entire month (selected in environ vars)
        if override in ['True', 'true', 'TRUE', '1', 'yes', 'Yes', 'YES']:
            monthOverride_int = int(monthOverride)
            yearOverride_int = int(yearOverride)  
            if monthOverride_int < 1 or monthOverride_int > 12: return 'bad month override'
            if yearOverride_int < 2014 or yearOverride_int > 2030: return 'bad year override'
            dayOfMonth = daysPerMonth[monthOverride_int]
            if monthOverride_int == 2 and yearOverride_int in leapyears: dayOfMonth = 29
            endDay = datetime.datetime(yearOverride_int, monthOverride_int, dayOfMonth, 0, 0, 0)
            monthString = '{:02d}'.format(endDay.month)
            yearString = '{:04d}'.format(endDay.year)

        # usual business: generate a report for one day, recent as possible
        else:
            today      = datetime.datetime.now()
            print(today)
            endDay      = today - datetime.timedelta(days = 1)
            dayOfMonth  = endDay.day
            monthString = '{:02d}'.format(endDay.month)
            yearString  = '{:04d}'.format(endDay.year)
            daysbackfromtoday_int = int(daysbackfromtoday)

        # Example 1: override is 'True' and monthOverride is string '4' and yearOverride is string '2019'
        #   Integer values are 4 and 2019. dayOfMonth will be daysPerMonth[4] = 30. endDay will be datetime 30-APR-2019.
        # Example 2: Today is September 14 2019
        #   endDay = yesterday's date (a datetime) so dayOfMonth = 13
        # In both cases the range(0, dayOfMonth) will index 0, 1, 2, ..., dayOfMonth - 1
        for i in range(dayOfMonth):
            datetimeByDay.append(endDay - datetime.timedelta(days = dayOfMonth - i))
            costByDay.append(0.)

        monthlyBillingFile = accountnumber +                                  \
            '-aws-billing-detailed-line-items-with-resources-and-tags-' +     \
            yearString + '-' + monthString + '.csv.zip'
            
        # copy the billing file and unzip it so it can be read
        s3_resource.Object(bucketname, monthlyBillingFile).download_file('/tmp/' + monthlyBillingFile)   # from S3 to local
        zip_ref = zipfile.ZipFile('/tmp/'+ monthlyBillingFile, 'r')
        zip_ref.extractall('/tmp/')
        csv_filename = monthlyBillingFile.split('.')[0]+'.csv'
        
        # prepare to get the column headers by creating an empty dictionary
        column_dictionary = {}
        monthBill = 0.
        nTotalItems = 0
        
        print("compare: daily cost list has length =", len(costByDay), 'versus day of month =', dayOfMonth)
        
        # if not len(costByDay) == dayOfMonth: 
        #     return("logic fail nDaysInferred vs dayOfMonth: " + str(len(costByDay)), dayOfMonth)
        
        with open('/tmp/' + csv_filename, 'r', newline = '\n') as csvfile:
            lines = csv.reader(csvfile, delimiter=',', quotechar='"')
            
            for idx, line in enumerate(lines):
                
                # For the first row: map column labels to integers
                #   see the extended comment at top of this file
                if idx == 0:
                    for i, n in enumerate(line): column_dictionary.update({n.strip(): i})
                    
                # otherwise accrue this cost to the total monthly bill and daily itemization
                else:
                    # by date aggregator
                    nTotalItems += 1
                    itemCost = float(line[BlendedCostIndex])
                    monthBill += itemCost
                    itemEndTime = datetime.datetime.strptime(line[UsageEndDateIndex], '%Y-%m-%d %H:%M:%S')
                    itemDayIndex = int(itemEndTime.day) - 1
                    
                    # name aggregate by product type
                    thisProductName = line[ProductNameIndex]
                    if thisProductName in nameByService:
                        thisProductIndex = nameByService.index(thisProductName)
                        costByService[thisProductIndex] += itemCost
                    else:
                        nameByService.append(thisProductName)
                        costByService.append(itemCost)

                    if itemDayIndex >= len(costByDay):
                        print("logic error: item exceeds allowed day range")
                        print('day index, len(cost list):', itemDayIndex, len(costByDay))
                        print('item end time:', itemEndTime)
                        print('final available datetime for month:', datetimeByDay[-1])
                        
                    else: costByDay[itemDayIndex] += itemCost 
                        
        print("Cost entries:", nTotalItems)
        
        # We want to sum yesterday... but cloudcheckr accumulation is accurate only after 2 or 3 days.
        #   This code tries to look as recently as possible using the environmental variable 'daysbackfromtoday'.
        #     The Lambda seems to work well with value 3; and possibly value 2. Serious doubt about value = 1.
        #   At the moment if we are too close to the start of the month this just gives up and returns zero.
        if dayOfMonth < daysbackfromtoday_int: mostRecentDayBill = 0.           
        else:                                  mostRecentDayBill = costByDay[dayOfMonth - daysbackfromtoday_int]

        mostRecentDayBillString = '%.2f' % mostRecentDayBill
        monthBillString = '%.2f' % monthBill
        
        # Use ComposeMessage() to assemble the body of the email message
        email_subject = '$' + mostRecentDayBillString  + ' AWS ' + friendlyaccountname
        email_body    = 'Month ' + monthString + ' ' + yearString + ' $' + monthBillString + '\n\nBy day:\n\n'
        for idx, entry in enumerate(costByDay): email_body += str(idx + 1) + ', ' + '%.2f' % entry + '\n'
        email_body += '\n\n'
        
        email_body += 'Cost by service/product:\n\n'
        for idx, entry in enumerate(costByService): email_body += nameByService[idx] + ', ' + '%.2f' % entry + '\n'
        email_body += '\n\n'
        email_body += 'total items so far for this month: ' + str(nTotalItems) + '\n'
        email_body += '\n\n'
       
        # for debugging in the console...
        print(email_subject + '\n\n' + email_body)
        
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
