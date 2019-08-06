# costnotify

We build an AWS lambda function *costnotify* that produces a cost breakdown for the parent account. This breakdown is sent 
to an email distribution where the email subject is the spend over the past 24 hours. The email body includes further detail.


The original code 


The method is to use an AWS Lambda (Python) to parse/digest data from a billing file called

```
111111111111-aws-billing-detailed-line-items-with-resources-and-tags-2019-02.csv.zip
```

The code to open and parse the code is something like this: 

```
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

yearOfFile = '2019'
monthOfFile = '02'
bucketName = 'copydbr-someidentifier'

s3_resource = boto3.resource('s3')
f = accountnumber +                                                   \
    '-aws-billing-detailed-line-items-with-resources-and-tags-' +     \
    yearOfFile + '-' + monthOfFile + '.csv.zip'
s3_resource.Object(bucketName, f).download_file('/tmp/' + f)        # copy of file local to the lambda environment
zip_ref = zipfile.ZipFile('/tmp/'+ f, 'r')
zip_ref.extractall('/tmp/')
csv_filename = f.split('.')[0]+'.csv'
with open('/tmp/' + csv_filename, 'r', newline = '\n') as csvfile:
    lines = csv.reader(csvfile, delimiter=',', quotechar='"')
    for idx, line in enumerate(lines):
        if idx == 0:
            col_dict = {}
            for i, n in enumerate(line): col_dict.update({n.strip(): i})
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
        else:
            # parse a line of the file...
            x = 0 # and so on 
```


record sends billing notifications to AWS account managers via email
[.](https://github.com/robfatland/ops) 
It was originally built to operate on DLT-supplied cost logging. As thathas proven sporadic we are re-writing it to work
against hourly billing records accumulated by "CloudChekr" in an S3 bucket called copydbr.

## Warnings 

- Don't put the billing file in this repo; it could contain info we don't want public
  - Rather suggest create an above-repo directory called ../billingdata
- Use roles rather than Access Keys built into the code for the same reason
  - Rob to translate the procedure from cloudmaven to here

## Motivation

- See yesterday's burn today in an email header
- Track grantee spend versus grant

## Before you begin 

- You will need a working Python environment where you can download the data file and try stuff. 
  - There are three choices available to you
    - Install Anaconda (or Miniconda) for example from Lesson 1 [here](https://carpentrieslab.github.io/python-aos-lesson/)
    - Get a JupyterHub account on Port Cormorack by request sent to Rob
    - Some other path that is not the above two
- You will probably want to work from the Python `csv` package as shown in the `analysis.py` program
  - Again you need:
    - A Python environment
    - The `csv` package installed there
    - The February billing data downloaded from the S3 `copydbr` bucket
  
## Set up the bucket and the IAM User 

- copydbr

## File name

- Cover file naming convention
  - `111122223333-aws-billing-detailed-line-items-with-resources-and-tags-YYYY-MM.cs`
- Cover opening and reading from a .zip file on an S3 bucket

## Coding contest

- Objective: 
  - Open the file e.g. using the `csv` package
  - Check month spend as `blended cost` against actual invoice
  - print Users and how much each spent; == total?
  - Bonus objective: 28-day spend plots by User
    - `numpy.datetime64` and I think `numpy.timedelta64` are useful
  - Bonus use two time parameters to do a time window version of this
  - Bonus compensate for UTC (PDT is -7 hrs, PST is -8 hrs)
