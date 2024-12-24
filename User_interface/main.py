import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
from dummy import DummyInterface, DummyArduino
import threading
import time
from datetime import datetime
from moduls import *
from timer import timer
import json

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)
import numpy as np

DATA_COLLECT_INTERVAL = 1 #s

NORMAL_MODE = 0    #hard-code
MANUAL_MODE = 1     #manual control + logging user behavior
AI_MODE = 2         #AI control

MODE = {
    NORMAL_MODE:'Normal',
    MANUAL_MODE:'Manual',
    AI_MODE:'AI',
}
  
class ArduinoInterface:
    def __init__(self, master):
        self.master = master
        master.title("Arduino Serial Interface")

        # Dropdown to select COM ports
        self.com_label = tk.Label(master, text="Select COM Port:", anchor="w")
        self.com_label.grid(row=0, column=0,sticky="w")

        self.com_ports = self.get_com_ports()
        self.com_var = tk.StringVar(value=self.com_ports[0] if self.com_ports else "")
        self.com_menu = ttk.Combobox(master, textvariable=self.com_var, values=self.com_ports)
        self.com_menu.grid(row=0, column=1,sticky="w")

        # Baud rate dropdown
        self.baud_label = tk.Label(master, text="Select Baud Rate:", anchor="w")
        self.baud_label.grid(row=1, column=0,sticky="w")
        

        self.baud_rates = [300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200]
        self.baud_var = tk.StringVar(value="9600")  # Default baud rate
        self.baud_menu = ttk.Combobox(master, textvariable=self.baud_var, values=self.baud_rates)
        self.baud_menu.grid(row=1, column=1,sticky="w")

        
        self.interval_label = tk.Label(master, text="Select check interval:", anchor="w")
        self.interval_label.grid(row=2, column=0,sticky="w")
        self.interval_var = tk.StringVar(value=DATA_COLLECT_INTERVAL)
        self.interval_slider = tk.Scale(master, from_=1, to=60, orient=tk.HORIZONTAL, variable=self.interval_var)
        # self.interval_slider.bind("<ButtonRelease-1>", self.change)
        self.interval_slider.grid(row=2, column=1,sticky="w")
        
        
        # Connect button
        self.connect_button = tk.Button(master, text="Connect", command=self.connect, width=10)
        self.connect_button.grid(row=0, column=2, sticky="e")

        # Restart button
        self.restart_button = tk.Button(master, text="Restart Serial", command=self.restart_serial, width=10)
        self.restart_button.grid(row=1, column=2, sticky="e")
        
        self.stop_button = tk.Button(master, text="Stop", command=self.stop_connection, width=10)
        self.stop_button.grid(row=2, column=2, sticky="e")

        # change to different mode
        self.change_mode_label = tk.Label(master, text="Select mode:", anchor="w")
        self.change_mode_label.grid(row=3, column=0, sticky="w")
        self.change_mode_fram = ttk.Frame(master,)
        self.change_mode_fram.grid(row=3, column=1, columnspan=2, sticky="ew")
        # self.cm_var = tk.StringVar(value=0)
        # self.cmb_o1 = ttk.Radiobutton(self.change_mode_fram, text='Normal', variable=self.cm_var, value=0, command=self.change_mode)
        # self.cmb_o1.grid(row=0, column=0, sticky="w")
        # self.cmb_o2 = ttk.Radiobutton(self.change_mode_fram, text='Manual', variable=self.cm_var, value=1, command=self.change_mode)
        # self.cmb_o2.grid(row=0, column=1, sticky="ew")
        # self.cmb_o3 = ttk.Radiobutton(self.change_mode_fram, text='AI', variable=self.cm_var, value=2, command=self.change_mode)
        # self.cmb_o3.grid(row=0, column=2, sticky="e")
        
        # Console for serial log
        self.console = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=90, height=10)
        self.console.grid(row=4, column=0, columnspan=3, sticky="we")

        # # Send test message button
        self.interact_fram = ttk.Frame(master,)
        self.interact_fram.grid(row=5, column=0, columnspan=3, sticky="NSEW")
        
        self.plot_fram = ttk.Frame(master,)
        self.plot_fram.grid(row=6, column=0, columnspan=3, sticky="NSEW")
        self.fig = Figure()
        self.plot_canvas = FigureCanvasTkAgg(self.fig, master=self.plot_fram)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().pack()
        
        self.toolbar = NavigationToolbar2Tk(self.plot_canvas, self.plot_fram)
        self.toolbar.update()
        self.plot_canvas.get_tk_widget().pack()

        self.serial_connection = None
        self.running = False
        self.acts = {}
        self.req_data_timer = timer(self.interval_var)
        
        self.cons = {}
        
        self.s_memory = {}
        self.a_memory = {}
    
    def check_dummy(self):
        return (self.com_var.get() == 'dummy')
    
    def change_mode(self):
        self.log(f'Changing mode to {MODE[int(self.cm_var.get())]} Mode.')
        if self.serial_connection is not None:
            out = f'CM|{self.cm_var.get()}\n'
            if not self.check_dummy():
                out = str.encode(out)
            self.serial_connection.write(out)
    
    def stop(self):
        self.running = False
        
    def stop_connection(self):
        self.stop()
        if isinstance(self.serial_connection, DummyArduino):
            self.serial_connection.interface.close()
            del self.serial_connection
            self.serial_connection = None
        for act in self.acts.values():
            try:
                act.destroy()
            except:
                pass
    

    def get_com_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()] + ["dummy"]
        return ports

    def init_control_fram(self, init_string):
        for d in init_string.split('||'):
            if d[:2] == 'IA':
                i = 0
                d = d[3:]
                for s_i in d.split(','):
                    print(s_i)
                    data, interact = s_i.split(';')
                    act, state = data.split(':')
                    if interact == 'none':
                        continue
                    if interact == 'tb':
                        self.acts[act] = toggle_button(self, act, 'act', bool(state), row=i)
                    elif interact == 'sl':
                        self.acts[act] = slider(self, act, 'act', int(state), row=i)
                    i += 1
            elif d[:2] == 'IC':
                i = 0
                d = d[3:]
                for s_i in d.split(','):
                    print(s_i)
                    c_n, data = s_i.split(':')
                    c_v, c_t, c_min, c_max = data.split(';')
                    if interact == 'none':
                        continue
                    if c_t == 'f':
                        self.cons[c_n] = slider(self, c_n, 'con', c_v, row=i, s_col=2, min_v=c_min, max_v=c_max)
                    i += 1
    
    def connect(self):
        com_port = self.com_var.get()
        baud_rate = self.baud_var.get()
        if com_port == "dummy":
            self.log(f"Connected to {com_port} at {baud_rate} baud (simulated).")
            self.serial_connection = DummyInterface().dummy_arduino
        else:
            self.serial_connection = serial.Serial(com_port, baudrate=int(baud_rate))
        self.running = True
        while not self.serial_connection.in_waiting:
            pass
        
        init_string = self.serial_connection.readline()
        if not isinstance(init_string, str):
            init_string = init_string.decode(encoding="utf-8")
        # print(init_string)
        self.init_control_fram(init_string=init_string)
        threading.Thread(target=self.check_for_message).start()
        threading.Thread(target=self.request_data).start()
        

    def restart_serial(self):
        self.log("Restarting serial connection (simulated).")
        self.stop_connection()
        self.connect()

    # def encode(self):
    #     out = 'CA|'
    #     for n, act in self.acts.items():
    #         out += f"{n}:{act.get_state()},"
    #     out = out[:-1]
    #     out += '\nCT|'
    #     for n, con in self.cons.items():
    #         out += f"{n}:{con.get_state()},"
    #     out = out[:-1]
    #     return out
        
    def send_update_act_message(self):
        out = 'CA|'
        for n, act in self.acts.items():
            out += f"{n}:{act.get_state()},"
        out = out[:-1]
        if not self.check_dummy():
            out = str.encode(out)
        self.serial_connection.write(out)
    
    def send_update_con_message(self):
        out = 'CT|'
        for n, con in self.cons.items():
            out += f"{n}:{con.get_state()},"
        out = out[:-1]
        if not self.check_dummy():
            out = str.encode(out) + b'\n'
        # print(out)
        self.serial_connection.write(out)
        
    def log(self, message):
        self.console.insert(tk.END, message + '\n')
        self.console.yview(tk.END)  # Auto scroll to the end

    def on_closing(self):
        self.stop()
        self.master.destroy()
    
    def ED_to_readable(self, ED_data, need_time=True, need_log=True):
        c_time = datetime.today()
        E_data, A_data = ED_data.split('||')
        if need_log:
            if 'time' not in self.s_memory:
                self.s_memory['time'] = []
            self.s_memory['time'].append(c_time)
            for d in E_data[3:].split(','):
                n, v = d.split(':')
                v = float(v)
                if n not in self.s_memory:
                    self.s_memory[n] = []
                self.s_memory[n].append(v)
            for d in A_data[3:].split(','):
                n, v = d.split(':')
                v = float(v)
                if n not in self.a_memory:
                    self.a_memory[n] = []
                self.a_memory[n].append(v)
                
            if len(self.s_memory['time'])>200:
                save_log = {'time':[i.strftime('%Y%m%d%H%M%S') for i in self.s_memory['time'][:100]]}
                save_log['sensors'] = {k:v[:100] for k, v in self.s_memory.items() if k != 'time'}
                save_log['acts'] = {k:v[:100] for k, v in self.a_memory.items()}
                
                log_name = save_log['time'][0] + 'to' + save_log['time'][0]
                with open(f'./log/{log_name}.json', 'w') as f:
                    json.dump(save_log, f, indent=1)
                
                for k in self.s_memory.keys():
                    self.s_memory[k] = self.s_memory[k][100:]
                for k in self.a_memory.keys():
                    self.a_memory[k] = self.a_memory[k][100:]
                    
                
        if need_time:
            read = '[' + c_time.strftime('%Y-%m-%d %H:%M:%S') + ']\nED{' + E_data[3:] + '}\nAD{' + A_data[3:] +'}'
        else:
            read = E_data[3:] + '\n' + A_data
            
        return read
    
    def plot_data(self):
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        s = 20
        too_long = (len(self.s_memory['time'])>s)
        for k in self.s_memory.keys():
            if k == 'time':
                continue
            v = self.s_memory[k]
            if too_long:
                ax.plot(self.s_memory['time'][-s:], v[-s:], label=k)
            else:
                ax.plot(self.s_memory['time'], v, label=k)
            
        for k in self.a_memory.keys():
            v = self.a_memory[k]
            ax.plot(self.s_memory['time'][-s:], v[-s:], label=k, linestyle = '--')
            
            
        ax.set_ylim(-0.1, 1.1)
        ax.legend(loc='upper right')
        self.plot_canvas.draw()
        self.toolbar.update()
        
    def check_for_message(self):
        while self.running:
            if self.serial_connection.in_waiting:
                read = self.serial_connection.readline()
                if not self.check_dummy():
                    read = read.decode(encoding="utf-8")
                    read = read.replace('\n', '')
                if read[:2] == 'ED':
                    logging = self.ED_to_readable(read)
                    self.plot_data()
                else:
                    logging = read
                self.log(logging)
                
            if isinstance(self.serial_connection, DummyArduino):
                time.sleep(0.5)  # Simulate processing delay

    def request_data(self):
        while self.running:
            now = time.time()
            if not self.serial_connection.in_waiting:
                if self.req_data_timer.check(now):
                    if self.check_dummy():
                        self.serial_connection.write('Send data\n')
                    else:
                        self.serial_connection.write(b'Send data\n')
                        
            time.sleep(0.1)

    def __del__(self):
        self.stop_connection()
        
        
if __name__ == "__main__":
    root = tk.Tk()
    app = ArduinoInterface(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.title("MECH5950 Final Project: Smart Workspace")
    root.mainloop()