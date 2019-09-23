# Welcome Zombie Hunters

Our first idea is to seek out and tidy up resources associated with EC2 instances. These are machines (computers) that we 
rent by the hour from the cloud provider, in this case from Amazon Web Services. 


The first thing we will do is provide a framework for how these things work. Then we will provide a process to go through
to cull down the zombies. 

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
  - Wrong. They still cost the same: 




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
