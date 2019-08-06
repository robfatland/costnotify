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



## S3 pre-configuration: This section gets a flag


It was originally written to the DLT specifications. It needs an update to CloudCheckr. 


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
  
## Stop here with a flag

Everything from this point onward is copied from the old instructions. It needs review and update. 

## Continuing with edited version of the old source material

- Scroll past **Designer** panel and **Function code** panel: You will enter four Environment variable key pairs now
  - Enter a Key string: accountnumber
    - Enter the correct Value string for your account: Your 12-digit AWS account number
    - This will be referenced in the Lambda Python code so that you do not need to hardcode your account number
  - Enter a Key string 'dayintervalStart'
    - Enter a Value string '2'
  - Enter a Key string 'dayintervalEnd'
    - Enter a Value string '2'
    - Start and End = 2 is the most recent day range (24 hours) that tends to work properly *most* of the time
      - You can try other values (remember these are days in the past, relative to today) to see how that works
      - If you run this on the second day of the month with values like 32 and 2 you should see something close to your monthly spend as the total
  - Enter a Key string 'emailsubject'
    - Enter a simple recognizable string as the Value, for example 'AWS daily spend'
- Scroll down further to the Basic settings panel
  - Set the Memory (MB) slider to 256 MB
  - Set the Timeout values to reflect 2 min 10 sec 
- The remaining lower panels can be left as-is
  - Notice that the Execution role panel should list the role you created in step 1
- Scroll back up to the **Function code** panel
  - Delete the lines of code if there is some stuff already in the code window 
  - Paste in the code block given here: 


```
This is where the old code used to be. See the folder original_code for this code.
```

- Note down the arnString value for use in the SNS setup (below)
  - In this case it would be 'arn:aws:sns:us-east-1:123456789012:dailycostnotify'
    - Where again 123456789012 should actually be your 12-digit account number
  - This will be the SNS topic as described below
- SAVE your settings so far: Click the Save button at the top of the web page


***Setting the Lambda triggers: CloudWatch and Lambda Test button***

- At the top of the lambda function page are tabs for Configuration and Monitoring as noted
- Staying on the Configuration tab locate the Designer region at the top of the page which includes a block diagram of the lambda function
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


## SNS


- In the AWS console go to the SNS services page
- Select Create topic
- Enter the topic name per the Python code above: dailycostnotify
- Enter a topic abbreviation, 10 characters
  - Example: dailycost
- Continue to topic details and click Create subscription
  - Choose type = email and add your email address plus any others you think should receive notifications
- Click on Create subscription to send a confirmation email to yourself; and then confirm that 


You should now start receiving a daily spend summary in your Inbox. 
Verify that this works using the Test button on the lambda function page.


## Validation and Debugging


You should be able to Test your lambda function now. If it fails you'll have to debug it. 


## Cost Explorer


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
