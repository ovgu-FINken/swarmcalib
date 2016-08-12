#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  calibration.py
#  

import finkenPID
import time
#import json  #Remove unused module
import datetime
#To save the calibration parameters
import calibrationOutput
#from os import walk #Remove unused module

#ROS libraries... maybe the communication python files should have it
import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Pose2D
#Ivy cal node
import ivyModules.IvyCalibrationNode
import math
import numpy

class Calibrator:
    """Class to calibrate the copter"""

    
    def __init__(self):
    #Here we can put some default variables for deadzone, targetzone and pollingTime and PID parameters
        self.targetXController = finkenPID.PIDController(0.01, 0.0000001, 0) #I set it to zero here for zero control
        self.targetYController = finkenPID.PIDController(0.01, 0.0000001, 0)
        self.copterXPos = 1 #Just to test
        self.copterYPos = 1 #Just to test
        self.copterTheta = 0;
        self.calibrationParameters = [0,0]
        self.myIvyCalNode = ivyModules.IvyCalibrationNode.IvyCalibrationNode()
        self.airBlockInteger = 2
        self.emptyBlockInteger = 1
        self.landingBlockInteger = 4
        self.accumulatedTime = 0
        self.isInSamePosition = False
    
    #Important INIT
    def setBasePosition(self, posX, posY):
        self.baseX = posX
        self.baseY = posY
    
    #Important INIT
    def setDeadZone(self, minX, maxX, minY, maxY):
        self.minX = minX
        self.maxX = maxX
        self.minY = minY
        self.maxY = maxY

    #Important INIT
    def setPollingTime(self, pollingTime):
        self.pollingTime = pollingTime
        self.accumulatedTime = pollingTime
        
    #Important INIT
    def setAircraftID(self, aircraftID):
        self.aircraftID = aircraftID
        
    def getXYCoordinates(self):
         #Call here the ivy method, it should return XY coordinates
         #We will set here 
         #self.copterXPos
         #self.copterYPos
         myObj = self.myIvyCalNode.IvyGetPos()
         self.isInSamePosition = (self.copterXPos == myObj.x) and (self.copterYPos == myObj.y)
         self.copterXPos = myObj.x
         self.copterYPos = myObj.y
         self.copterTheta = myObj.theta
         print("X: "+str(self.copterXPos) + " Y: "+str(self.copterYPos) + " Theta: " + str(self.copterTheta))
         
    def killCopter(self):
        #Call kill copter command
        print("Copter Kill signal")
        self.myIvyCalNode.IvySendKill(self.aircraftID)
        time.sleep(0.1)
        self.myIvyCalNode.IvySendSwitchBlock(self.aircraftID,self.emptyBlockInteger)
        return
        
    def unkillCopter(self):
        print("Unkilling Copter")
        self.myIvyCalNode.IvySendUnKill(self.aircraftID)
        return
        
    def sendStartMode(self):
        print("Sending start mode")
        self.myIvyCalNode.IvySendSwitchBlock(self.aircraftID,self.emptyBlockInteger)
        time.sleep(0.1)
        self.myIvyCalNode.IvySendSwitchBlock(self.aircraftID,self.airBlockInteger)
        
    def sendPitch(self, pitchToSend):
        #Call send pitch
        return
        
    def sendRoll(self, rollToSend):
        #Call send roll
        return
        
    def sendParametersToCopter(self, pitchToSend, rollToSend, yawToSend):
        #IvyCalibrationNode.IvySendParams
        print("roll: "+str(rollToSend)+" pitch: "+str(pitchToSend))
        print()
        self.myIvyCalNode.IvySendCalParams(self.aircraftID, 0, rollToSend, pitchToSend, yawToSend)
        return
        
    def sendYaw(self):
        #Call send yaw, I think this one is not required.
        return
        
    def followTarget(self):
        if (self.isInSamePosition):
            self.accumulatedTime += self.pollingTime
            return #We do a check if it is in the same position, as this is very unlikely we simply get out of the function and return to the main code
        errorX = (self.copterXPos - self.baseX) 
        errorY = (self.copterYPos - self.baseY)
        coord = numpy.array([errorX,errorY])
        self.copterTheta=self.copterTheta*math.pi/180
        translationMatrix = numpy.matrix([[math.cos(self.copterTheta), math.sin(self.copterTheta)], [-math.sin(self.copterTheta), math.cos(self.copterTheta)]])
        newCoord = numpy.dot(translationMatrix,coord)
        #print(newCoord);
        errorX = newCoord.item(0)
        errorY = newCoord.item(1)
        print('ErrorX: '+str(errorX)+' ErrorY: '+str(errorY))

        rollToSend = self.targetXController.step(errorY, self.accumulatedTime)
        pitchToSend = self.targetYController.step(errorX, self.accumulatedTime)
        #self.sendPitch(pitchToSend)
        #self.sendRoll(rollToSend)
        self.sendParametersToCopter(pitchToSend, -rollToSend, 0)
        #Save in list constantly
        self.calibrationParameters = [pitchToSend, rollToSend]
        self.accumulatedTime = self.pollingTime 
        
    def isInDeadZone(self):
        if ((self.copterXPos > self.maxX) or (self.copterXPos < self.minX) 
            or (self.copterYPos > self.maxY) or(self.copterYPos < self.minY)):
            self.killCopter();
            return True
        return False

myCalibrator = Calibrator()
#myCalibrator.setDeadZone(-0.2,1.0,-0.1,2.1) #minX, maxX, minY, maxY
myCalibrator.setDeadZone(250,1250,250,950) #minX, maxX, minY, maxY
myCalibrator.setBasePosition(750,600)
myCalibrator.setPollingTime(0.005)
myCalibrator.setAircraftID(5)
myCalibrator.myIvyCalNode.IvyInitStart()
myCalibrator.myIvyCalNode.IvySendCalParams(myCalibrator.aircraftID, 0, 0, 0, 0)
myCalibrator.unkillCopter()
myCalibrator.sendParametersToCopter(0, 0, 0)
time.sleep(3) #For the camera to detect the initial position
myCalibrator.sendStartMode() #I uncommented this for simulation purposes
time.sleep(1.75) #When the copter turns on, there are no lights until a few seconds
i = 0;
while(i<=10000000):
    myCalibrator.getXYCoordinates()
    if (myCalibrator.isInDeadZone()):
        myCalibrator.killCopter()
        #save calibration parameters.. the filename will be a timestamp
        calibrationOutput.saveObject(myCalibrator.calibrationParameters,'')
        myCalibrator.myIvyCalNode.IvyInitStop()
        break;
    #time.sleep(3)
    myCalibrator.followTarget()
    i=i+1
    time.sleep(myCalibrator.pollingTime)
    
myCalibrator.myIvyCalNode.IvySendSwitchBlock(myCalibrator.aircraftID,myCalibrator.landingBlockInteger)
time.sleep(2)
myCalibrator.killCopter()
print("ProgramEnded")
raise SystemExit()



