from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


import pygame
from pygame.locals import *

import numpy as np
import random
import time
import copy
import os
import cPickle as pickle
import gzip
from ball_class import *
#from pymetawear.discover import select_device
from pymetawear.client import MetaWearClient
from pymetawear import libmetawear
from attentionGather_class import *

os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'

### VARIABLES ###
# Boolean :
key_pressed = False
exp = True
print_name_baseline = False
print_name_acquisition = False
print_name_extinction = False
print_name_closing = False

address_1 = 'CF:F5:53:13:C7:1E'
address_2 = 'CE:B3:19:9A:A2:E6'

print("Connect to {0}...".format(address_1))
client_1 = MetaWearClient(str(address_1), timeout=10.0, debug=False)
libmetawear.mbl_mw_settings_set_connection_parameters(client_1.board, 7.5, 7.5, 0, 6000)
print("New client created: {0}".format(client_1))
print("Connect to {0}...".format(address_2))
client_2 = MetaWearClient(str(address_2), timeout=10.0, debug=False)
libmetawear.mbl_mw_settings_set_connection_parameters(client_2.board, 7.5, 7.5, 0, 6000)
print("New client created: {0}".format(client_2))


#Window, balls and sounds :
#Window :
background_color = (0, 0, 0) #color of the  bg
W, H             = 1024, 768 #size of the window
text_color       = (255, 255, 255) #color of the text
text_size        = 40 #size of the text


#Screen refreshing
ref_period = 20.0  #refreshing screen period (ms)

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
        'obj1':
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
}

ball_lst = []
ky = geoObj.keys()
ky.sort()
for bl in ky:
        class_name = geoObj[bl]['name']
        ball_lst.append(objNameToObjClass[class_name](**geoObj[bl]))

#attention ghater
file_audio = ['Kev1.ogg', 'Kev2.ogg', 'Kev3.ogg']
screen_size = screen.get_size()
attGath = att_gather(duration=1.5, period=60.0, screen_size=screen_size, n_repetition=2, volume=0.07, list_audio = file_audio)

# attGath.audio[0].play()
# time.sleep(3.0)
# attGath.audio[0].stop()

#Sounds :
sounds = ["bg.ogg", "tiny2.ogg"] #sounds
bg_sound = sounds[0] #sound of the background
volume_bg = 0.2 #volume of the background sound when the character is not moving
volume_bg_mov = 1.0 #volume of the background sound when the character moves
mov_sound = sounds[1] #sound when the character moves
volume_mov_sound = 0.07 #volume of the sound when the character moves
    
#MetaWear
#Device 1
data_out1 = [[]]

def acc_callback1(data1):
    data_out1[0]  = data1[1][:]

def accel1(data_out1):
   if len(data_out1[0]) > 0:
       accs1 = list(data_out1[0]) 
   else :      
       accs1 = [0,0,0]
   return (accs1) 

client_1.accelerometer.set_settings(data_rate=50.0, data_range=4.0)
client_1.accelerometer.high_frequency_stream = True
client_1.accelerometer.notifications(acc_callback1)

#Device 2
data_out2 = [[]] 

def acc_callback2(data2):
    data_out2[0] = data2[1][:] 

def accel2(data_out2):
    if len(data_out2[0]) > 0:
        accs2 = list(data_out2[0]) 
    else :      
        accs2 = [0,0,0]
    return (accs2) 

client_2.accelerometer.set_settings(data_rate=50.0, data_range=4.0)
client_2.accelerometer.high_frequency_stream = True
client_2.accelerometer.notifications(acc_callback2)

#Calibration gravity :
low_pass_acc_cont = np.zeros(3)
low_pass_acc_non_cont = np.zeros(3)

#Duration experiment :
duration_baseline    = 0.0 #duration of the acquisition (in minute)
duration_acquisition = 6.0 #duration of the acquisition (in minute)
duration_extinction  = 2.0 #duration of the acquisition (in minute)
end_baseline = duration_baseline * 60000  #time at which the baseline ends (in ms)
end_acquisition = (duration_baseline + duration_acquisition) * 60000  #time at which the acquisition ends (in ms)
end_extinction = (duration_baseline + duration_acquisition + duration_extinction) * 60000  #duration at which the extinction ends (in ms)

#State of the experiment :
phase = "Start" #initialization

