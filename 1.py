import pygame
from pygame.locals import *

import numpy as np
import random
import time
import copy
import os
from ball_class import *
from pymetawear.client import MetaWearClient

os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'

### VARIABLES ###
# Boolean :
key_pressed = False
exp = True
print_name_baseline = False
estimate_mean_acc_baseline = False
estimate_mean_acc_acquisition = False
estimate_mean_acc_extinction = False

#Window, balls and sounds :
#Window :
background_color = (0, 0, 0) #color of the  bg
W, H = 1024, 768 #size of the window
text_color = (255, 255, 255) #color of the text
text_size = 40 #size of the text

#Initialization of pygame :
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode([W, H])

objNameToObjClass = {'ball':ball_class, 'ball_change_ray':ball_change_ray, 'moving_img': moving_img}
#Ball :
geoObj={
        #'obj1':
        #{
        #        'name': 'ball',
        #        'color': (255,0,0),
        #        'radius':80,
        #        'trajectory':
        #        {
        #                'name'      : 'circle',
        #                'center'    : [W/2,H/2],
        #                'radius'    : 200,
        #                'start_vel' : [1,-1]
        #        }
        #}
        'obj2':
        {
                'name': 'moving_img',
                'load_img': 'character.png',
                'trajectory':
                {
                        'name'      : 'straight',
                        'start_pos' : [W/2,H/2],
                        'start_vel' : [1,-1]
                }
        }
        # 'obj2':
        # {
        #         'name': 'ball_change_ray',
        #         'color': (255,255,0),
        #         'radius':65,
        #         'max_radius': 70,
        #         'min_radius': 25,
        #         'trajectory':
        #         {
        #                 'name'      : 'circle',
        #                 'start_vel' : [1,-1],
        #                 'radius'    : 200,
        #                 'center'    : [W/2,H/2]
        #         }
        # },
        # 'obj3':
        # {
        #         'name': 'ball',
        #         'color': (255,0,0),
        #         'radius':20,
        #         'trajectory':
        #         {
        #                 'name'      : 'circle',
        #                 'center'    : [W/2,H/2],
        #                 'radius'    : 200,
        #                 'start_vel' : [1,-1]
        #         }
        # }
}

ball_lst = []
ky = geoObj.keys()
ky.sort()
for bl in ky:
        class_name = geoObj[bl]['name']
        ball_lst.append(objNameToObjClass[class_name](**geoObj[bl]))

step_location = 0
#Sounds :
sounds = ["bg.ogg", "tiny2.ogg"] #sounds
bg_sound = sounds[0] #sound of the background
volume_bg = 0.2 #volume of the background sound when the character is not moving
volume_bg_mov = 1.0 #volume of the background sound when the character moves
mov_sound = sounds[1] #sound when the character moves
volume_mov_sound = 0.07 #volume of the sound when the character moves

#Data metaWear :
backend = 'pygatt'  # Or 'pybluez'
c = MetaWearClient("DA:FA:3A:2B:36:A4", backend) #D0:97:0F:A0:10:3B #D2:72:86:29:51:11 #DA:FA:3A:2B:36:A4
data_out = [[]] #data from the accelerometer

#Calibration gravity :
low_pass_acc = np.zeros(3)

#Duration experiment :
duration_baseline    = 0.1 #duration of the acquisition (in minute)
duration_acquisition = 1.0 #duration of the acquisition (in minute)
duration_extinction  = 0.1 #duration of the acquisition (in minute)
end_baseline = duration_baseline * 60000  #time at which the baseline ends (in ms)
end_acquisition = (duration_baseline + duration_acquisition) * 60000  #time at which the acquisition ends (in ms)
end_extinction = (duration_baseline + duration_acquisition + duration_extinction) * 60000  #duration at which the extinction ends (in ms)

#State of the experiment :
phase = "Start" #initialization

#Acceleration :
loop_period_acc = 10.0 #loop period measuring acceleration (in ms)
curr_time_acc = 0.0 #to calculate loop period acceleration (in ms)
prev_time_acc = 0.0 #to calculate loop period acceleration (in ms)
acc_x = 0.0 #acceleration in x
acc_y = 0.0 #acceleration in y
acc_z = 0.0 #acceleration in z
list_acc = [] #all accelerations (x,y,z)
mod = 0.0 #current acceleration (module)
list_mod = [] #all modules

#Running mean :
w_prev = 0.015 #weight of previous data
w_curr = 1.0 - w_prev #weight of new data
rm = 0.0 #running mean
list_rm_baseline = [] #all running means during baseline
list_rm_acquisition = [] #all running means during acquisition
list_rm_extinction = [] #all running means during extinction

