# costnotify

This repo develops an AWS Lambda function written in Python that sends billing notifications to AWS account managers via email. 
It was originally built to operate on DLT-supplied cost logging. As that has proven sporadic we are re-writing it to work
against hourly billing records accumulated by "CloudChekr" in an S3 bucket called copydbr.

## Warnings

- Don't put the billing file in this repo; it could contain info we don't want public
  - Rather suggest create an above-repo directory called ../billingdata
- Use roles rather than Access Keys built into the code for the same reason
  - Rob to translate the procedure from cloudmaven to here

## Motivation

- See yesterday's burn today in an email header
- Track grantee spend versus grant

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