#Acceleration :
loop_period_acc = 10.0 #loop period measuring acceleration (in ms)
curr_time_acc   = 0.0 #to calculate loop period acceleration (in ms)
prev_time_acc   = 0.0 #to calculate loop period acceleration (in ms)
#Contingent bracelet:
list_acc_cont = [] #all accelerations (x,y,z)
mod_cont = 0.0 #current acceleration (module)
list_mod_cont = [] #all modules
#Non-contingent bracelet:
list_acc_non_cont = [] #all accelerations (x,y,z)
mod_non_cont = 0.0 #current acceleration (module)
list_mod_non_cont = [] #all modules

#Running mean :
w_prev = 0.015 #weight of previous data
#w_prev  = 0.1
w_curr  = 1.0 - w_prev #weight of new data
rm_cont = 0.0 #running mean contingent bracelet
rm_non_cont = 0.0 #running mean non-contingent bracelet

#Movements of the character (used in acquisition):
#force_change = 0 #used to change manually the force applied to movements
force = 0.04  #force applied to movements of the ball
friction = 0.01  #friction applied to movements of the ball
step_location = 0     #step of the movements of the ball
max_displace = 20.0  #maximum displacement each ref_period


### SETTINGS ###
#Information on the subject :
age       = raw_input("Age of the baby : ") #age
number    = raw_input("Number of the baby : ") #number
condition = raw_input("Condition done by the baby (R = right and L = left) : ") #condition
sex       = raw_input("Sex of the baby (F = female and M = male) : ") #sex

#Opening of a file :
save_dir = "../dataMetaExp/"
p = open(save_dir + "{ag}_{num}_{cond}.txt".format(ag=age, num=number, cond=condition), "w")
# Print the names of the columns :
print("NUMBER AGE CONDITION SEX TIME PHASE ACC_X_CONT ACC_Y_CONT ACC_Z_CONT MOD_CONT RM_CONT ACC_X_NON_CONT ACC_Y_NON_CONT ACC_Z_NON_CONT MOD_NON_CONT RM_NON_CONT", end ="\n" , file=p)


#Opening pygame window - set parameters of this window : 
font = pygame.font.Font(None, text_size)

#Loading sounds for pygame :
pygame.mixer.music.load(bg_sound)
pygame.mixer.music.set_volume(volume_bg)
mov_sound = pygame.mixer.Sound(mov_sound)
mov_sound.set_volume(volume_mov_sound)


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
            time.sleep(5.0)
            client_1.disconnect()
            time.sleep(5.0)
            client_2.disconnect()
            time.sleep(2.0)
            print("Done")
         if e.type == KEYDOWN and e.key == K_SPACE:
            key_pressed = True

