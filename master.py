import RPi.GPIO as GPIO
import time
import dht11
from gpiozero import LightSensor
import datetime
import smtplib

def initpins():     #fn for initializing pins
    Motor1Pin1=17    #pins for motor-driver1
    Motor1Pin2=18
    Motor1Enable=27

    Motor2Pin1=8	 #pins for motor-driver2
    Motor2Pin2=11
    Motor2Enable=9

    ldr1 = LightSensor(4)	#pins for LDRs
    ldr2 = LightSensor(22)

    SPICLK=19	#pins for waterlvl sensor 
    SPIMISO=13
    SPIMOSI=6
    SPICS=16
    photo_ch=0
    channel=20	#pin for water-pump

    temp = dht11.DHT11(pin=21)	#pin for dht

    GPIO.setwarnings(False)
    GPIO.cleanup()
            
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(Motor1Pin1,GPIO.OUT)
    GPIO.setup(Motor1Pin2,GPIO.OUT)
    GPIO.setup(Motor1Enable,GPIO.OUT)
    GPIO.output(Motor1Enable,GPIO.LOW)

    GPIO.setup(Motor2Pin1,GPIO.OUT)
    GPIO.setup(Motor2Pin2,GPIO.OUT)
    GPIO.setup(Motor2Enable,GPIO.OUT)
    GPIO.output(Motor2Enable,GPIO.LOW)
        
    GPIO.setup(SPIMOSI, GPIO.OUT)
    GPIO.setup(SPIMISO, GPIO.IN)
    GPIO.setup(SPICLK, GPIO.OUT)
    GPIO.setup(SPICS, GPIO.OUT)
    GPIO.setup(channel,GPIO.OUT)

def readadc(adcnum, clockpin, mosipin, misopin, cspin):    #utility fn for reading water-level
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)	
        GPIO.output(clockpin, False)  
        GPIO.output(cspin, False)
        commandout = adcnum
        commandout |= 0x18
        commandout <<= 3
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        adcout >>= 1
        return adcout

def moveright():    #utility fn for moving platform to the right
    print("right is registering more light")
    GPIO.setmode(GPIO.BCM)
    PIN_TRIGGER1 = 23
    PIN_ECHO1 = 24
    GPIO.setup(PIN_TRIGGER1,GPIO.OUT)
    GPIO.setup(PIN_ECHO1,GPIO.IN)
    GPIO.output(PIN_TRIGGER1,False)
    time.sleep(0.5)
    GPIO.output(PIN_TRIGGER1,True)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER1,False)
    while GPIO.input(PIN_ECHO1)==0:
        pulse_start_time1=time.time()
    while GPIO.input(PIN_ECHO1)==1:
        pulse_end_time1=time.time()
    pulse_duration1=pulse_end_time1-pulse_start_time1
    distance1=round(pulse_duration1*17150)
    distance1 = round(distance1,2)
    if distance1<15:
        print("obstacle detected, stopping motors")
        GPIO.output(Motor1Enable,GPIO.LOW)
    else:
        print("rotating the motors clockwise")
        GPIO.output(Motor1Enable,GPIO.HIGH) #motor1
        GPIO.output(Motor1Pin1,GPIO.HIGH)
        GPIO.output(Motor1Pin2,GPIO.LOW)
        time.sleep(0)
        GPIO.output(Motor2Enable,GPIO.HIGH) #motor2
        GPIO.output(Motor2Pin1,GPIO.HIGH)
        GPIO.output(Motor2Pin2,GPIO.LOW)
        time.sleep(0)

def moveleft(): #utility fn for moving platform to the left
    print("left is registering more light")
    GPIO.setmode(GPIO.BCM)
    PIN_TRIGGER2 = 10
    PIN_ECHO2 = 25
    GPIO.setup(PIN_TRIGGER2,GPIO.OUT)
    GPIO.setup(PIN_ECHO2,GPIO.IN)
    GPIO.output(PIN_TRIGGER2,False)
    time.sleep(0.5)
    GPIO.output(PIN_TRIGGER2,True)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER2,False)
    while GPIO.input(PIN_ECHO2)==0:
        pulse_start_time2=time.time()
    while GPIO.input(PIN_ECHO2)==1:
        pulse_end_time2=time.time()
    pulse_duration2=pulse_end_time2-pulse_start_time2
    distance2=round(pulse_duration2*17150)
    distance2 = round(distance2,2)
    if distance2<15:
        print("obstacle detected, stopping motors")
        GPIO.output(Motor1Enable,GPIO.LOW)
    else:
        print("rotating the motors anticlockwise")
        GPIO.output(Motor1Enable,GPIO.HIGH) #motor1
        GPIO.output(Motor1Pin1,GPIO.LOW)
        GPIO.output(Motor1Pin2,GPIO.HIGH)
        time.sleep(0)
        GPIO.output(Motor2Enable,GPIO.HIGH) #motor2
        GPIO.output(Motor2Pin1,GPIO.LOW)
        GPIO.output(Motor2Pin2,GPIO.HIGH)
        time.sleep(0)

def waterpump():    #utility fn for switching the water pump on and off
    adc_value=readadc(photo_ch, SPICLK, SPIMOSI, SPIMISO, SPICS)	#o/p for waterlvl
    print("water level= " +str(adc_value)+"\n")
    if int(adc_value)>150:			#condition for pump 
            print("switching pump on")
        GPIO.output(channel,GPIO.LOW)
    time.sleep(0.5)
    if int(adc_value)<150:
        GPIO.output(channel,GPIO.HIGH)

def sendmail():    #utility fn for sending mail
    result = instance.read()	#reading the temp
    if result.is_valid():
        #print("Temperature: %d C" % result.temperature)
        #print("Humidity: %d %%" % result.humidity)
        if result.temperature>30:
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.ehlo()

            username='(put your mail address over here, eliminate the brackets)'
            password='(put your mail password over here, eliminate the brackets)'
            s.login(username,password)

            replyto='(put the mail address you wish to get a reply to, eliminate the brackets)' 
            sendto=['(put the mail address you wish to send the mail to, eliminate the brackets)'] 
            sendtoShow='me@me.com' 
            subject='Temperature'
            content="The temperature right now is "+str(result.temperature)+". This mail has been sent to you because the current temperature is well above your plant's tolerable limit. Please put your plant in a cooler place. Thank you." # content 

            mailtext='From: '+replyto+'\nTo: '+sendtoShow+'\n'
            mailtext=mailtext+'Subject:'+subject+'\n'+content

            s.sendmail(replyto, sendto, mailtext)
            rslt=s.quit()
            print('Mail sent successfully' + str(rslt[1]))

initpins();

try:
    while True:
        if ldr1.value==0.0 and ldr2.value==0.0: 
            print("equally lit, no movement")
            GPIO.output(Motor1Enable,GPIO.LOW)
            GPIO.output(Motor2Enable,GPIO.LOW) 

        elif ldr2.value<ldr1.value:
            moveright()

        elif ldr1.value<ldr2.value:
            moveleft()

        else:
            print("equally dark, no movement")
            GPIO.output(Motor1Enable,GPIO.LOW)
            GPIO.output(Motor2Enable,GPIO.LOW)

        waterpump()
        sendmail()
            
finally:
    GPIO.cleanup()