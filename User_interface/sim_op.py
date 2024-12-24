import time
# from timer import timer
import random

MAX_SIT_TIME= 5
MAX_STAND_TIME = 1

TIMEOUT_TIME = 3

class pid_control:
    def __init__(self, out, read, target):
        self.kp = 0.005
        self.ki = 0.005
        self.kd = 0.0001
        self.out = out
        self.read = read
        self.last_time=None
        self.last_err = 0.
        self.errSum = 0.
        self.target = 0.
        
    
    def update(self, now):
        if self.last_time is None:
            self.last_time = now
        dt = now - self.last_time    
        if dt == 0.:
            return
        else:
            err = self.target[0]-self.read[0]
        self.errSum += (err * dt);
        # print(self.errSum)
        derr = (err-self.last_err)/dt
        # print(f'{err = }')
        # print(f'{ self.errSum = }')
        # print(f'{derr = }')
        c_out = self.kp * err + self.ki * self.errSum + self.kd * derr
        # print(c_out)
        
        c_out = min(255, max(0, c_out))
        
        self.out[0] = int(c_out)
        
        self.last_err = err
        self.last_timet = now
        

        
        

class normal_op:
    def __init__(self, ard):
        self.fan_on_temp = 27
        self.fan_off_temp = 23
        
        self.sit_time = None
        self.stand_time = None

        self.not_move_time = None
        self.have_ppl = False
        
        
        self.ard = ard
        self.running = False
        
        self.photo_pid = pid_control(self.ard.acts['lamp'], self.ard.sensors['Photo'], self.ard.controls['Light_level'])
        
        
    def temp_part(self):
        temp = self.ard.sensors['Temp'][0]
        if temp >= self.fan_on_temp:
            self.ard.acts['FAN'][0] = 1
        elif temp <= self.fan_off_temp:
            self.ard.acts['FAN'][0] = 0
            
    def sit_part(self, now):
        is_sit = self.ard.sensors['Sit'][0]

        if is_sit:
            self.stand_time = None
            if self.sit_time is None:
                self.sit_time = now
            if (now-self.sit_time) > MAX_SIT_TIME:
                # print(now-self.sit_time)
                self.ard.acts['LED'][0] = 1
        else:
            if self.stand_time is None:
                self.stand_time = now
            if (now - self.stand_time) > MAX_STAND_TIME:
                self.ard.acts['LED'][0] = 0
                self.sit_time = None
                
    def lamp_part(self, now):
        is_detect = self.ard.sensors['IR'][0]
        # light_level = self.ard.sensors['Photo'][0]
        if is_detect:
            self.have_ppl = True
            self.not_move_time = None
        else:
            if self.not_move_time is None:
                self.not_move_time = now
            if self.have_ppl:
                if (now - self.not_move_time) > TIMEOUT_TIME:
                    self.have_ppl = False
        
        if self.have_ppl:
            # target = self.ard.controls['Light_level'][0]
            # c_act = self.ard.acts['lamp'][0]
            # c_act += 1 if (light_level<target) else -1
            # c_act = min(255, max(0, c_act))
            # self.ard.acts['lamp'][0] = c_act
            self.photo_pid.target = self.ard.controls['Light_level']
            self.photo_pid.update(now)

        else:
            self.photo_pid.target = [0.]
            self.ard.acts['lamp'][0] = 0
        
        
        

            
            
    def loop(self):
        while self.running:
            now = time.time()
            self.temp_part()
            self.sit_part(now)
            self.lamp_part(now)
            # print(temp)
            time.sleep(0.1)
            

class env_sim:
    def __init__(self, ard):
        self.ard = ard
        self.running = False
        
        self.room_temp = 25
        self.light_level = 10
        
    def lamp2photo(self):
        lamp_level = self.ard.acts['lamp'][0]
        photo_read = (lamp_level*1.2)+random.randint(-1,1)
        photo_read = max(0,min(photo_read,255))
        # print(photo_read)
        self.ard.sensors['Photo'][0] = photo_read
        
        
    def loop(self):
        while self.running:
            self.lamp2photo()
            time.sleep(0.1)
        
