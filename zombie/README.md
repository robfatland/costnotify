# Welcome Zombie Hunters


Our first idea is to seek out and tidy up resources associated with EC2 instances. These are machines (computers) that we 
rent by the hour from the cloud provider, in this case from Amazon Web Services. 


The first thing we will do is provide a framework for how these things work. Then we will provide a brief remark on 
***Tagging*** followed by a procedural for culling back the zombies.  This is followed by some email excerpts with 
Joel at AWS as I am trying to sort out the details.


## Framework


An EC2 instance is originally requested and granted. It comes with some small amount of disk space, typically like 8GB. 
That is where the operating system lives; and there is some space left over for the User. We'll call this the root drive.
On a Windows machine it is the C:/ drive. 


In addition the User getting the EC2 can request additional drive space be added. This might be just making the 
root drive bigger, perhaps much bigger, like 2000 GB. It might also involve attaching additional drives, analogous 
to the D:/ and E:/ and F:/ drives (say) on a windows machine. 


Now we have an EC2 instance with its root drive and we have possibly some additional drives. Here is the acronym jargon:


- EC2 = A computer we rent by the hour
  - This is called an ***Instance***
- EBS = Elastic Block Storage i.e. disk drives attached to the EC2 when it starts up
  - This is called a ***Volume***


Let's assume that a researcher has started up and used an EC2 with a root drive of 500 GB plus an additional drive 
of 1000 GB (1 TB (1 Terabyte)) for three days to get some computing done. Let's see how this resource turns
into a zombie.


- The computer costs $1 per hour so the researcher is careful to use the console to ***Stop*** the instance.
  - No longer paying, right? 
- The 500 GB volume is 492 GB larger than its default size of 8 GB
  - This costs $0.10 per GB per month or $49.20 per month
- The 1000 GB volume costs $0.10 per GB per month or $100 per month
- Both of the EBS volumes together cost $149.20 per month
  - They are not in use; just sitting there
- In the console the EBS volumes can be ***Detached***: Select the volume, then use the **Actions** dropdown to **Detach volume**
  - Once they are detached they don't cost anything, right?
  - Wrong. They still cost the same: $0.10 per GB per month
- In the console for **Volumes** select an EBS volume then Action > Create Snapshot
  - The volume will be compressed to minimal size and stored at that size for $0.05 / GB / month
- In the console for **Instances** select an EC2 instance then Action > Image > Create Image
  - As with volume snapshots the root volume will be compresed and stored as an AMI (which includes a snapshot)
  - This also costs $0.05 per GB per month
- Once the snapshots and AMIs are created: Delete the volumes so they no longer cost money


It bears repeating: An AMI is a short description of the EC2 instance plus a snapshot of the root volume. This means
that we do not have to snapshot the root volume in addition to making an AMI. The AMI includes the snapshot so just do 
that. However for additional attached drives we need one snapshot of each. 


> It is also much cheaper to store things in object storage; so there is another step possible here that I won't go
into in detail. The idea would be to create a zip file of all the data on the large EBS volume or volumes and move that
to object storage which costs $0.023 per GB per month; so less than half as much as a snapshot. Then delete that data 
from the EBS volume and *then* make the snapshot if it is still needed. From there we can even move the data from 
object storage to archival which gets us another factor of six cost savings; but this makes sense only if we do not plan
to use the data for some time. 


## Tagging


Each item (EC2, Volume, AMI, Snapshot) has a ***Name***. For example the first EC2 instance in the table I
am looking at has Name = CAHW_notebook. This was launched on Nov 20 2018 (almost a year ago) and it is currently
stopped. The first thing I do is edit this Name by hovering over it to select the pencil. I change the name from
*CAHW_notebook* to *Elsa CAHW_notebook DNT Rob*. Why? First I happen to know that *Elsa* is the person associated
with this EC2 instance; so now her name is foremost for future reference. Second I preserve the project name 
CAHW_notebook so we know what the machine was for. Third I put in 'DNT Rob' to mean "Do Not Terminate / Rob was here". 
Now future reviews of this resource will have a basis for figuring out what to do with it; and hopefully nobody will
just randomly Terminate the instance. Notice that we have the capacity to tag a lot of resources. I find 46 Instances,
46 Volumes, 38 AMIs and 103 Snapshots. Out of all these resources only 3 Instances are currently running; so there
is a great potential for cleaning up the zombies.


## Procedure

- Log in to the AWS console
- Under Services (upper left) choose EC2 and make sure your Region (upper right) is set to Oregon
- Copy the URL and open three more tabs, pasting that URL in to the address bar each time
  - You now have four browser tabs connected to EC2. Each will go to a different EC2 sub-page
- Choose (left side-bar) Instances for your first tab
- Choose Volumes for your second tabl
- Choose AMIs for your third tab
- Choose Snapshots for your fourth tab


