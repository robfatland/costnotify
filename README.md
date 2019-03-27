# costnotify

This repo is an AWS Lambda function written in Python that sends billing notifications to AWS account managers via email. 
It was originally built to operate on DLT-supplied cost logging. As that has proven sporadic we are re-writing it to work
against hourly billing records accumulated by "CloudChekr" in an S3 bucket called copydbr.

## Warning on data and on roles versus variables versus keys

- Don't put the billing file in this repo; it could contain info we don't want public
  - Rather suggest create an above-repo directory called ../billingdata
  

## Motivation


## Set up the bucket and the IAM User 


## File name

- Cover file naming convention
- Cover opening and reading from a .zip file

## Coding contest

- Rob versus Kara versus possibly Madeleine
- Objective: Open the file, print who and how much for the month of February
  - Bonus objective: 28-day spend plots by User
  - Bonus use two time parameters to do a time window version of this
  - Bonus compensate for UTC (PDT is -7 hrs, PST is -8 hrs)
