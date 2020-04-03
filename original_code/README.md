# What is here

This is entirely legacy code for reference

## Some old file choosing code

```



#######################
###
### Artifact code from the past
###
#######################

### choose which file(s) to parse
# def FileChoice(contents_list):
    # establish two lists: filenames and the time that each was last updated (seconds since 1970!)
    # filelist, updateTime = [], []
    # for element in contents_list:
        # filename = element['Key'].split('.')    # a printable 3-element list: <long-filename>, '.csv', '.zip'
        # filetime = element['LastModified']
        # if filename[-1] == 'zip':
            # filelist.append(element['Key'])
            # updateTime.append(element['LastModified'].timestamp())     # Verified: len(filelist) is equal to len(updateTime)

    # this could be expanded to a list of files if we are at a month or year boundary right now
    # return filelist[-1]
    
# flag this will need attention on month/year boundaries
# fileChosen = FileChoice(csv_file_list['Contents'])

# For reference: some_dt = datetime.datetime(x.year, x.month, x.day, 0, 0, 0);
# reference components of the datetime using for example some_datetime.year


```

## Original code `AWS_costnotify_lambda.py`


