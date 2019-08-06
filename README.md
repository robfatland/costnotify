# costnotify

We build an AWS lambda function *costnotify* that produces a cost breakdown for the parent account. This breakdown is sent 
to an email distribution where the email subject is the spend over the past 24 hours. The email body includes further detail.


The source code we maintain here is in the `costnotify.py` file. This could either be uploaded as a `tar` file or copy-pasted into
the AWS lambda code window. An earlier draft also retained here is the file `analysis.py`.  
Instructions for building out the costnotify lambda function are found in the `instructions` folder. 
As a resource: The `original_code` folder contains the source code for an earlier version of costnotify. 

Some additional considerations...

- Our first motive for building costnotify is to see yesterday's AWS cloud spend today
  - This acts as a convenient safety check at-a-glance: Make sure something hasn't gone awry
- Further motivation is to help track grantee spend versus grant budget
- Good practice: Don't put a billing file in this repo
- Good practice: Use AWS Roles rather than Access Keys
- Development: You can work in the AWS console to iteratively develop this code
- Updating this repo: Copy-paste from the AWS console code box to here
- You can also work from a clone of this repo and develop code locally, for example...
  - Install Miniconda per Lesson 1 [here](https://carpentrieslab.github.io/python-aos-lesson/)
- Good practice: Use the Python `csv` package as shown in the `analysis.py` program 


There are four AWS services attached to the costnotify lambda function:


* CloudWatch Events set to trigger the costnotify lambda every day (like an alarm clock)
* S3 bucket `copydbr-<account_identifier>` where monthly billing itemization CSV files are stored
  * Accumulation courtesy of CloudCheckr 
* CloudWatch Logs is a little unclear so this gets a flag for future clarification
  * It does seem to associate with a Role with three associated Policies...
* SNS Simple Notification Service to distribute costnotify emails to recipients


## Specific to this version of costnotify...


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