#Beginning of the experiment :
t0 = time.time() #takes the time when the experiment starts
step_location_float = 0.0
old_step_location = 0
last_screen_ref = time.time()
last_change = time.time()
### MAIN LOOP ###
while exp:

    ### MANUAL COMMANDS ###
    #quit the program :
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exp = False
        #keys to press to change the threshold value or the rm value (weight of the previous rm) :
        #if e.type == pygame.KEYDOWN:
                #if e.key == pygame.K_z:
                        #force_change =  1
                #if e.key == pygame.K_s:
                        #force_change = -1

    #change of the rm value (weight of the previous rm):                   
    #if force_change != 0:
        #if force_change == 1:
            #force  += 0.003
        #else:
            #force -= 0.003
        #force_change = 0
        #miminum and maximum of the rm value (weight of the previous rm) :
        #if force > 1.:
           #force = 1.
        #if force < 0.:
           #force = 0.
       
        #print "New value of force:", force
            
    ### TIMER ###
    #time spent from the beginning of the experiment :
    spent = (time.time() - t0)*1000 #in ms
    
    ### ACCELERATION ####
    #reading of the data from the sensor, calculation of the module, calculation of the running mean and print the data in the file
    time.sleep(0.005)
    curr_time_acc = time.time() #takes the current time
    if (((curr_time_acc - prev_time_acc)*1000) > loop_period_acc): #step of data recording
        prev_time_acc = curr_time_acc #updates prev_time
        #Contingent bracelet :
        acc_cont  = accel1(data_out1)
        #list_acc_cont.append(acc_cont) #list of acc (acc = array of 3 values, add the current acc at each step)
        low_pass_acc_cont = 0.9 * low_pass_acc_cont + 0.1 * np.asarray(acc_cont)
        mod_cont = ((low_pass_acc_cont - np.asarray(acc_cont))**2).sum()
        #list_mod_cont.append(mod_cont) #list of modules (mod = single value, add the current module at each step)
        rm_cont = w_prev*rm_cont + w_curr*mod_cont #list_mod_cont[-1] # rm = current running mean, list_mod[-1] = precedent value of the running mean
        #Non-contingent bracelet :
        acc_non_cont = accel2(data_out2)
        #list_acc_non_cont.append(acc_non_cont) #list of acc (acc = array of 3 values, add the current acc at each step)
        low_pass_acc_non_cont = 0.9 * low_pass_acc_non_cont + 0.1 * np.asarray(acc_non_cont)
        mod_non_cont = ((low_pass_acc_non_cont - np.asarray(acc_non_cont))**2).sum()
        #list_mod_non_cont.append(mod_non_cont) #list of modules (mod = single value, add the current module at each step)
        rm_non_cont = w_prev*rm_non_cont + w_curr*mod_non_cont# rm = current running mean, list_mod[-1] = precedent value of the running mean
        #print >> p, number, age, condition, sex, spent, phase, acc_cont[0], acc_cont[1], acc_cont[2], mod_cont, rm_cont#, acc_non_cont[0], acc_non_cont[1], acc_non_cont[2], mod_non_cont, rm_non_cont
        print(str(number)+" "+str(age)+" "+condition+" "+sex+str(spent)+" "+phase+str(acc_cont[0])+" "+str(acc_cont[1])+" "+str(acc_cont[2])+ str(mod_cont) +" "+str(rm_cont)+" "+str(acc_non_cont[0])+" "+str(acc_non_cont[1])+ " " +str(acc_non_cont[2])+" "+str(mod_non_cont)+" "+str(rm_non_cont), end="\n", file=p)
        
        
    ### PYGAME ###
    
    #refreshing pygame window:
    if (time.time() - last_screen_ref)*1000.0 > ref_period:     
        last_screen_ref = time.time()
        screen.fill((0, 0, 0))
        if attGath.attention_check(time.time()):
            attGath.draw(screen)
        else:
          for bl in ball_lst:
              bl.draw(screen)
        pygame.display.flip()
        
    ### BASELINE ###
    #if in baseline : prints current phase, setups color of plot, list of rm 
    if (spent <= end_baseline) :
        phase = "Baseline"
        if not print_name_baseline : #print the name of the current phase (=baseline)
                print_name_baseline = True
                print(phase)

                
    ### ACQUISITION ###
    #if in acquisition : prints mean rm and loop duration in baseline - prints current phase, setups color of plot, list of rm, updates the picture and volume (movements)
    if (spent > end_baseline and spent <= end_acquisition):
        phase = "Acquisition"
        
        #print name of the current phase:
        if not print_name_acquisition:
                start_acq = time.time()
                print_name_acquisition = True
                print(phase) #current phase (=acquisition)
                last_change = spent #setups last_change for future movements (= last time a change occurred)
                
        #Movements of the character :
        if ((time.time() - last_change)*1000.0 > ref_period) :
                step_location_float = step_location_float + force * rm_cont**(0.5) * (ref_period/2.0)**(2.0) - friction*step_location_float*ref_period/2.0 #force and friction applied to the ball
                if step_location_float > max_displace:
                        step_location_float = max_displace
                step_location = int(step_location_float)
                last_change = time.time()

                for bl in ball_lst:
                        bl.next_pos(step_location, H, W)
                        bl.save_pos()
                        
                if old_step_location < 2 and step_location >= 2:
                     mov_sound.play() #plays the sound for movements 

                old_step_location = step_location

                
                
    ### EXTINCTION ###
    #if in extinction : prints mean rm and loop duration in acquisition - prints current phase, setups color of plot, list of rm, puts picture and volume at their initial state
    if (spent > end_acquisition and spent <= end_extinction) :
        phase = "Extinction"
        step_location = int(step_location - friction*step_location) #friction : stops the ball after some loops

        #print name of the current phase
        if not print_name_extinction :
                print_name_extinction = True
                print(phase) #current phase (=extinction)
        

    ### CLOSING ###
    #if in closing : prints mean rm in extinction - prints current phase, closes the experiment
    if (spent > end_extinction) : 
        phase = "Close"
        if not print_name_closing :
                print_name_closing = True
                print(phase) #current phase (=closing)
                
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

print("Saving data...")
balls_hist = []
for bl in ball_lst:
        balls_hist.append(bl.pos_hist)
                        
with gzip.open(save_dir + "{ag}_{num}_{cond}.pkl.gz".format(ag=age, num=number, cond=condition), "w") as f:
        pickle.dump(balls_hist, f, protocol=pickle.HIGHEST_PROTOCOL)
print("Done")


print("Unsubscribe to notification...")
time.sleep(5.0)
client_1.disconnect()
time.sleep(5.0)
client_2.disconnect()
time.sleep(2.0)
print("Done")


#Close the file and Pygame :
p.close
pygame.quit()
