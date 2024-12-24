import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from datetime import datetime, timedelta
from scipy.ndimage import gaussian_filter
import numpy as np
import argparse



class AI_model(nn.Module):
    def __init__(self, in_ch, out_ch, deep=10, fram=10):
        super().__init__()
        temp = []
        step = torch.linspace(in_ch, out_ch, steps=deep)
        for i in range(deep-1):
            in_C = int(step[i])
            out_c = int(step[i+1])
            temp.append(nn.Linear(in_C, out_c))
            temp.append(nn.ReLU())
        temp = temp[:-1]
        self.model = nn.Sequential(*temp)
        # print(self.model)

    def forward(self, x):
        y = self.model(x)
        return y


class sim_d_set(Dataset):
    def __init__(self, fram=10, step=timedelta(seconds=10), num_date=1):
        self.fram = fram
        self.t = np.arange(datetime(2024,12 ,12), datetime(2024,12,12+num_date), step).astype(datetime)            
        # Sensors
        num_data = len(self.t)
        self.temp_read = ((-np.cos(np.linspace(0, 2*np.pi, num_data))*0.5+0.5)*4 + 24.)/50.  # Tempeture
        # print(self.temp_read[len(self.t)//2])
        self.humi_read = np.repeat(0.5, num_data)
        self.sit_read = np.repeat(0., num_data)
        self.ir_read = np.repeat(0., num_data)
        self.photo_read = np.repeat(0., num_data)
        for i, time in enumerate(self.t):
            hour = time.hour
            if (6<=hour<19):
                self.photo_read[i] = 0.6
        self.photo_read = gaussian_filter(self.photo_read,sigma= 100)
        
        working_hour = (9, 18)
        is_wh = lambda h: (working_hour[0]<=h<12) or (14<=h<working_hour[1])
        for i, time in enumerate(self.t):
            hour = time.hour
            mins = time.minute
            h_m = hour * 60 + mins
            if is_wh(hour):
                self.ir_read[i] = 1.
                self.photo_read[i] = 0.9

            if ((working_hour[0]*60+30)<=h_m<=(11*60+30)) or ((14*60+30)<=h_m<=((working_hour[1]-1)*60+30)):
                self.sit_read[i] = 1.
                
        # Target
        self.temp_target = np.repeat(0., num_data)
        self.temp_target_on = np.repeat(0., num_data)
        self.light_target = np.repeat(0., num_data)
        for i, time in enumerate(self.t):
            hour = time.hour
            mins = time.minute
            h_m = hour * 60 + mins
            if is_wh(hour):
                self.temp_target[i] = 23./50.
                self.temp_read[i] = 23./50.
                self.light_target[i] = 0.9
                self.temp_target_on[i] = 1.
            if (((working_hour[0])*60+45)<=h_m<=((working_hour[1])*60)):
                self.temp_target[i] = 25./50.
                self.temp_read[i] = 25./50.
                self.temp_target_on[i] = 1.

        self.temp_read = gaussian_filter(self.temp_read,sigma=10)
                
        
                
        # import matplotlib.pyplot as plt
        # plt.plot(self.t, self.temp_read, label='temp', linestyle='-',   linewidth=2, alpha=0.9)
        # plt.plot(self.t, self.humi_read, label='humi', linestyle='-',   linewidth=2, alpha=0.9)
        # plt.plot(self.t, self.sit_read, label='sit', linestyle='-',     linewidth=2, alpha=0.9)
        # plt.plot(self.t, self.ir_read, label='IR', linestyle='-',       linewidth=2, alpha=0.9)
        # plt.plot(self.t, self.photo_read, label='Photo', linestyle='-', linewidth=2, alpha=0.9)
        
        # plt.plot(self.t, self.temp_target,      label='target_temp',    linestyle='dotted',  linewidth=4)
        # plt.plot(self.t, self.temp_target_on,   label='target_temp_on', linestyle='dotted',  linewidth=4)
        # plt.plot(self.t, self.light_target,     label='target_light',   linestyle='dotted',  linewidth=4)
        
        # plt.xticks(rotation = 90
        #                     )
        # plt.ylim((0., 1.2))
        # plt.legend()
        
        # plt.show()
        # exit()
                
            
    def __len__(self):
        nb = len(self.t) - self.fram
        return nb
        
    
    def __getitem__(self, ind):
        start_ind = ind
        end_ind = start_ind + self.fram
        out_time = self.t[start_ind:end_ind]
        time = torch.tensor([[i.hour/24., i.minute/60., i.second/60.] for i in out_time])
        tr = torch.from_numpy(self.temp_read[start_ind:end_ind]).view(-1,1)
        hr = torch.from_numpy(self.humi_read[start_ind:end_ind]).view(-1,1)
        sr = torch.from_numpy(self.sit_read[start_ind:end_ind]).view(-1,1)
        irr = torch.from_numpy(self.ir_read[start_ind:end_ind]).view(-1,1)
        pr = torch.from_numpy(self.photo_read[start_ind:end_ind]).view(-1,1)
        
        x = torch.cat([time, tr, hr,sr,irr, pr], dim=-1).to(torch.float)
        x[:,3:] += (torch.rand_like(x[:,3:])*0.0001)
        x = x.flatten().to(torch.float)
        
 
        y = torch.tensor([self.temp_target[end_ind], self.temp_target_on[end_ind], self.light_target[end_ind]]).to(torch.float)
        y_1 = torch.tensor([self.temp_target[end_ind-1], self.temp_target_on[end_ind-1], self.light_target[end_ind-1]]).to(torch.float)
        
        return x, y, y_1

    def get_output_shape(self):
        return self[0][1].shape

    def get_input_shape(self):
        return self[0][0].shape
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser("AI module")
    parser.add_argument("--mode", type=str, default="train", choices=["train", "test"])
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--batch", type=int, default=100)
    parser.add_argument("--n_epoches", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.0002)
    args = parser.parse_args()
    
    data = sim_d_set(fram=100, step=timedelta(seconds=30))
    in_shape = data.get_input_shape()
    out_shape = data.get_output_shape()
    model = AI_model(in_shape[0], out_shape[0])
    train = args.mode == "train"
    device = args.device
    model.to(device)
    batch = args.batch
    if train:
        loader = DataLoader(data, batch, shuffle=True, drop_last=True)
        
        epoches = args.n_epoches
        lr = args.lr
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = nn.MSELoss()
        for ep in range(epoches):
            model.train()
            total_loss = 0
            for x, y, y_1 in loader:
                x = x.to(device)
                y = y.to(device)
                # y_1 = y_1.to(device)
                # xy_last = torch.cat([x,y_1], dim=-1)
                
                pre = model(x)
                loss = loss_fn(pre, y)

                total_loss += loss.item()
                opt.zero_grad()
                loss.backward()
                opt.step()
                
            print(f"EP: {ep:>4d}, Loss: {total_loss/len(loader):.3e}")
            
        torch.save(model.state_dict(), './weight/weight.pt')
    else:
        loader = DataLoader(data, batch, shuffle=False, drop_last=False)
        
        model.load_state_dict(torch.load('./weight/weight.pt'))
        model.eval()
        y = []
        # y_last = torch.zeros((1,3)).to(device)
        for x, *_ in loader:
            x = x.to(device)
            # xy_last = torch.cat([x,y_last], dim=-1)
            pre_y = model(x).detach()
            # y_last = pre_y           
            y.append(pre_y.cpu())
            
        y = torch.cat(y, dim=0)
        
        import matplotlib.pyplot as plt
        # plt.plot(data.t, data.temp_read, label='temp')
        # plt.plot(data.t, data.humi_read, label='humi')
        # plt.plot(data.t, data.sit_read, label='sit')
        # plt.plot(data.t, data.ir_read, label='IR')
        # plt.plot(data.t, data.photo_read, label='Photo')
        
        plt.plot(data.t, data.temp_target, label='target_temp', linestyle='-', linewidth=8, alpha=0.4)
        plt.plot(data.t, data.temp_target_on, label='target_temp_on', linestyle='-', linewidth=8, alpha=0.4)
        plt.plot(data.t, data.light_target, label='target_light', linestyle='-', linewidth=8, alpha=0.4)
        
        plt.plot(data.t[data.fram:], y[:,0], label='prediction_temp', linestyle='-', linewidth=2)
        plt.plot(data.t[data.fram:], y[:,1], label='prediction_temp_on', linestyle='-', linewidth=2)
        plt.plot(data.t[data.fram:], y[:,2], label='prediction_light', linestyle='-', linewidth=2)
        # plt.plot(data.t[data.fram:], data.light_target, label='t_temp', linestyle=':', linewidth=5)

        plt.xticks(rotation = 90
                            )
        plt.ylim((0., 1.2))
        plt.legend()
        
        plt.show()
            
        



