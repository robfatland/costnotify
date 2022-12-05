## Objective and Supporting Information

Install **`costnotify`** to receive a daily email tracking AWS account spend.
There is also a **Test** mode through the AWS console that will generate and send 
a report for any chosen year/month dating back to when you start this service.
Here are some cloud-oriented aspects of this configuration procedure:

- Consistently use `costnotify` to label resources such as the Lambda function
- Possible interest: [UW CSE Database group AWS page](http://db.cs.washington.edu/etc/aws.html).
- **DLT** is the cloud re-seller; think 'liaison to AWS'
- The AWS Simple Notification Service(SNS) supports sending automated emails 
- **S3** is Object storage on AWS
- **tags** are key-value pairs: cloud resource metadata, we assign
    - **Owner**: Use this key in a tag to identify the person responsible for **`costnotify`**
- **policy** is a text document on the AWS cloud that permits or restricts actions


## Procedure Outline


- Get an AWS account (context: at U.Washington through DLT send a request to `help@uw.edu`)
- Create a dedicated S3 bucket
- Create an IAM Role with necessary Policies
- Create an SNS Topic with a Subscription designating your email as recipient
- Create the `costnotify` Lambda function
- Configure the Lambda function: Add environment variables, code, etcetera
- Test the Lambda function; and verify the service is running properly


## Procedure

### S3 Configuration and IAM User access


This procedure sets up your DLT AWS account to have CloudCheckr service/cost logging enabled.


In the AWS console select **Services** and sub-select **S3** under the **Storage** heading. This should
produce an alphabetized listing of **S3 buckets**. The listing is **Global** (upper right corner of
the console) so no region to specify. Look for a bucket that would be designated for CloudCheckr
service/cost logging. In our case these buckets were named `copydbr-<ID>` where `<ID>` is some string that
identifies this AWS account. 
  

If such a bucket is found: Click on it. An enabled bucket will contain filenames like this: 



`<accountnumber>-aws-billing-detailed-line-items-with-resources-and-tags-<year>-<month>.csv.zip`



If these files are present you are done with this step. 


If these files and/or this bucket are not
present: Send an email to `OpsCenter at dlt dot com` identifying yourself as an administrator and
ask 'How do I enable cloudcheckr cost logging to an S3 bucket?' The past procedure is given below.
However procedures change so be prepared to make an email enquiry.



* create bucket with a name format like `copydbr-our-unicorn-research`
    * Details:
        * I will abbreviate the bucket name as `copydbr-<ID>`
        * Choose `N.Virginia us-east-1` as the bucket region
        * Do not copy settings from an existing bucket
        * Block *all* public access
        * Disable bucket versioning
        * Add `Owner` and `Project` tags. The project is `costnotify`
        * Disable server-side encryption
        * Create bucket
    * Note bucket information once it shows up in Amazon S3 > Buckets
        * Name: **`copydbr-<ID>`**
        * Region: **`us-east-1`**
        * ARN: **`arn:aws:s3:::copydbr-<ID>`**


* In the AWS console go to the IAM service > Users > Add users
    * create an IAM account for use by DLT
        * User name: DLT 
        * Credential type: Access key
        * Permissions...
            * Attach existing policies directly > Create policy (new tab)
                * **JSON** tab 
                * Copy-paste the policy shown below into the text box (replacing the example text)

```
{
 "Version": "2012-10-17",
 "Statement": [{
      "Sid": "Stmt1443712554000",
      "Effect": "Allow",
      "Action": [
      "s3:DeleteObject",
      "s3:GetBucketLocation",
      "s3:ListObject",
      "s3:PutObject"
      ],
      "Resource": ["arn:aws:s3:::your-target-S3-bucket-name-here*"]
  }
 ]
}
```

* Provide access to this IAM account to DLT
    * Generate and download IAM User access keys to a safe location
    * Send the IAM User keys to DLT support together with the name of the S3 bucket and the account number
    * DLT should notify you fairly quickly when logging is enabled


Billing files are periodically updated (daily) and closed at the end of each month. 
That is: Each billing file corresponds to one month of AWS charges. These are the files that 
are parsed by the `costnotify` lambda function. Once these files are appearing in
bucket `copydbr-<ID>` you can continue.


### Create a Role for the Lambda function in advance


- Log in to the AWS console with admin privileges
- Go to IAM (Identity and Access Management) and choose (left sidebar) **Roles**
  - Notice these are Global; there is no *region* to consider
- Create a new role of type **Lambda**, proceed to Permissions
- Search for the managed policy **AWSLambdaExecute** and check the box
- Search for the managed policy **SNSFullAccess** and check the box 
  - As you do this the previous **AWSLambdaExecute** policy will not be visible; this is ok, it will remember
- Search for the managed policy **AmazonS3ReadOnlyAccess** and check the box
  - As above the other two policies you have selected will not be visible
- At lower right click the button **Next: Review**. You should (must!) see all three of these policies listed here.
- Name the role `costnotify` and give a description
- Create the role


### Create an SNS Topic 


This Topic will be referenced by the Python code installed in the Lambda function. This is done by
means of an "ARN string" that refers to the topic.


- Under Services select **Simple Notification Service**
- Ensure that your region (upper right) is set to **N.Virginia**
- Select **Topics** in the left sidebar and click the **Create topic** button
- Set both the **Name** and **Display name** to `costnotify`
- Ignoring all other settings add a tag with Key = 'Owner' and Value = your username
  - This helps make the SNS topic traceable to you
- Click the **Create topic** button at lower right
  - This creates the topic -- so far so good -- but next we add a Subscription to it so that email can be sent
- Click **Create subscription**
- Under **Protocol** select **Email**
- In the **Endpoint** box enter your email address
- Click the **Create subscription** box at lower right
- Return to the `costnotify` topic by clicking **Topics** in the left sidebar
  - Notice that the topic has an ARN string of the form `arn:aws:sns:us-east-1:<accountnumber>:costnotify
  - This string is used to reference the topic and thereby deliver email to all listed subscribers
  - Add additional email recipients by adding additional subscriptions, one per recipient
  - Each recipient confirms their subscription by responding to an email (so you should receive one)`


### Create the Lambda function


- Go to the Lambda services page and select the **N. Virginia** region at the upper right
- Create a new Lambda function: Choose to author it from scratch
- Name it `costnotify`
- Choose the Python 3.7 runtime (or higher; most recent is the point)
- Choose the role from step 1 above called `costnotify`
- Click **Create function** at lower right
  - 'congrats' message at the top of your new Lambda page
  - Notice two tabs available: Configuration and Monitoring
  - Both tabs are important; for now we stay on the Configuration tab
  

### Configure the `costnotify` Lambda function


The following steps are "everything needed" to get the costnotify Lambda working. As you work through this list
periodically click the Save button at the top of the page.


- Navigate to the Lambda function page and ensure that the **Configuration** tab is selected
  - Click on the **Test** button and give the test a name like `costnotify` with other defaults unmodified
  - Find the box **Designer** and click on **+ Add Trigger**
    - This creates a CloudWatch alarmclock that will run this Lambda function once per day
    - Select **CloudWatch Events** as the trigger
    - For **Rule** select **Create a new Rule**
    - Give a rule name (say `costnotify`) and short description
    - For **Rule type** select **Schedule expression**
    - Enter this rule in the **Schedule expression* box: `cron(0 10 * * ? *)`
      - This will run once per day at 10am UTC which will be early in the morning in the US
      - The idea is for the job to run fairly soon after the day has ended for you
      - For more on this rather arcane format do a search on 'cron format'
      - See also [this resource](http://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-schedule-experessions.html)
      - Of potential interest: Lambda functions can be triggered as well by a Put Object call to S3
    - Make sure **Enable trigger** is checked
    - Click the **Add** button at lower right to complete this trigger configuration step
    - ***Important step! In the Designer box click on the Lambda `costnotify` box***
      - ***This will dismiss the **Cloudwatch events** detail and return you to the Lambda configuration boxes***
  - Find the box **Function Code**
    - Delete the code provided here as a placeholder
    - Copy the `costnotify.py` code from this repo
    - Paste it into the Function Code box
  - Find the box **Environment Variables**
    - Enter the following Key-Value pairs:
    
`accountnumber`: your corresponding 12-digit numerical AWS account number<BR>
`bucketname`: The name of your *copydbr-etcetera* S3 bucket (see above on setting this up)<BR>
`snstopic`: `costnotify` (i.e. match the topic name you created in the previous SNS configuration step) <BR>
`friendlyaccountname`: Short word/phrase identifying which account this is for a human reader<BR>
`override`: `False` (set `True` to get the analysis for a particular year/month<BR>
`monthOverride`: The numerical month 1, 2, ..., 12 you are interested in<BR>
`yearOverride`: The numerical year 2019, ... you are interested in<BR>

  - Find the box **Tags**
    - Enter a key = `Owner` and a corresponding value = your IAM User name
      - This associates the Lambda with you
  - Find the box **Execution Role**
    - If you configured this to use the `costnotify` role this should appear here
    - If you did not specify this...
      - Create the `costnotify` role (if you have not done so) as described above
      - Select `Use existing role` and select the `costnotify` role
  - Find the box **Basic Settings** 
    - Give a short description of the Lambda function
    - Set the memory to 256MB
    - Set the timeout interval to 2 minutes
  - Be sure to click **Save** and then **Test** to verify your `costnotify` Lambda function is working 

## Debugging, Monitor tab, Cost Explorer

When your click the **Test** button at the top of the Lambda function page the results are shown as either Success or Failure.


If execution Fails: Read through the message in the Output section of the **Code** box. This will indicate
the line of code where the problem occurred.

Whether the Lambda execution succeeded or failed you may be interested in the output it produces.
Follow the **logs** hyperlink to see a list of result log files. The most recent is at the top. Click on
this file to open it. Any `print` output from the Lambda function can be found here. 

The **Monitor** tab may also be useful in debugging. Dashboard charts indicate the lambda has been triggered, etcetera.
  
Cost Explorer is a feature of the AWS browser console. You can access this using the top right dropdown menu 
and selecting My Billing Dashboard; then start the Cost Explorer.  

When you receive a billing statement you should compare it with the Cost Explorer estimate of your daily spend
  - At the upper right of the console use your Account Name dropdown to select My Billing Dashboard
  - Link to the Cost Explorer and launch it
  - Use the Reports dropdown to select **Daily Costs**
  - A calendar drop-down allows you to select a time range (I use MTD); and you must click the **Apply** button
  - You should now see daily expense as a bar chart
    - You can hover over a particular day to get the exact value
    - One DLT accounts the current day cost will look low and tend to be inaccurate
  - This daily cost record should be -- we intend -- commensurate with the email notification you will now receive from lambda
