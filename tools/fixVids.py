'''
This script will fix videos that have do not have the "moov atom" metadata in 
their video encoding (usually due to recording camera unexpectedly shutting down)
 
It will use an "untrunc" program, and go through multiple video data sets
concurrently

Note: Must setup docker for untrunc before running
'''

import os
import boto3
import shutil
import csv
import threading
import time
from helper import uploadToS3


#Function for fixing/untruncating videos
def untruncVideo(videoName, newVideoPath):
    untrunc = 'docker run -v ~/untrunc/videos/:/videos untrunc /videos/goodVid.mp4 /videos/'+videoName
    try:
        os.system(untrunc)
        shutil.move(videoDownloadPath+videoName+'_fixed.mp4', newVideoPath+videoName)
    except:
        print("Zero-length file video")

def run(site):
    #Create tracking file for which videos have been analyzed
    trackFile = path+"processed.txt"
    print("TrackFile: ", trackFile)
    if not os.path.isfile(trackFile):
        f = open(trackFile,'a+')
        f.close()

    # Go through every video in S3 bucket 
    # "untrunc" the video
    # Reupload new video to S3
    for s3_file in s3.Bucket(VIDEO_BUCKET_NAME).objects.filter(Prefix='videos/'+site):
        substring = s3_file.key.split("/")
        filename  = substring[-1]
        
        if filename.endswith(".mp4"):
            #Skip video fixing if already done
            if s3_file.key in open(doneFile).read():
                print("\n\nAlready read:"+ s3_file.key)
                continue
            else:
                print("\n\nAnalyzing "+ s3_file.key +" video...")

                #Split key name
                vidName  = filename.split('.')[0]
                time     = substring[-2]
                date     = substring[-3]
                facility = substring[-4]
                print("Video name: " + vidName)
                print("Facility: "   + facility)

                #Download video from S3
                print("Downloading video from S3...")
                videoFullPath = vidPath+filename
                s3.Bucket(VIDEO_BUCKET_NAME).download_file(s3_file.key, videoFullPath)
                print("Finished downloading video")

                #Create new directory for fixed video
                newVidPath = vidPath+facility+'/'+date+'/'+time+'/'
                if not os.path.exists(newVidPath):
                    os.makedirs(newVidPath)

                #Fix Video
                untruncVideo(filename, newVidPath)

                #Sync video to S3
                if os.isfile(newVidPath+filename):
                    source = newVidPath+videoName 
                    destination = 's3://'+str(VIDEO_BUCKET_NAME)+'/*/full_videos_fixed/'+facility+'/'+date+'/'+time+'/'
                    uploadToS3("sync", source, destination)  

                #Remove video
                print("Done analyzing, removing current video file...")
                os.remove(videoFullPath)

                #Add video to doneFile
                f = open(trackFile,'a')
                f.write(str(s3_file.key)+'\n')
                f.close()
                print("Moving onto next video...\n")

def main(args):

    #Create Video Path
    path    = args.root_dir + '/' + args.new_dir + '/'
    vidPath = path + 'Videos/'

    if not os.path.exists(vidPath):
        os.makedirs(vidPath)    

    #Setup list of directories to run through
    sites1 = ['Comp3','Comp4','Comp5']
    sites2 = ['Comp6','Comp7','Comp8']

    #Setup and begin multi-threading 
    main_thread = threading.currentThread()
    threads = []
    for site in sites1:
        t = threading.Thread(target=run, args=(site,))
        threads.append(t)
        t.start()

    #Check status of threads and start new side thread if a site's video list has completed
    endFlag = False
    threadCompleteCount = 0
    while !endFlag:
        print("Alive Threads: " + str(threading.enumerate()))
        print("Thread count: " + str(threading.activeCount()))
        if (threading.activeCount() == 1):
            print("All threads are completed... finishing script")
            endFlag = True
        elif (threading.activeCount() < 4 and threadCompleteCount < 3):
            print("A side thread has completed, start new thread for next site in list")
            t = threading.Thread(target=run, args=(sites2[threadCompleteCount],))
            threads.append(t)
            threadCompleteCount += 1
            t.start()
        else:
            print("\nContinue running program...\n")
            time.sleep(120)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Find Contours of video')
    argparser.add_argument('-r', '--root_dir', default=os.path.join(os.environ['HOME'], 'Videos'), help='root directory')
    argparser.add_argument('-d', '--new_dir', help='folder directory')
    argparser.add_argument('-v', '--video', help='video')
    args = argparser.parse_args()
    main(args)    
