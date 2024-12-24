import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from timer import timer
import numpy as np
from sim_op import *

HOT_TEMP = 27
COLD_TEMP = 25

NORMAL_MODE = 0    #hard-code
MANUAL_MODE = 1     #manual control + logging user behavior
AI_MODE = 2         #AI control

MODE = {
    NORMAL_MODE:'Normal',
    MANUAL_MODE:'Manual',
    AI_MODE:'AI',
}

class DummyArduino:
    def __init__(self, interface):
        self.running = False
        self.in_queue = []
        self.out_queue = []
        self.custom_response = "Echo: {}"  # Default response format
        self.interface = interface
        self.mode = 0
        self.in_waiting = 0
        
        self.acts = {'lamp': [0, 'sl'],
                     'RGB': [[0,0,0], 'none'],
                     'LED': [0, 'tb'],
                     'FAN': [0, 'tb']}


        self.sensors = {'Temp': [25., 'f', 0, 50],
                        'Photo': [0., 'a', 0, 255],
                        'IR': [0., 'd', 0, 1],
                        'Sit': [0., 'd', 0, 1],
                        }
        
        self.controls = {'Temp': [25, 'f', 0, 50],
                         'Light_level': [200, 'f', 0, 255],
                         }
        
        
        self.c_op = None
        self.e_sim = None
        
        
    def random_sensor_reading(self):
        for k, (_, m, mi, ma) in self.sensors.items():
            v = np.random.randint(mi,ma+1)
            self.sensors[k][0] = v
                
    def start_env_sim(self):
        if self.e_sim is not None:
            self.e_sim.running = False
        self.e_sim = env_sim(self)
        self.e_sim.running = True
        threading.Thread(target=self.e_sim.loop, daemon=True).start()
    
    def send_init_message(self):
        out = 'IA|'
        for n, info in self.acts.items():
            if info[1] != 'none':
                out += f"{n}:{info[0]};{info[1]},"
        out = out[:-1]
        out += '||IC|'
        for n, info in self.controls.items():
            if info[1] != 'none':
                out += f"{n}:{';'.join([str(i) for i in info])},"
        out = out[:-1]
        self.interface.log('Sending: ' + out)
        self.out_queue.append(out)
        self.in_waiting = len(self.out_queue)
            
    
        
        
    def start(self):
        self.running = True
        threading.Thread(target=self.run, daemon=True).start()
        self.send_init_message()
        self.change_mode(self.mode)
        self.start_env_sim()

    def stop(self):
        self.running = False
        if self.c_op is not None:
            self.c_op.running = False
        if self.e_sim is not None:
            self.e_sim.running = False

    def run(self):
        while self.running:
            # print('hi)')
            # self.in_waiting = len(self.out_queue)
            self.process()
            self.interface.update_sliders()
            time.sleep(1)  # Simulate processing delay
        
    def readline(self):
        out = self.out_queue.pop(0)
        self.in_waiting = len(self.out_queue)
        return out
        
    def write(self, message):
        self.in_queue.append(message)
    
    def send_current_data(self):
        out = ''
        for n, (va, ty, mi, ma) in self.sensors.items():
            out += f"{n}:{float(va-mi)/float(ma-mi):.3f},"
        out = out[:-1]
        return out
    
    def change_mode(self, new_mode):
        self.mode = new_mode
        if self.c_op is not None:
            self.c_op.running = False
        self.interface.log(f"Change mode to {MODE[new_mode]}")
        if new_mode == 0:
            self.c_op = normal_op(self)
        elif new_mode == 1:
            pass
        elif new_mode == 2:
            pass
        
        if self.c_op is not None:
            self.c_op.running = True
            threading.Thread(target=self.c_op.loop, daemon=True).start()
            
    def acts_data(self):
        out = ''
        for n, info in self.acts.items():
            # print(info)
            (c_v, interact) = info
            if interact != 'none':
                out += f'{n}:{c_v if interact != 'sl' else c_v/255.},'
        out = out[:-1]
        return out
    
    def process(self):
        
        if len(self.in_queue) > 0:
            messagess = self.in_queue.pop(0)
            # print(messagess)
            for messages in messagess.split('\n'):
                if messages == 'Send data':
                    out = 'ED|'+self.send_current_data()
                    self.interface.log('Collecting data.')
                    out += '||AD|'+self.acts_data()
                    # self.random_sensor_reading()
                    self.interface.log('Sending data.')
                    self.out_queue.append(out)
                    self.in_waiting = len(self.out_queue)
                elif 'CM|' in messages:
                    # Do change mode sequence
                    new_mode = int(messages[3:])
                    self.change_mode(new_mode)
                    
                elif 'CA|' in messages:
                    self.interface.log('Changing actor')
                    
                elif 'CT|' in messages:
                    self.interface.log('Changing target')
                    for m in messages[3:].split(','):
                        name, value = m.split(':')
                        self.controls[name][0] = int(value)
                    self.interface.log('Done changing target')
                    
                    
                elif messages != "":
                    new_message = "RP|" + messages
                    self.interface.log(new_message)
                    print((f"Dummy Arduino sending: {messages}"))
                    self.out_queue.append(new_message)
                    self.in_waiting = len(self.out_queue)
            
    # def in_waiting(self):
    #     return len(self.out_queue)
        
        
class DummyInterface:
    def __init__(self):
        
        self.do_update_sliders = True
        self.dummy_arduino = DummyArduino(self)
        
        self.window = tk.Toplevel()
        self.window.title("Dummy Arduino Interface")


        self.sc = {}
        self.sc_fram = ttk.Frame(self.window)
        self.sc_fram.pack()
        i = 0
        for s_n, (s_v, s_t, s_mi, s_mx) in self.dummy_arduino.sensors.items():
            self.sc[s_n] = {}
            self.sc[s_n]['label'] = tk.Label(self.sc_fram, text=s_n+': ')
            self.sc[s_n]['label'].grid(row=i, column=0, sticky="w")
            self.sc[s_n]['var'] = tk.StringVar(value=s_v)
            self.sc[s_n]['sl'] = tk.Scale(self.sc_fram, from_=s_mi, to=s_mx, orient=tk.HORIZONTAL, variable=self.sc[s_n]['var'])
            self.sc[s_n]['sl'].grid(row=i, column=1, sticky="w")
            self.sc[s_n]['sl'].bind("<ButtonRelease-1>", self.update_sensor)
            self.sc[s_n]['sl'].bind("<ButtonPress-1>", self.disable_sliders_update)
            
            i += 1
    
        # Console for dummy serial log
        self.console = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, width=50, height=10)
        self.console.pack()

        # Start Dummy Arduino
        self.dummy_arduino.start()

        # Close button
        self.close_button = tk.Button(self.window, text="Close", command=self.close)
        self.close_button.pack()

        self.window.protocol("WM_DELETE_WINDOW", self.close)
        

    def disable_sliders_update(self, event):
        self.do_update_sliders = False
        
    def update_sliders(self):
        if self.do_update_sliders:
            for s_n in self.sc.keys():
                self.sc[s_n]['sl'].set(self.dummy_arduino.sensors[s_n][0])

    def log(self, message):
        self.console.insert(tk.END, message + '\n')
        self.console.yview(tk.END) 
    
    def close(self):
        self.dummy_arduino.stop()
        self.window.destroy()
        
    def update_sensor(self, event):
        for s_n, d in self.sc.items():
            self.dummy_arduino.sensors[s_n][0] = int(float(d['var'].get()))
        
        self.do_update_sliders = True