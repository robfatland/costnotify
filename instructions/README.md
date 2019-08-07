## Objective and Supporting Information

This is	a walk-through for installing a daily cost notify email for an AWS account. It is 
revised 6-AUG-2019 to accommodate the CloudCheckr itemization file format. 


- In what follows we try to consistently use `costnotify` as a resource label
  - Use whatever you like but we suggest keeping it pretty short
- At UW use *help@uw.edu* for help setting up an AWS account. 
- Also check out the [UW CSE Database group's AWS page](http://db.cs.washington.edu/etc/aws.html).
- **DLT** is cloud re-seller that provides AWS accounts to the University of Washington 
- **Lambda** is code that runs on AWS; sometimes called *serverless* computing. 
- **SNS**: The AWS Simple Notification Service(SNS) which permits you to format and send emails 
automatically. In our case this action will be triggered by a Lambda function
- **S3**: Object storage on AWS, i.e. the place where *objects* are placed and accessed.
- **tag**: A key-value pair associated with a cloud resource 
  - **Owner**: A useful tag key where the value is then an IAM User responsible for the resource 
- **Policy**: A text document on the AWS cloud that permits or restricts actions


## Procedure overview

- Create the S3 bucket in your account and turn on the accumulation process
- Create an IAM Role with some permission Policies. The Role will permit your Lambda to "do stuff" on AWS
- Create a Lambda function that assumes this Role 
- Configure the Lambda function; add environment variables and code and associated services
  - ...including a CloudWatch trigger that will cause the Lambda to run once per day
  - ...including an SNS topic to distribute the Lambda results to an email distribution
- Test your notifier



## S3 pre-configuration


In 2019 working with DLT we received new instructions on setting up an S3 bucket. The support ticket
at DLT uses OpsCenter at DLT dot com so start by writing them an email asking for help setting up a 
billing bucket on S3. The bucket name we use is `copydbr-<ID>` where `<ID>` is a string unique to 
your AWS account. Once this bucket is established the billing itemization file should appear therein. 
These files are periodically updated (time scale hours) and then closed out at the end of each month. 
That is: Each billing file corresponds to one month of AWS charges. The filenames for these files 
use the 12-digit AWS account number, here `<accountnumber>`. A typical file will be named 
  
`<accountnumber>-aws-billing-detailed-line-items-with-resources-and-tags-<year>-<month>.csv.zip`

These are the files that will be parsed by the costnotify lambda function. Note that they must be 
un-zipped to be readable. 


## Create a Role for the Lambda function in advance


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


## Create an SNS Topic 

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


## Create the Lambda function


- Go to the Lambda services page and select the **N. Virginia** region at the upper right
- Create a new Lambda function: Choose to author it from scratch
- Name it `costnotify`
- Choose the Python 3.6 runtime
- Choose the role from step 1 above called `costnotify`
- Click **Create function** at lower right
  - 'congrats' message at the top of your new Lambda page
  - Notice two tabs available: Configuration and Monitoring
  - Both tabs are important; for now we stay on the Configuration tab
  

## Configuring the `costnotify` Lambda function

The following steps are "everything needed" to get the costnotify Lambda working. As you work through this list
you may want to periodically click the Save button at the top of the page.


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
    - Make sure **Enable trigger** is checked
    - Click the **Add** button at lower right to complete this trigger configuration step
    - ***Important step! In the Designer box click on the Lambda `costnotify` box***
      - ***This will dismiss the **Cloudwatch events** detail and return you to the Lambda configuration boxes***
  - Find the box **Function Code**
    - Delete the code provided here as a placeholder
    - Copy the `costnotify.py` code from this repo
    - Paste it into the Function Code box
  - Find the box **Environment Variables**
    - Enter Key `accountnumber` and Value = your corresponding 12-digit numerical AWS account number 
    - Enter Key `bucketname` and Value = `copydbr-<ID>`
    - Enter Key 'snstopic' and Value 'costnotify'
      - This Value should match the topic name you created in the previous SNS configuration step
    - Enter Key 'dayintervalStart' and Value '2'
    - Enter Key 'dayintervalEnd' and Value '1'
      - This defines the 24-hour time range for accumulating total spend
      - flag what is the time zone for time codes in the file?
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

## Debugging and using Cost Explorer

## Stop here with a flag

Everything from this point onward is copied from the old instructions. It needs review and update. 

## Continuing with edited version of the old source material

- Scroll past **Designer** panel and **Function code** panel: You will enter four Environment variable key pairs now


- Note down the arnString value for use in the SNS setup (below)
  - In this case it would be 'arn:aws:sns:us-east-1:123456789012:dailycostnotify'
    - Where again 123456789012 should actually be your 12-digit account number
  - This will be the SNS topic as described below
- SAVE your settings so far: Click the Save button at the top of the web page


***Setting the Lambda triggers: CloudWatch and Lambda Test button***

- Add a CloudWatch Events trigger. CloudWatch is a management tool that allows you to create an Event linked to your Lambda.
  - This Event begins with creating a rule in Step 1
    - Choose **schedule** and use the following string to stipulate 'once per day at noon GMT'...
      - cron(0 12 * * ? *)
      - For more on this see [this link](http://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-schedule-experessions.html)
    - Set the target as the Lambda function name: **dailycostnotify** 
    - Move forward to Configure details in Step 2
    - Give this rule a Name 'dailycostnotify'. Add a Description and click the button 'Create rule'
    - The new rule should appear with a timer icon
      - It will trigger your lambda function every 24 hours
      - Missing piece: Setting the actual time of day for this trigger...
  - Note: A lambda function can be set to trigger from S3 access (Get or Put Object)
    - We do not do that here because the DLT logging process has latency built in
  - As a separate task: Configure the Lambda function to execute from the Test button 
    - Go through the default configuration process; you don't have to modify anything
    - Save and click the Test button. It will fail until everything below is also in place 






Cost Explorer is a feature of the AWS browser console. You can access this using the top right dropdown menu 
and selecting My Billing Dashboard; then start the Cost Explorer.  In more detail:


- When you receive a billing statement you should compare it with the Cost Explorer estimate of yor daily spend
  - At the upper right of the console use your Account Name dropdown to select My Billing Dashboard
  - Link to the Cost Explorer and launch it
  - Use the Reports dropdown to select **Daily Costs**
  - A calendar drop-down allows you to select a time range (I use MTD); and you must click the **Apply** button
  - You should now see daily expense as a bar chart
    - You can hover over a particular day to get the exact value
    - One DLT accounts the current day cost will look low and tend to be inaccurate
  - This daily cost record should be -- we intend -- commensurate with the email notification you will now receive from lambda


#### The Lambda function monitoring tab


- This tab is very useful is something is not working properly with your lambda function
- The monitoring tab is selected near the top of your lambda service page in the AWS console
- Dashboard charts indicate the lambda has been triggered
- The link to View logs in Cloudwatch is also helpful; diagnostics printed by the lambda show up here
  - Set print statements in the lambda; save the lambda; trigger it using the Test button; diagnose 
