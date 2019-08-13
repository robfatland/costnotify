***Status: This is a re-build of an earlier solution. The software is in development (13-AUG-2019) and not yet stable, not yet useful.***


# costnotify

We build an AWS lambda function *costnotify* that produces a cost breakdown for the parent account. This breakdown is sent 
to an email distribution where the email subject is the spend over the past 24 hours. The email body includes further detail.


The source code we maintain here is in the `costnotify.py` file. AWS does not upload this automatically; 
rather it must be installed via some means. The two methods that are the most immediate work via your 
browser connecting to the AWS 'console', an account management website. Method 1 is to upload a `tar` file 
that contains your code. We don't cover that here. Method two is to simply copy-paste the code into
the AWS Lambda code window. That's what we cover here. 


Some earlier work on putting this together may still reside in this repo with filenames like `prototype.py` 
and/or `analysis.py` and these (flag) should eventually be tidied up once things are working.

**Instructions for building out the costnotify lambda function are found in the `instructions` folder.**
As a resource: The `original_code` folder contains the source code for an earlier version of costnotify.

Additional considerations...

- Motivation for building **costnotify**: See yesterday's AWS cloud spend today
  - A safety check at-a-glance: Everything is ok
- Further motivation: Track grantee spend versus (say) a grant budget
- Good practice: Don't put a billing file in this repo
- Good practice: Use AWS Roles rather than Access Keys
- Development: You can work in the AWS console to iteratively develop this code
- Updating this repo: Copy-paste from the AWS console code box to here
- You can also work from a clone of this repo and develop code locally, for example...
  - Install Miniconda per software carpentry lesson 1 [here](https://carpentrieslab.github.io/python-aos-lesson/)
- Good practice: Use the Python `csv` package as shown in the `analysis.py` program
  - You could also use :) pandas :)


There are four AWS services attached to the costnotify Lambda function:


* CloudWatch Events set to trigger the costnotify lambda every day (like an alarm clock)
* S3 bucket `copydbr-<account_identifier>` where monthly billing itemization CSV files are stored
  * Accumulation courtesy of CloudCheckr 
* CloudWatch Logs enables debugging; it records the output when the Lambda executes
* SNS (Simple Notification Service) distributes the **costnotify** email to recipients


## Specific to this version of costnotify...


Go to the S3 listing for N.Virginia and find a bucket with a name that begins `copydbr-`. If it is not there you
will need to set it up by contacting DLT at OpsCenter at dlt dot com. Once the bucket is in place you should 
verify it contains monthly billing itemization files. 

- Reading a billing file involves dealing with the `.zip` format
- `blended cost` seems to be the right source for comparison with invoicing
- sort by IAM User and by resource type
- A 28-day spend by User would be helpful
- Crossing month and/or year boundaries implies multiple CSV files
- `numpy.datetime64` and `numpy.timedelta64` are useful
- Be sure to accommodate UTC versus local (e.g. PDT is -7 hrs, PST is -8 hrs)
