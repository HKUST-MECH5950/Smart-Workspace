import tkinter as tk

class temp_interact:
    def __init__(self, master_class, name, t, init_state):
        self.master_class = master_class
        self.name = name
        self.state = init_state
        self.t = t
    
    def get_state(self):
        return self.state
    
    def change(self, event):
        if self.t == 'act':
            self.master_class.send_update_act_message()
        elif self.t== 'con':
            self.master_class.send_update_con_message()
    
    def change_state(self, target):
        if isinstance(self.state, type(target)):
            self.state = target
        else:
            raise TypeError(f"target state and state's type do not match {type(target)} and {type(self.state)}")

class toggle_button(temp_interact):
    def __init__(self, master_class, name, t, init_state=False, row=0, s_col=0):
        super().__init__(master_class, name, t, init_state)
        # self.master_class = master_class
        self.name = name
        self.state = init_state
        self.label = tk.Label(master_class.interact_fram, text=name + ': ', anchor="w")
        self.label.grid(row=row, column=s_col)
        self.button = tk.Button(master_class.interact_fram, text="ON" if init_state else "OFF", command=self.toggle, fg="green" if init_state else "red")
        self.button.grid(row=row, column=s_col+1)
        
        self.state = not self.state
        # self.toggle()
        
    def toggle(self):
        self.state = not self.state
        if self.state:
            self.button.config(text = "ON", fg = "green")
        else:
            self.button.config(text = "OFF", fg = "red")
        # self.master_class.send_update_message()
        self.change(None)
    
    def get_state(self):
        return int(self.state)
    
    def destroy(self):
        self.button.destroy()
        self.label.destroy()
    
class no_interact(temp_interact):
    def __init__(self, master_class, name, t, init_state):
        super().__init__(master_class, name, t, init_state)

class slider(temp_interact):
    def __init__(self, master_class, name, t, init_state=0, row=0, s_col=0, min_v=0, max_v=255):
        super().__init__(master_class, name, t, init_state)
        self.master_class = master_class
        self.name = name
        
        self.label = tk.Label(master_class.interact_fram, text=name+": ", anchor="w")
        self.label.grid(row=row, column=s_col)
        
        self.var = tk.StringVar()
        self.slider = tk.Scale(master_class.interact_fram, from_=min_v, to=max_v, orient=tk.HORIZONTAL, variable=self.var)
        self.slider.bind("<ButtonRelease-1>", self.change)
        self.slider.grid(row=row, column=s_col+1)
        self.slider.set(init_state)
            
    
    def get_state(self):
        return int(self.var.get())
    
    def destroy(self):
        self.slider.destroy()
        self.label.destroy()