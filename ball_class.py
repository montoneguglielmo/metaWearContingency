import random
import numpy as np
import pygame
from trajectory_class import * 

trajNameToTrajClass = {'circle':circle_traj, 'straight':strait_traj}

class moving_obj(object):

    def __init__(self, **kwargs):


        trajectory    = kwargs['trajectory']    
        self.obj_traj = trajNameToTrajClass[trajectory['name']](**trajectory)
        self.pos      = self.obj_traj.pos
        self.pos_hist = []

    def change_shape(self,**kwargs):
        pass

    def next_pos(self, disp, H, W):
        self.pos  = self.obj_traj.next_pos(obj=self, disp=disp, H=H, W=W)
        self.change_shape(disp=disp, H=H, W=W)

    def draw(self, screen, **kwargs):
        pass

    def save_pos(self):
        pos = [str(self.pos[0]), str(self.pos[1])]
        self.pos_hist.append(pos)
        
class moving_img(moving_obj):

    def __init__(self, **kwargs):

        super(moving_img, self).__init__(**kwargs)
        self.load_image = pygame.image.load(kwargs['load_img']).convert_alpha()
        self.radius = int(np.mean(self.load_image.get_size()))
        
    def draw(self, screen, **kwargs):
        super(moving_img, self).draw(screen, **kwargs)
        pos = np.asarray(self.pos, dtype=int)
        screen.blit(self.load_image, pos)

        
class geom_shape(moving_obj):

    def __init__(self, **kwargs):

        if 'color' in kwargs:
            self.color = kwargs['color']
        else:
            self.color = (255,0,0)

        super(geom_shape, self).__init__(**kwargs)

        

class ball_class(geom_shape):

    def __init__(self, **kwargs):

        super(ball_class, self).__init__(**kwargs)
    
        if 'radius' in kwargs:
            self.radius = kwargs['radius']
        else:
            self.radius = 20

    def draw(self, screen, **kwargs):
        super(ball_class, self).draw(screen, **kwargs)
        pos    = np.asarray(self.pos, dtype=int)
        radius = int(self.radius) 
        pygame.draw.circle(screen, self.color, pos, radius, 0)
        

class ball_change_ray(ball_class):

    def __init__(self,**kwargs):

        super(ball_change_ray, self).__init__(**kwargs)
        self.max_radius = kwargs['max_radius']
        self.min_radius = kwargs['min_radius']
        self.growing    = True 
        
    def change_shape(self,**kwargs):
        super(ball_change_ray, self).change_shape(**kwargs)
        disp = kwargs['disp']
        
        if self.radius >= self.max_radius or self.radius <= self.min_radius:
            self.growing = not self.growing

        if disp > 0:    
            if self.growing:
                self.radius += 0.1 * disp
            else:
                self.radius -= 0.1 * disp

        
if __name__ == "__main__":

    balls = {
              'ball1':
              {
                 'color': (255,255,0),
                 'start_pos': (0,0),
                 'radius':10
              },
              'ball2':
              {
                'color': (255,255,255),
                'start_pos': (0,10),
                'radius':10
              }
            }

    bl_class = []
    for bl in balls.keys():
        print balls[bl]
        bl_class.append(ball_class(**balls[bl]))


    print bl_class[0].color
