***Status: This is a re-build of an earlier solution. The software is in development (13-AUG-2019) and not yet stable, about 80% of the way to being useful.***


# costnotify

This repo is instructions and code for building an AWS lambda function *costnotify* to send a spending breakdown 
email to selected recipients for an AWS cloud account. Typically the email subject is "how much did I spend in
the past 24 hours" and the email body is further details breaking down cost. 


The lambda code is the file `costnotify.py` in this folder. Our instructions include a copy-paste of this 
code into the code window of the lambda function on the AWS console. There is another method for doing this
using a tar file that we do not cover here.


Other files in this repo such as `prototype.py` and `analysis.py` are older version source material. 
We'll try and keep `costnotify.py` as our best working version.

**Instructions for building out the costnotify lambda function are found in the `instructions` folder.**

Additional considerations...

- Motivation for building **costnotify**: See yesterday's AWS cloud spend today
  - A safety check at-a-glance: Everything is ok
- Further motivation: Track grantee spend versus (say) a grant budget
- Good practice: Don't put a billing file in this repo
- Good practice: Use AWS Roles, ***not*** Access Keys
- Good practice: Use the Python `csv` package... simpler than using pandas :)


There are four AWS services attached to the costnotify Lambda function:


* CloudWatch Events trigger the costnotify lambda (cron)
* S3 bucket: We use name `copydbr-<account_identifier>` billing itemization CSV files from CloudCheckr 
* CloudWatch Logs enables debugging; output of Lambda execution
* SNS (Simple Notification Service) to distribute the **costnotify** message to subscribers

## AWS Billing Notebook

A notebook to act as an interactive extension of costnotify and mirror the methods used on the
<a href="https://github.com/pangeo-data/gcp-billing">
	Google Cloud Platform
</a>
side of Pangeo. The notebook should be runnable for anyone on the us-east-1 Pangeo JupyterHub. It should also be usable for anyone who has configured the AWS CLI and is an admin on the project.

Running the notebook as-is will find all the billing files in the bucket and download all of them. There is a possibility that they could just be read into memory and worked with there, but downloading is easier for now.

There are a few convenient functions in the notebook for common visualizations: cost by day and cost by month. There is also a line of code to show a table of itemized costs over the time period you select.

## Prep


Within a candidate account: Check the S3 listing for N.Virginia to identify the logging bucket. 
In our case this bucket has a name that begins with `copydbr-`. The bucket should contain monthly 
billing itemization files. 

- Billing files are in `.zip` format
- `blended cost` seems to be the right source for comparison with invoicing
- tagging suggest auto-tagging by IAM User
- A 28-day spend by User would be helpful
- Crossing month and/or year boundaries implies mining multiple CSV files
- Be sure to accommodate UTC versus local (e.g. PDT is -7 hrs, PST is -8 hrs)