We will proceed to work our way through Instances, Volumes, AMIs and Snapshots


### Part 0: Reminder on tagging


If you have seen it once it bears repeating: Consider re-reading the section above on ***Tagging***
before going further.


### Part 1: Instances and Volumes

- If an instances is Stopped it is a candidate for Termination once it has been backed up as an AMI
- If an instance is Running it should be allowed to keep running but with an email sent to the owner

### 1.1 Tagging Instances and Volumes

Each instance should be tagged with **some-name project DNT your-name** as a temporary measure. This
ensures that the instance won't be terminated (we hope) without good cause. Remember that **some-name**
is the name of the person who was using the instance (if available) and **project** is the research 
project associated with that work. 

In parallel all of the Volumes associated with these Instances should be tagged in the exact same manner.
If the Volume is in-use then it will be obvious where it is attached: See the Attachment information which
will hyperlink directly to the EC2. Rather than use **DNT** in the tag I prefer **DND** for Do Not Delete. 

What about instances or volumes that are clearly derelict? If you are certain that they have no possible 
value to anyone; and particularly if they are not labeled or labeled in ambiguous fashion: Go ahead and delete 
them.  


### 1.2 Making AMIs and snapshots


### 1.3 Sending Grim Reaper emails


Here is where the tagging pays off. You send email to the person listed as the owner of the resource 
inviting them to evaluate its use. Either they do not respond... or they say "go ahead and delete it"...
or they request it be preserved.


### 2.1 Sorting out AMIs and Snapshots

As with the previous phase: Tag everything that has value...

...and for resources that are not traceable, that are ancient, that have no 







## A Sequence of Q&A Emails with Joel Morgan at AWS


### Rob's first email

Sanity check: Are these correct statements? 


- A first snapshot of an EBS is responsible for all the bits on that volume
- This is typically going to occupy less volume than the EBS drive volume when 
there are vast amounts of unused space on that EBS volume because the snapshot is compressed (zipped or whatever)
- Subsequent snapshots are deltas to the first one
- These are stored on S3 at 5 cents / GB / month which is a bit more than twice the base S3 rate
- The drive has to be detached so first stop the instance then detach the drive then update the 
snapshot then blow away the drive and you are no longer paying for the drive (just the snapshot) and this can be reconstituted. 
- The snapshots will persist indefinitely incurring charges at their rate until deleted
- Snapshots should be annotated with Tags in order to determine where they came from (i.e. which 
User generated them) so that if that User shows up needing to restore their volume we are not in a 
position of looking at hundreds of incomprehensible identifier strings trying to guess which one 
was the EBS volume needed.

### Joel responds


Correct on all points but one: an EBS volume does not have to be detached before taking a snapshot. 


