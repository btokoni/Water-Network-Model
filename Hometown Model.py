#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Import matplotlib notebook for pyplot


# In[2]:


import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'notebook')

import wntr
import wntr.network.base as base
import wntr.network.controls as controls
import wntr.network.elements as elements


# In[3]:


# create empty_water_network model. This would create structures needed to set up node, pipes and water supply. 
# Alternatively: inp_file = 'L-Town.inp'


# In[4]:


ewn = wntr.network.WaterNetworkModel() 


# In[5]:


# Define Demand patterns


# In[6]:


ewn.add_pattern('flat',[1])
ewn.add_pattern('linear',[0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8,
                         0.85,0.9,0.95,1,1.05,1.1,1.15,1.2,1.25])
ewn.add_pattern('realistic',
               [0.644,0.404,0.25 ,0.176,0.152,0.289,0.93 ,1.396,1.469,1.476,1.453,1.424,
                1.392,1.361, 1.278,1.143,1.134,1.19 ,1.247,1.295,1.318,1.323,1.114,0.905])


# In[7]:


# Adding 4 nodes via add_junction function


# In[8]:


for i in range(1,3):
    for j in range(1,3):
        name = 'n' + str(2*(i-1)+(j-1)+1)
        ewn.add_junction(name, base_demand=0.01*i*j,
                        demand_pattern='flat',
                        elevation=100,
                        coordinates=(i,j)) 


# In[9]:


# water supper to the network must come from somewehere. namely: reservoirs(Nodes). 
# They are connected to the system via pipes(Links).
# 1. Add the reservioir to the network


# In[10]:


ewn.add_reservoir('R1', base_head = 125, head_pattern='pat1', coordinates=(1,4))


# In[11]:


# Nodes = Junctions, Tanks, Reservoirs
# Links = Pipes, Pumps, C_Valves
# Adding pipes to the networks P1-P5 on Nodes n1 and n2, n1 and n3, n2 and n3, n3 and n4, R1 and n2
# I used n1 n2,  n1 n3,  n2 n4,  n3 n4,  R1 n2


# In[12]:


ewn.add_pipe('p1', 'n1', 'n2',
            length=100, diameter=0.5,roughness=100, minor_loss=0.0, status='OPEN')
ewn.add_pipe('p2', 'n1', 'n3',
            length=100, diameter=0.5,roughness=100, minor_loss=0.0, status='OPEN')
ewn.add_pipe('p3', 'n2', 'n4',
            length=100, diameter=0.5,roughness=100, minor_loss=0.0, status='OPEN')
ewn.add_pipe('p4', 'n3', 'n4',
            length=100, diameter=0.5,roughness=100, minor_loss=0.0, status='OPEN')
ewn.add_pipe('p5', 'R1', 'n2',
            length=100, diameter=0.5,roughness=100, minor_loss=0.0, status='OPEN')


# In[13]:


# plot the network


# In[14]:


wntr.graphics.plot_network(ewn, node_size = 200, node_labels = True, node_attribute = 'elevation')


# In[15]:


# Modifying the network..components can be modified
# steps..Select component, access attribute, set new value


# In[16]:


sel_node = [ewn.get_node('n1'),ewn.get_node('n3')]
sel_node[0].elevation = 90
sel_node[1].elevation = 103

pat = ewn.get_pattern('realistic')
sel_node[0].demand_timeseries_list.append((0.2,pat))
sel_node[1].demand_timeseries_list.append((0.15,pat))


# In[17]:


# Plot the modified network


# In[18]:


wntr.graphics.plot_network(ewn, node_size = 200, node_labels = True,
                          node_attribute ='elevation')


# In[19]:


# Advanced Model Elements: Adding pressure reduction valves to regulate pressure for the new node which has a lower elevation


# In[20]:


ewn.add_junction('n5', base_demand=0.1,
                        demand_pattern='realistic',
                        elevation=50,
                        coordinates=(2,5))

ewn.add_valve('PRV_1', 'n4', 'n5', diameter=0.15, valve_type='PRV', minor_loss=0.0, setting=35)


# In[21]:


# where pumps are present, tanks might be required to act as buffers, so we add a tank. Tank is added. 


# In[22]:


ewn.add_tank('T_1', elevation=200, coordinates=(5,1),
            init_level=3, min_level=1, max_level=4, diameter=16)


# In[23]:


# KEY STEPS for next line of code: 
# The new node (Junction) is created
# Pressure valve is added to the node
# The node is connected to a Tank
# Pump curve is defined
# Pump is added as a head pump to the system, conncetung node n3 and T1


# In[24]:


ewn.add_junction('n6', base_demand=0.1,
                        demand_pattern='realistic',
                        elevation=200,
                        coordinates=(6,1))

ewn.add_pipe('p6', 'T_1', 'n6',
            length=100, diameter=0.5,roughness=100, minor_loss=0.0, status='OPEN')

ewn.add_curve('PUMP_1_curve', 'HEAD', [(0.00,126.67),(0.0076,88.67),(0.0138,0.00)])

ewn.add_pump('PUMP_1', 'n3', 'T_1', pump_type='HEAD', pump_parameter='PUMP_1_curve')


# In[25]:


# Controls are essential for operating components z.B to insert conditonal changes.
# Stopping pump if tank level is above(>=) 3.9m 


# In[26]:


condition = controls.ValueCondition(ewn.get_node('T_1'),'level','>=',3.9)
action = controls.ControlAction(ewn.get_link('PUMP_1'), 'status', base.LinkStatus(0))
control = controls.Control(condition, action, priority=3)
ewn.add_control('CONTROL_1', control)


# In[27]:


# Check if pump is closed. Use the print function


# In[28]:


for control in ewn.controls():
    print(control)


# In[29]:


# Set the second control so that the pump resumes when level reaches(<=)2.4m. LinkStatus should be set to (1) means'open'.
# Switch to control 2


# In[30]:


condition = controls.ValueCondition(ewn.get_node('T_1'),'level','<=',2.4)
action = controls.ControlAction(ewn.get_link('PUMP_1'), 'status', base.LinkStatus(1))
control = controls.Control(condition, action, priority=3)
ewn.add_control('CONTROL_2', control)


# In[31]:


# Check controls i.e Control_1 and Control_2


# In[32]:


for control in ewn.controls():
    print(control)


# In[33]:


# Plot the Network


# In[34]:


wntr.graphics.plot_network(ewn, node_size=200, node_labels=True, link_labels=True, node_attribute='elevation')


# In[35]:


# Save file format as .inp. CMH  for easier readability of the file


# In[37]:


ewn.options.hydraulic.en2_units = 'CMH'

ewn.write_inpfile('My_Hometown.inp')


# In[ ]:




