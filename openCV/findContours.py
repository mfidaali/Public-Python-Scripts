'''
Script that goes through a list of videos in a CSV, and finds the relevant contour information of video
This is helpful in binning the videos based off contour information, to understand dataset for AI training
'''

import os
import boto3
import shutil
import csv
import time
import statistics 

from helper import load_AI1, timestring_to_secs, secs_to_timestring, crop_frame, resize_frame, uploadToS3

import re
import tensorflow as tf

from openCV.cvVideo import cvVideo


#AWS Credentials
session = boto3.Session(
       aws_access_key_id='*',
       aws_secret_access_key='*'
   )

s3 = session.resource('s3')
VIDEO_BUCKET_NAME = "*"
IMAGE_BUCKET_NAME = "*"

#Find shape of object in video using contouring
#Look at 25 images of the video, and take 'mode' contour value
#Specify shape based on mode value
def analyzeContour(vidPath, videoName, vidNameNoSpaces, imgPath, csvFile, row):
    
    #Call openCV video class
    vid = cvVideo(path=vidPath, vid=videoName, startIdx=1200)
    vid.displayInfo()
    
    #Define generic AI variables
    is_AI = False
    THRESHOLD = 20*30
    current_threshold = 0
    
    #Define contour variables
    shapeCount = 0 
    shapeList = []
    
    while vid.capIsOpened():
        ret, frame = vid.readFrame()
    
        if not ret:
            print("Video Finished")
            break

        # Finished gathering sample size of images to determine contour of video
        # End Video analysis
        if shapeCount == 25:
            print("Calculating 'mode' of shapeList")
            try:
                modeVal= statistics.mode(shapeList)
            except:
                #Mode failed for row
                modeVal = 0
            
            row.append(str(modeVal))
            if modeVal == 4:
                row.append("Square")
            elif modeVal>8:
                row.append("Round")
            else:
                row.append("Unsure")
            
            f = open(csvFile,'a')
            f.write(",".join(row) + "\n")
            f.close()
            break


        # Crop
        crop_img, tl_x, tl_y = crop_frame(frame)
        r, c, ch = crop_img.shape

        # If cropped image is empty, skip
        if r == 0 or c == 0:
            continue

        # Resize for an image net
        img = resize_frame(crop_img, 224)
        
        # Use AI to determine if this frame is good for contour calculation
        AI_preds = model_AI.predict(img)[0][0]
        if (1-AI_preds) < 0.9: 
            if is_AI:
                current_threshold += 1
                if current_threshold > THRESHOLD:
                    is_AI = False
                    print("AI is false")
                    current_threshold = 0
            else:
                continue
#                 current_cd = COOLDOWN*5        
        else: 
            # AI predicted true
            # Reset current "false" threshold
            is_AI = True
            current_threshold = 0

        # This frame is good for determining contour
        # Begin contour calculation 
        if is_AI:
            # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = vid.gray(frame)
            ret,thresh = cv2.threshold(gray,127,255,1)

            contours,h = cv2.findContours(thresh,1,2)
            shapeCount += 1    
            shapeStr = "XXX"
            approx = 0
            for cnt in contours:
                approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
                if len(approx)==4:
                    shapeStr = "square"
                    print("shapeFound: "+str(shapeCount)+"; " + shapeStr)   
                elif len(approx)<9:
                    shapeStr = "not_circle_not_square"
                    print("shapeFound: "+str(shapeCount)+"; " + shapeStr)
                elif len(approx) == 9:
                    shapeStr = "half_circle"
                    print("shapeFound: "+str(shapeCount)+"; " + shapeStr)
                elif len(approx) > 9:
                    shapeStr = "circle"
                    print("shapeFound: "+str(shapeCount)+"; " + shapeStr)
             

            #Save image with image_name based on contour type            
            if len(approx) > 9:
                shapeList.append(10)
            else:
                shapeList.append(len(approx))
            
            imgName = vidNameNoSpaces+"__f%06d__approx%02d__sF%02d_sH%s" % (int(frameNum), int(len(approx)), int(shapeFound), str(shapeStr))                    
            cv2.imwrite(imgPath + imgName +".jpg", crop_img)     
        
        else:
            continue
                      
    vid.release()