#Movements of the character (used in acquisition):
force_change  = 0
force         = 0.04  #force applied to movements of the ball
friction      = 0.01  #friction applied to movements of the ball
step_location = 0     #step of the movements of the ball
max_displace  = 20.0  #maximum displacement each ref_period

#Screen refreshing
ref_period    = 20.0  #refreshing screen period (ms)

### FUNCTIONS ###
def acc_callback(data): #data from bracelets
        data_out[0] = copy.deepcopy(data) 

def accel(data_out): #acceleration (x,y,z)
    if len(data_out[0]) > 0:
        acc = list(data_out[0][1]) #list of 3 values (x,y,z)
    else :      
        acc = [0,0,0]
    return (acc) #list of 3 values  


### SETTINGS ###
#Setup the sensor :
c.accelerometer.set_settings(data_rate=50.0, data_range=4.0)
c.accelerometer.high_frequency_stream = False
c.accelerometer.notifications(acc_callback)

#Information on the subject :
age = raw_input("Age of the baby : ") #age
number = raw_input("Number of the baby : ") #number
condition = raw_input("Condition done by the baby (R = right and L = left) : ") #condition
sex = raw_input("Sex of the baby (F = female and M = male) : ") #sex

#Opening of a file :
p = open("{ag}_{num}_{cond}.txt".format(ag=age, num=number, cond=condition), "w")
# Print the names of the columns :
print >> p, "NUMBER", "AGE", "CONDITION", "SEX", "TIME", "PHASE", "ACC_X", "ACC_Y", "ACC-Z", "MOD", "FORCE", "RM"


#Opening pygame window - set parameters of this window : 
font = pygame.font.Font(None, text_size)

#Loading sounds for pygame :
pygame.mixer.music.load(bg_sound)
pygame.mixer.music.set_volume(volume_bg)
mov_sound = pygame.mixer.Sound(mov_sound)
mov_sound.set_volume (volume_mov_sound)


### PROGRAM ###
#Start : wait for "space" press to start
start = font.render('Press <SPACE> to start', True, text_color, background_color)
size_start = start.get_size()
start_x = W/2 - size_start[0]/2
start_y = H/2 - size_start[1]/2
screen.fill((0, 0, 0))
screen.blit(start, (start_x, start_y))
pygame.display.flip()
while not key_pressed:
    for e in pygame.event.get():
         if e.type == pygame.QUIT:
            pygame.quit()
            print("Unsubscribe to notification...")
            c.accelerometer.notifications(None)
            time.sleep(5.0)
            c.disconnect()
            time.sleep(2.0)
            print("Done")
         if e.type == KEYDOWN and e.key == K_SPACE:
            key_pressed = True

