from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread, Event
from gpiozero import MotionSensor, LED, Servo
import RPi.GPIO as GPIO
from time import sleep
from pygame import mixer
import random

app = Flask(__name__)
#socketio = SocketIO(app,async_mode=None, logger=True, engineio_logger=True, cors_allowed_origins="*")
socketio = SocketIO(app,async_mode=None, cors_allowed_origins="*")

thread = Thread()
thread_stop_event = Event()
 

pir = MotionSensor(4)
led = LED(3)
#servo = Servo(17)

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
servo1=GPIO.PWM(17, 50)
servo1.start(0)

scary_sounds = [ 'halloween1.mp3',
                 'halloween2.mp3',
                 'halloween3.mp3',
                 'halloween4.mp3',
                 'halloween5.mp3']

values = {
    'slider1': 25,
    'slider2': 0,
}

def play_sound():

    mixer.init()
    random_sound = random.choice(scary_sounds)
    print("playing " + random_sound)
    sound = mixer.Sound(random_sound)
    sound.play()
    
   

def activate_haunt():
    led.on()
    GPIO.output(17, True)
    servo1.start(0)
    play_sound()
     
    print("☠️☠️ Activating haunt ☠️☠️ ")

    for step in range(10):
        servo1.ChangeDutyCycle(5) # left -90 deg position
        sleep(1)
        servo1.ChangeDutyCycle(7.5) # neutral position
        sleep(1)
        servo1.ChangeDutyCycle(10) # right +90 deg position
        sleep(1)
        #servo.min()
       # sleep(.6)
       # servo.max()
       
       
    

        #sleep(.8)


    #turn off the light when the show is over    
    led.off()
    servo1.stop()
    #GPIO.cleanup()
 
def detect_motion():
    #global pir
    #   global led
    while not thread_stop_event.isSet():
        if pir.value == 1:
            print("Motion deteted!")
            socketio.emit('motion_value', {'data': "Server detects motion"}, namespace='/test')
            activate_haunt()

        else:
            print("All quiet")      
            socketio.emit('motion_value', {'data': "Server detects no motion"}, namespace='/test')
            
        socketio.sleep(.3)

@app.route('/')
def index():
    return render_template('index.html',**values)

@socketio.on('connect', namespace='/test')
def test_connect():

    global thread
    print('Client connected')

    #Start the PIR thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        emit('connecting',  {'data':'Starting motion detector...'})
        thread = socketio.start_background_task(detect_motion)
   
        

@socketio.on('Slider value changed')
def value_changed(message):
    values[message['who']] = message['data']
    emit('updated value', message, broadcast=True)

@socketio.on('motion update' , namespace='/test')
def report_motion(message):
    
    values[message['status']] = str(pir.value)
    emit('reporting motion', message, broadcast=True)


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)