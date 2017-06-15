import numpy as np
import random


class traj(object):

    def __init__(self, **kwargs):

        if 'start_pos' in kwargs:
            self.pos = kwargs['start_pos']
        else:
            self.pos = [0,0]


    def next_pos(self, **kwargs):
        pass


class circle_traj(traj):

    def __init__(self, **kwargs):
        super(circle_traj, self).__init__(**kwargs)
        self.center  = kwargs['center']
        self.radius  = kwargs['radius']
        self.vel     = kwargs['start_vel']    
        self.pos     = self.center + self.radius*np.asarray([1,0], dtype=np.float)
        
    def next_pos(self, **kwargs):
        obj  = kwargs['obj']
        H    = kwargs['H'] 
        W    = kwargs['W']
        disp = kwargs['disp']

        pos = obj.pos
        vel = self.vel
        
        pos[0] = pos[0] - self.center[0]
        pos[1] = pos[1] - self.center[1]

        if pos[1] >= 0:
            theta = np.arccos(float(pos[0])/float(self.radius))
        else:
            theta = np.pi + np.arccos(float(-pos[0])/float(self.radius))
         
        D_theta  = 2.0 * float(disp)/(np.pi * float(self.radius))

        pos[0]    = self.center[0] + self.radius * np.cos(theta + D_theta)
        pos[1]    = self.center[1] + self.radius * np.sin(theta + D_theta)
        
        return pos
        
        
class strait_traj(traj):

    def __init__(self, **kwargs):
        super(strait_traj, self).__init__(**kwargs)
        self.vel     = kwargs['start_vel']    

    def next_pos(self, **kwargs):
        obj  = kwargs['obj']
        H    = kwargs['H'] 
        W    = kwargs['W']
        disp = kwargs['disp']

        pos = obj.pos
        vel = self.vel
    
        if (pos[0] <= 0) :
            pos[0]  = 1
            vel[0] *= -1
            vel[1]  = random.choice([-1,1])
            
        if ((pos[0] + obj.radius) >= W) :
            pos[0]  = (W - obj.radius - 1)
            vel[0] *= -1
            vel[1]  = random.choice([-1,1])

        if (pos[1] <= 0) :
            pos[1]  = 1
            vel[1] *= -1
            vel[0]  = random.choice([-1,1])
        
        if ((pos[1] + obj.radius) >= H):
            pos[1]  = (H - obj.radius - 1)
            vel[1] *= -1
            vel[0]  = random.choice([-1,1])
        
        pos[0]  = pos[0] + vel[0]*disp
        pos[1]  = pos[1] + vel[1]*disp

        self.vel = vel
        
        return pos
