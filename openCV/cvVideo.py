import cv2
import numpy as np
import argparse
import os


class cvVideo:
    def __init__ (self, path=None, vid=0, startIdx=0, outputPath=None, codec='XVID'):
        self.vid  = vid
        self.path = path
        self.idx  = startIdx
        self.outputPath = outputPath

        self.cap = cv2.VideoCapture(path+'/'+vid)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES,startIdx)
        print("Vid Init: ", self.vid)

        self.fps          = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame_count  = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        #Video Writer variables
        self.fourcc = None
        self.codec  = codec
        self.writer = None
        

    #Display function
    def displayInfo(self):
        print("\n[I] Video Info:\n")
        print('{0:<15} {1}'.format("FPS: ", self.fps))
        print('{0:<15} {1}'.format("Frame Count: ", self.frame_count))
        print('{0:<15} {1}'.format("Frame Width: ", self.frame_width))
        print('{0:<15} {1}'.format("Frame Height:", self.frame_height))
        print('{0:<15} {1}'.format("Frame Index: ", self.idx))
        print("\n\n")

    #Accessor functions


    #Setter functions


    #Writer functions
    def recordOutput(self)
        self.fourcc = cv2.VideoWriter_fourcc(*'{self.codec}')
        self.writer = cv2.VideoWriter(self.outputPath, self.fourcc, self.fps, (self.frame_width,self.frame_height))

    def releaseOut(self)
        self.writer.release()

    #Reader functions
    def readFrame(self):
        self.idx += 1
        ret, frame = self.cap.read()
        return ret, frame

        # if ret:
        #     return ret, frame
        # else:
        #     print("Done")    

    def showFrame(self):
        cv2.imshow('frame', self.readFrame()[1])
        # print(f'{self.idx}')
        if cv2.waitKey(100) & 0xFF == ord('q'):
            return

    def runVideo(self):
        while self.cap.isOpened():
            self.showFrame()
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break


    def release(self):
        self.cap.release()


    #Transformation functions
    def gray(frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return gray




def procedural(args):
    cap = cv2.VideoCapture(f'{args.root_dir}/{args.video}')
    print('{0:<15} {1}'.format("FPS: ", int(cap.get(cv2.CAP_PROP_FPS))))
    while(cap.isOpened()):
        ret, frame = cap.read()
        print("In open")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        cv2.imshow('frame',gray)
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def run(args):
    # print("Dir: ", args.root_dir)
    # print("Video: ", args.video)
    
    vid = cvVideo(path= args.root_dir, vid= args.video, startIdx=500)
    vid.displayInfo()

    # for i in range(10):
    #     vid.showFrame()

    vid.runVideo()

    vid.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='Load Video into OpenCV')
    parser.add_argument('-r', '--root_dir', default=os.path.join(os.environ['HOME'], 'Videos'), help='root directory')
    parser.add_argument('-v', '--video', help='video')
    args = parser.parse_args()
    run(args)
    
if __name__ == "__main__":
    main()
