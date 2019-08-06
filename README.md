# costnotify

We build an AWS lambda function *costnotify* that produces a cost breakdown for the parent account. This breakdown is sent 
to an email distribution where the email subject is the spend over the past 24 hours. The email body includes further detail.


The file we maintain here is called `costnotify.py`. This could either be uploaded as a `tar` file or copy-pasted into
the AWS lambda code window. An earlier draft also retained here is the file `analysis.py`.  


Instructions for building out the costnotify lambda function are found in the `instructions` folder. 


As a resource: The `original_code` folder contains the source code for an earlier version of costnotify. This code worked from
a DLT-generated version of the cost itemization CSV file. DLT is an AWS cloud distributor, in intermediate between the AWS 
cloud and (say) a UW research group. CSV stands for Comma-Separated Value; so a CSV file is a text version of a spreadsheet
where columns are delimited by commas[.](https://github.com/robfatland/ops) 


There are four AWS services attached to the costnotify lambda function:

* CloudWatch Events set to trigger the costnotify lambda every day (like an alarm clock)
* S3 bucket `copydbr-<account_identifier>` where monthly billing itemization CSV files are stored
  * Accumulation courtesy of CloudCheckr 
* CloudWatch Logs is a little unclear so this gets a flag for future clarification
  * It does seem to associate with a Role with three associated Policies...
* SNS Simple Notification Service to distribute costnotify emails to recipients

## Warnings 

- Don't put a billing file in this repo; treat that as private information
- Use roles rather than Access Keys built into the code for the same reason

## Motivation for costnotify

- See yesterday's burn today at a glance 
- Track grantee spend versus grant budget

## Before you begin

- You can work in the AWS console to iteratively develop this code
- Once a new version is built: copy-paste it over the existing version in this repo
- You can also work from a clone of this repo and develop code locally, for example...
  - Install Miniconda per Lesson 1 [here](https://carpentrieslab.github.io/python-aos-lesson/)
- Probably use the Python `csv` package as shown in the `analysis.py` program
  
## Billing bucket and other considerations

Go to the S3 listing for N.Virginia and find a bucket with a name that begins `copydbr-`. Verify that this contains monthly 
billing itemization files. These are zipped so the file extension should be `.zip`. The precise name of this bucket should
be stored as a Lambda environment variable that loads into the code on execution. 

- Reading the file involves dealing with the `.zip` format
- `blended cost` seems to be the right source for comparison with invoicing
- sorting by IAM User and by resource type
- A 28-day spend by User would be helpful
- Crossing month boundaries implies multiple CSV files
- `numpy.datetime64` and `numpy.timedelta64` are useful
- Be sure to accommodate UTC versus local (e.g. PDT is -7 hrs, PST is -8 hrs)