#Beginning of the experiment :
t0 = time.time() #takes the time when the experiment starts
#pygame.mixer.music.play(-1) #play bg music continuously
step_location_float = 0.0
old_step_location = 0
cnt_acq = 0
last_screen_ref = time.time()
last_change     = time.time()
### MAIN LOOP ###
while exp:
    time.sleep(0.005)
    ### MANUAL COMMANDS ###
    #quit the program :
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exp = False
        #keys to press to change the threshold value or the rm value (weight of the previous rm) :
        if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_z:
                        force_change =  1
                if e.key == pygame.K_s:
                        force_change = -1

    #change of the rm value (weight of the previous rm):                   
    if force_change != 0:
        if force_change == 1:
            force  += 0.003
        else:
            force -= 0.003
        force_change = 0
        #miminum and maximum of the rm value (weight of the previous rm) :
        if force > 1.:
           force = 1.
        if force < 0.:
           force = 0.
       
        print "New value of force:", force

            
    ### TIMER ###
    #time spent from the beginning of the experiment :
    spent = (time.time() - t0)*1000 #in ms

    
    ### ACCELERATION ####
    #reading of the data from the sensor, calculation of the module, calculation of the running mean and print the data in the file
    curr_time_acc = time.time() #takes the current time
    if (((curr_time_acc - prev_time_acc)*1000) > loop_period_acc): #step of data recording
        prev_time_acc = curr_time_acc #updates prev_time
        acc_array = accel(data_out) #array of the acceleration in x, y, z (reading the data from the sensors)
        acc_x = acc_array[0] #acceleration in x
        acc_y = acc_array[1] #acceleration in y
        acc_z = acc_array[2] #acceleration in z
        list_acc.append(acc_array) #list of acc (acc = array of 3 values, add the current acc at each step)
        low_pass_acc = 0.9 * low_pass_acc + 0.1 * np.asarray(acc_array)
        mod = ((low_pass_acc - np.asarray(acc_array))**2).sum()
        list_mod.append(mod) #list of modules (mod = single value, add the current module at each step)
        rm = w_prev*rm + w_curr*list_mod[-1] # rm = current running mean, list_mod[-1] = precedent value of the running mean
        print >> p, number, age, condition, sex, spent, phase, acc_x, acc_y, acc_z, mod, force, rm #prints all data in a file
        
        
    ### PYGAME ###
    
    #refreshing pygame window:
    if (time.time() - last_screen_ref)*1000.0 > ref_period:     
        last_screen_ref = time.time()
        screen.fill((0, 0, 0))
        for bl in ball_lst:
                bl.draw(screen)
        pygame.display.flip()

        
    ### BASELINE ###
    #if in baseline : prints current phase, setups color of plot, list of rm 
    if (spent <= end_baseline) :
        phase = "Baseline"
        list_rm_baseline.append(rm) #list of rm in baseline (rm = single value, add the current rm at each step)
        
        if not print_name_baseline : #print the name of the current phase (=baseline)
                print_name_baseline = True
                print phase

                
    ### ACQUISITION ###
    #if in acquisition : prints mean rm and loop duration in baseline - prints current phase, setups color of plot, list of rm, updates the picture and volume (movements)
    if (spent > end_baseline and spent <= end_acquisition):
        phase = "Acquisition"
        list_rm_acquisition.append(rm) #list of rm in acquisition (rm = single value, add the current rm at each step) 
        cnt_acq +=1
        
        #calculates mean rm in baseline, sets up the threshold, prints mean rm and loop duration of baseline and the name of the current phase (=acquisition), setups last_change:
        if not estimate_mean_acc_baseline:
                start_acq = time.time()
                estimate_mean_acc_baseline = True
                mean_acc_baseline = np.asarray(list_rm_baseline).mean() #single value = mean of all rm recorded during the baseline
                print("Mean of acceleration during the baseline :")
                print mean_acc_baseline #mean rm in baseline
                print phase #current phase (=acquisition)
                last_change = spent #setups last_change for future movements (= last time a change occurred)
                
        #Movements of the character :
        if ((time.time() - last_change)*1000.0 > ref_period) :
                step_location_float = step_location_float + force * rm**(0.5) * (ref_period/2.0)**(2.0) - friction*step_location_float*ref_period/2.0 #force and friction applied to the ball
                if step_location_float > max_displace:
                        step_location_float = max_displace
                step_location       = int(step_location_float)
                last_change         = time.time()

                for bl in ball_lst:
                        bl.next_pos(step_location, H, W)

                        
                if old_step_location < 2 and step_location >= 2:
                     mov_sound.play() #plays the sound for movements 

                old_step_location = step_location

    ### EXTINCTION ###
    #if in extinction : prints mean rm and loop duration in acquisition - prints current phase, setups color of plot, list of rm, puts picture and volume at their initial state
    if (spent > end_acquisition and spent <= end_extinction) :
        phase = "Extinction"
        list_rm_extinction.append(rm) #list of rm in extinction (rm = single value, add the current rm at each step)
        step_location = int(step_location - friction*step_location) #friction : stops the ball after some loops

        #calculates mean rm in acquisition, prints mean rm and loop duration of acquisition and the name of the current phase (=extinction), puts the character/volume to their initial state
        if not estimate_mean_acc_acquisition :
                print (time.time() - start_acq)/float(cnt_acq)
                estimate_mean_acc_acquisition = True
                mean_acc_acquisition = np.asarray(list_rm_acquisition).mean() #single value = mean of all rm recorded during the acquisition
                print("Mean of acceleration during the acquisition :")
                print mean_acc_acquisition #mean rm in acquisition
                print phase #current phase (=extinction)
        

    ### CLOSING ###
    #if in closing : prints mean rm in extinction - prints current phase, closes the experiment
    if (spent > end_extinction) : 
        phase = "Close"

        #calculates mean rm in extinction, prints mean rm of extinction and current phase (=closing)
        if not estimate_mean_acc_extinction :
                mean_acc_extinction = np.asarray(list_rm_extinction).mean() #single value = mean of all rm recorded during the extinction
                estimate_mean_acc_extinction = True
                print("Mean of acceleration during the extinction :")
                print mean_acc_extinction #mean rm in extinction
                print phase #current phase (=closing)
                
        exp = False #end of the experiment

        
### OUT OF THE MAIN LOOP ###
#End :say thanks and disconnects the MetaWears :
end = font.render('Merci pour votre participation !', True, text_color, background_color) #defines text
size_end = end.get_size()
end_x = W/2 - size_end[0]/2
end_y = H/2 - size_end[1]/2
screen.fill((0, 0, 0))
screen.blit(end, (end_x, end_y))
pygame.display.flip()
print("Unsubscribe to notification...")
c.accelerometer.notifications(None)
time.sleep(5.0)
c.disconnect()
time.sleep(2.0)
print("Done")

#Close the file and Pygame :
p.close
pygame.quit()