To help with keeping your snapshots under control and to protect your sanity, we now have a service called 
[AWS Backup](https://aws.amazon.com/backup/) which helps schedule creation and deletion of EBS snapshots (among other things). 


### Rob writes back, part 1, answer pending


If I look at my list of snapshots on some account in some Region I see a table of snapshots with additional 
data across the row. The big task here is: Does this snapshot need to persist; so what is its level of need 
and how much does it cost? To do the forensics I have this data: 


- Name = usually left blank; that's our fault!
- Size = 1024GB. Am I charged 1024 x 5 cents per month? Or less due to actual-use and zip compression? 
How to find this out?
-  Description = Created by CreateImage(i-0f99etcetera) for ami-0b251etcetera: Implies this snapshot 
is actually the basis for an AMI where the "AMI aspect" is some additional metadata stored under AMIs
- Started = October 27, 2018 etc: First snapshot but does not indicate latest update

Then for the selected Snapshot down below in the Description / Perm / Tags tabs: 

Tags are usually blank: our fault!
Description includes: 

- Volume with link: If I go to the link and No Volumes Found then the EBS volume itself has been deleted; so that is good info
- Description includes the AMI which I can look up; and there I find both a Name and an AMI Name. So this is my final clue. 

Here's where you can check my conclusions: 

Yes these snapshots are the "guts" of an AMI. Their actual size and therefore actual billing cost is not 
available through the console but I might be able to find it listed in CloudCheckr billing records. 
Similarly I have no way of knowing when this snapshot was last updated. Hence: The only way I can 
determine if these snapshots are "worth keeping around" is to check the tags on the AMI and see if 
that leads me to a person; and then check with them. Otherwise deleting these snapshots is basically 
taking the chance that they are abandoned resources. I at least know that the maximum amount they 
can cost is 5 cents per GB per month. 


### Rob writes back, part 2, answer pending


There is a bit of a lead-in to make sure I understand correctly...


Suppose I obtain an EC2 with by default an 8GB root disk. I bump this up to 500 GB and add an EBS 
of 1 TB. Now I have 1500 GB of EBS and I am paying $0.10 per GB per month for 1492 GB. So this 
runs me $149.20 per month. 


Now I Stop the EC2 instance but the two EBS volumes are still "in use". So I select them and do Detach Volume. 
Now they are Available but they still cost as before, $149.20 per month. For the 1000 GB EBS I select 
Create Snapshot. Because this drive was only partially full let's suppose it compresses down to 500 GB 
where I pay $0.05 per GB per month for that snapshot, i.e. $25 / month. So far so good. 


Now what about the 500 GB EBS Volume that includes the OS? What I imagine is the correct procedure is that 
I select the EC2 (this is all in the console) and use Actions > Image > Create Image. This will create both 
an AMI (metadata about the machine) and an associated Snapshot that references the AMI. So let's imagine this 
snapshot has a volume after compression of 100 GB. Now that also costs me $0.05 per GB per month or $5 per month. 


Now that I have created the AMI (with snapshot) and the other snapshot I can go ahead and run Delete Volume on 
both of my EBS volumes. I am no longer paying for them; only for the storage of the snapshots. 


My question is: Does Create AMI succeed even though I have detached that root 500 GB EBS volume? 
Another question: Suppose I do both Create AMI on the EC2 and Create Snapshot on the 500 GB EBS volume: 
Does this create two snapshots of this one volume, one with and one without the AMI metadata? In other 
words: The snapshot is redundant and unnecessary once the Create AMI is successful; and should 
therefore be deleted. 



### Joel writes back inline answers

- Size = 1024GB. Am I charged 1024 x 5 cents per month? Or less due to actual-use and zip compression? How to find this out? 

> Less, but frustratingly it is not possible to see the actual size of the snapshot.

-  Description = Created by CreateImage(i-0f99etcetera) for ami-0b251etcetera: Implies this snapshot is actually the basis for an AMI where the "AMI aspect" is some additional metadata stored under AMIs 

> Yes, AMIs are based on Snapshots, but contain extra data with instructions on how to launch and EC2 instance using the Snapshot.

- Started = October 27, 2018 etc: First snapshot but does not indicate latest update 

> A Snapshot won’t be updated. Instead, subsequent snapshots are listed on their own but are based on the 
first snapshot. You can delete the first snapshot of a volume if the only one you really need is the third 
or fourth etc. https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSSnapshots.html#how_snapshots_work

 

 

Then for the selected Snapshot down below in the Description / Perm / Tags tabs:  

- Volume with link: If I go to the link and No Volumes Found then the EBS volume itself has been deleted; so that is good info

- Description includes the AMI which I can look up; and there I find both a Name and an AMI Name. So this is my final clue. 

 

Here's where you can check my conclusions: 

 

Rob thinks: Yes these snapshots are the "guts" of an AMI. Their actual size and therefore actual billing cost is not available 
through the console but I might be able to find it listed in CloudCheckr billing records. Similarly I have no way of 
knowing when this snapshot was last updated. Hence: The only way I can determine if these snapshots are "worth 
keeping around" is to check the tags on the AMI and see if that leads me to a person; and then check with them. 
Otherwise deleting these snapshots is basically taking the chance that they are abandoned resources. I at least 
know that the maximum amount they can cost is 5 cents per GB per month. 


Joel responds: 


> Since snapshots are not “updated”, if you only want the most recent you can delete all snapshots for the volume which are dated earlier. If you go to the Snapshots page you can then filter by the volume ID which will show you all the snapshots made for that volume. All snapshots that are part of an AMI will indicate so in the description. It is of course possible to take a direct EBS Snapshot of a volume and also create an AMI from the instance to which the volume is attached. In that case there will be two snapshots for the volume listed: one that is an independent EBS snapshot and one that is tied to the AMI.


### Joel writes back directly on AMIs and Snapshots


Answered your previous questions inline [above]. When you create an AMI, it will by default include all volumes 
attached to the instance. If you want everything an EC2 instance has, then you can simply make an AMI. When 
you later launch an EC2 instance from the AMI, it will also create clones of any attached volumes on the original. 
You have the option to not include any volumes but the root volume when taking an AMI. This is useful if you 
want to create new EC2 instances but you don’t need any data from the extra volumes on the original. Customers 
will often take AMIs infrequently since the root volume with the OS and applications doesn’t change much, but 
more frequently take EBS snapshots of the data volumes since the data on them changes more frequently. If you 
want to be able to create EBS volumes populated with data but don’t care about the root volume, then take a 
direct Snapshot. If you want a full system from which you can launch EC2 instances then take an AMI. If you 
want to manage data volumes and a system image separately, then uncheck the option to include all attached 
volumes when you create an AMI. What it comes down to is Snapshots can create EBS volumes, and AMIs create 
EC2 instances. As a side note, if you had an EBS Snapshot of a root volume and the OS is Linux, you can 
create an AMI out of it.
