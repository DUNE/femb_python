# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 16:43:58 2018

@author: protoDUNE
"""
import matplotlib.pyplot as plt
plt.switch_backend('agg')

class plot_functions:
    def __init__(self, config_file = None):
        """
        Initialize this class (no board communication here. Should setup self.femb_udp as a femb_udp instance, get FE Registers, etc...)
        """
        if (config_file == None):
            from femb_python.configuration import CONFIG
            self.config = CONFIG
        else:
            self.config = config_file
            
        self.sample_period = float(self.config["DEFAULT"]["SAMPLE_PERIOD"])

    def plot_chip(self, data, plot_name, title_name, power, length = 1000):
        
        time_x = []       
        for j in range(length):
            time_x.append(self.sample_period * j)

        fig = plt.figure(figsize=(16, 12), dpi=80)
        plt.title(title_name, fontsize = 20)
        overlay_ax = plt.gca()
        overlay_ax.spines['top'].set_color('none')
        overlay_ax.spines['bottom'].set_color('none')
        overlay_ax.spines['left'].set_color('none')
        overlay_ax.spines['right'].set_color('none')
        overlay_ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        overlay_ax.set_xlabel('Time (counts)')
        overlay_ax.set_ylabel('ADC Counts')
        overlay_ax.yaxis.set_label_coords(-0.035,0.5)
        
        vdda_comment = "VDDA --> {} V, {} mA".format(round(power[0][1],2), round(power[0][2] * 1000, 2))
        overlay_ax.text(0.00,-0.04,vdda_comment,transform=overlay_ax.transAxes, fontsize = 10)
        
        vddp_comment = "VDDP --> {} V, {} mA".format(round(power[1][1],2), round(power[1][2] * 1000, 2))
        overlay_ax.text(0.15,-0.04,vddp_comment,transform=overlay_ax.transAxes, fontsize = 10)
        
        ax1 = fig.add_subplot(16,1,16)
        plt.plot(time_x, data[0][:length])
        start, end = ax1.get_ylim()
        ax1.yaxis.set_ticks(range(int(start), int(end), int(end/4)))

#        plt.setp(ax1.get_xticklabels(), fontsize=12)
        ax1.set_title("Chn 0")
        ax2 = ax1.twinx()
        ax2.set_ylabel("Chn 0", rotation = 0)
        ax2.spines['top'].set_color('none')
        ax2.spines['bottom'].set_color('none')
        ax2.spines['left'].set_color('none')
        ax2.spines['right'].set_color('none')
        ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        for j in range(15):
            time_x = []         
            
            for k in range(length):
                time_x.append(self.sample_period * k)
            ax = fig.add_subplot(16,1,15-j, sharex=ax1)
            plt.plot(time_x, data[j+1][:length])
            start, end = ax1.get_ylim()
            ax.yaxis.set_ticks(range(int(start), int(end), int(end/4)))
            for item in (ax.get_xticklabels()):
                item.set_fontsize(20)
            plt.setp(ax.get_xticklabels(), visible=False)
            
            ax2 = ax.twinx()
            ax2.set_ylabel("Chn " + str(j+1), rotation = 0)
#               ax2.spines['top'].set_color('none')
#               ax2.spines['bottom'].set_color('none')
#               ax2.spines['left'].set_color('none')
#               ax2.spines['right'].set_color('none')
            ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            pos1 = ax2.get_position() # get the original position 
            pos2 = [pos1.x0 + 0.025, pos1.y0 + 0.005,  pos1.width , pos1.height ] 
            ax2.set_position(pos2) # set a new position
            
        
        
        plt.subplots_adjust(wspace=0, hspace=0, top = 0.95, bottom = 0.05, right = 0.95, left = 0.05)
        
        plt.savefig (plot_name)  
        plt.close(fig)
#        print("Plot--> Data Saved as " + plot_name + "_{}".format(chip_num))
        
    def quickPlot(self, data):
        
        time = []
        for i in range(len(data)):
            time.append(self.sample_period * i)
            
            
        fig = plt.figure(figsize=(16, 12), dpi=80)
        overlay_ax = fig.add_subplot(1,1,1)
        overlay_ax.set_ylim(0, 1000 * float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]))
        overlay_ax.set_xlabel('Time (counts)')
        overlay_ax.set_ylabel('ADC Counts')
        overlay_ax.plot(time, data)
        
        #plt.show()
        
        return [overlay_ax, fig]
        
    def debugScatterplot(self, data, peaks_index, title, save_location):
        
        time = []
        for i in range(len(data)):
            time.append(self.sample_period * i)
            
            
        fig = plt.figure(figsize=(16, 12), dpi=80)
        overlay_ax = fig.add_subplot(1,1,1)

        overlay_ax.set_xlabel('Time (counts)')
        overlay_ax.set_ylabel('ADC Counts')
        overlay_ax.plot(time, data)
        
        try:
            for j in peaks_index:
                y_value = data[j]
                overlay_ax.scatter(j * self.sample_period, y_value, marker='x')
        except TypeError:
            pass
            
        overlay_ax.set_title(title)
        overlay_ax.title.set_fontsize(20)
        for item in ([overlay_ax.xaxis.label, overlay_ax.yaxis.label] + overlay_ax.get_xticklabels() + overlay_ax.get_yticklabels()):
            item.set_fontsize(20)
                
        plt.savefig(save_location)
        
        plt.close()