def main(args):

    #Load AI model
    model_AI = load_AI()

    #Create Video and Image Paths
    path    = args.root_dir + '/' + args.new_dir + '/'
    vidPath = path + 'Videos/'
    imgPath = path + 'Images/'

    if not os.path.exists(vidPath):
        os.makedirs(vidPath)    
    if not os.path.exists(imgPath):
        os.makedirs(imgPath)   


    #Create tracking file for which videos have been analyzed
    trackFile = path+"processed.txt"
    print("TrackFile: ", trackFile)
    if not os.path.isfile(trackFile):
        f = open(trackFile,'a+')
        f.close()


    #Create CSV to track contour information for each video analyzed
    contourCSV = path+"videosContour.csv"
    print("contourCSV: ", contourCSV)
    csvWrite = open(contourCSV,'a+')



    #Go through every row in labeled CSV
    #Grab relevant video information
    #Download specified video from S3
    #Analyze video for relevant contour information
    #Write contour information to new CSV
    with open('data.csv') as data:
        dataCSV = csv.reader(data, delimiter=',')
        line_count = 0

        for row in dataCSV:
            if line_count == 0:
                line_count+=1
            else:
                vidID= row[0]
                patID= row[1]
                print("Video ID: " + vidID + "\n")
                print("Relevant ID: " + patID + "\n")
                
                vidFoundFlag = 0
                
                #Find video in s3 Bucket
                for s3_file in s3.Bucket(VIDEO_BUCKET_NAME).objects.filter(Prefix='*'):
                    #Skip video if already analyzed
                    if s3_file.key in open(trackFile).read():
                        vidFoundFlag = 1
                        print(s3_file.key + " has already been analyzed\n")
                    else:
                        substring = s3_file.key.split("/")[-1]
                        if substring.startswith(str(vidID)) and 
                                    str(patID) in substring and 
                                    substring.endswith(".webm") and 
                                    "Test" not in substring:
                            
                            #Correct video found
                            print("Analyzing "+ s3_file.key +" video...")
                            vidName = substring.split('.')[0]
                            vidNameNoSpaces = vidName.replace(" ","_space_")

                            #Create image directory for specific video
                            imgFullPath = imgPath+vidNameNoSpaces+"/images/"
                            if not os.path.exists(imgFullPath):
                                os.makedirs(imgFullPath)

                            #Download video from S3 
                            print("Downloading video from S3...")
                            vidFullPath=vidPath+vidNameNoSpaces+"/video/"
                            if not os.path.exists(vidFullPath):
                                os.makedirs(vidFullPath)
                            
                            s3.Bucket(VIDEO_BUCKET_NAME).download_file(s3_file.key, vidFullPath+substring)
                            print("Finished downloading video")

                            #Run main function to determine contour info of images in video
                            analyzeContour(vidFullPath, substring, vidNameNoSpace, imgFullPath, contourCSV, row)

                            #Remove video
                            print("Done analyzing, removing current video file...")
                            os.remove(videoFullPath)

                            #Move image folder to S3
                            source = imgFullPath
                            destination = 's3://'+str(IMAGE_BUCKET_NAME)+'/'
                            uploadToS3('mv', source, destination)
                            
                            #Update Tracking File
                            f = open(trackFile,'a')
                            f.write(str(s3_file.key)+'\n')
                            f.close()
                            print("Moving onto next video...\n")

                            #Updated vidFoundFlag
                            vidFoundFlag = 1

                #In case video listed in CSV was not found in S3:
                if vidFoundFlag == 0:
                    print("Not analyzing "+ s3_file.key +" because it is not a valid video or cannot be used")
        
    cv2.destroyAllWindows()

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Find Contours of video')
    argparser.add_argument('-r', '--root_dir', default=os.path.join(os.environ['HOME'], 'Videos'), help='root directory')
    argparser.add_argument('-d', '--out_dir', help='output directory')
    argparser.add_argument('-v', '--video', help='video')
    args = argparser.parse_args()
    main(args)    