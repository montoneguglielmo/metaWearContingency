import time
import pygame
import numpy as np


class att_gather(object):

    def __init__(self, **kwargs):

        self.duration      = kwargs['duration']
        self.period        = kwargs['period']
        self.screen_size   = np.asarray(kwargs['screen_size'])
        self.n_repetition  = kwargs['n_repetition']
        self.name_audio    = kwargs['list_audio']
        self.volume        = kwargs['volume']
        self.pos           = np.asarray(self.screen_size/2.0, dtype=int)
        self.playing       = False
        self.last_played   = time.time() - self.period
        self.start_radius  = np.min(self.screen_size)/2.0
        self.radius        = self.start_radius
        self.color         = (255, 255, 255)
        self.repetition    = 1
        
        n_step             = self.duration*1000.0 / 20.0
        self.len_step      = np.min(self.screen_size)/(2.0*n_step) 

        self.audio_cnt     = 0
        self.audio         = []
        for aud in self.name_audio:
            self.audio.append(pygame.mixer.Sound(aud))

        for aud in self.audio:
            aud.set_volume(self.volume)
        
    def attention_check(self, curr_time):
        
        if (curr_time - self.last_played) > self.period:
            self.audio[self.audio_cnt].play()
            self.audio_cnt += 1
            if self.audio_cnt == len(self.audio):
                self.audio_cnt = 0
                
            self.radius      = self.start_radius
            self.playing     = True
            self.last_played = curr_time 
            self.repetition  = 1
        return self.playing
        

    def draw(self, screen, **kwargs):
        self.radius -= self.len_step
        radius = int(self.radius)
        pygame.draw.circle(screen, self.color, self.pos, radius, 0)
        if radius <= 0:
            if self.repetition==self.n_repetition:
                self.playing = False
                self.audio[self.audio_cnt-1].fadeout(10)
            else:
                self.radius = self.start_radius
                self.repetition += 1
        
