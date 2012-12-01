#!/usr/bin/python -tt

# BZRC Imports
from bzrc import BZRC, Command

# OpenGL Imports
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
#from numpy import zeros
import numpy

# Misc Imports
import sys, math, time, random


def normalize_angle(angle):
    '''Make any angle be between +/- pi.'''
    angle -= 2 * math.pi * int (angle / (2 * math.pi))
    if angle <= -math.pi:
        angle += 2 * math.pi
    elif angle > math.pi:
        angle -= 2 * math.pi
    return angle
    
def dist(pt1, pt2):
    '''Calculate distance between two points'''
    return math.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
    
def midpoint(pt1, pt2):
    return ((pt1[0] + pt2[0]) / 2, (pt1[1] + pt2[1]) / 2)
    
def add(vector1, vector2):
    return (vector1[0] + vector2[0], vector1[1] + vector2[1])
    
# grid is a numpy grid, center is a point in the grid to center at, size is the size of the box that should be averaged
def subgrid(grid, center, size):
    width, height = grid.shape
    left = int(max(0, center[0] - size/2))
    right = int(min(width, center[0] + size/2))
    bottom = int(max(0, center[1] - size/2))
    top = int(min(height, center[1] + size/2))
    return grid[bottom:top, left:right]
    
def average(l):
    return reduce(lambda x, y: x + y, l) / len(l)

def average_grid(grid, center, size):
    return numpy.mean(subgrid(grid, center, size))
    
def min_grid(grid, center, size):
    return numpy.min(subgrid(grid, center, size))
    
def max_grid(grid, center, size):
    return numpy.max(subgrid(grid, center, size))

def deg2rad(n):
    return n * (math.pi / 180.0)
    
def rad2deg(n):
    return n * (180.0 / math.pi)
    

class Agent(object):

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        
        # Initialize World Map / Belief Grid
        #init_window(int(self.constants["worldsize"]), int(self.constants["worldsize"]))
        #self.bel_grid = numpy.array(list(list(.75 for j in range(int(self.constants["worldsize"]))) for i in range(int(self.constants["worldsize"]))))
        #self.conf_grid = numpy.array(list(list(0.0 for j in range(int(self.constants["worldsize"]))) for i in range(int(self.constants["worldsize"]))))
        #update_grid_display(self.conf_grid)
        
        self.commands = []
        self.tanks = {tank.index:Tank(bzrc, self, tank) for tank in self.bzrc.get_mytanks()}
        
        ''' Available Constants ''' '''
        CONSTANT        EX. OUTPUT
        team            blue
        worldsize       800
        hoverbot        0
        puppyzone       30
        tankangvel      0.785398163397
        tanklength      6
        tankradius      4.32
        tankspeed       25
        tankalive       alive
        tankdead        dead
        linearaccel     0.5
        angularaccel    0.5
        tankwidth       2.8
        shotradius      0.5
        shotrange       350
        shotspeed       100
        flagradius      2.5
        explodetime     5
        truepositive    1
        truenegative    1
        '''
        
        self.write_kalman_fields("test1", 10, 10, 0)
        self.write_kalman_fields("test2", 100, 10, 0)
        self.write_kalman_fields("test3", 10, 100, 0)
        self.write_kalman_fields("test4", 100, 100, .5)
        self.write_kalman_fields("test5", 100, 100, .9999)
    
    def write_kalman_fields(self, file, sigma_x, sigma_y, rho):
        
        with open("{0}.gpi".format(file), 'w+') as out:
            # header
            out.write("set xrange [-400.0: 400.0]\n")
            out.write("set yrange [-400.0: 400.0]\n")
            out.write("set pm3d\n")
            out.write("set view map\n")
            out.write("unset key\n")
            out.write("set size square\n")
            # Print to png when run
            out.write("set term png\n")
            out.write("set output \"{0}.png\"\n".format(file))
            out.write("\n")
            out.write("unset arrow\n")
            #out.write("set arrow from 0, 0 to -150, 0 nohead front lt 3\n")
            #out.write("set arrow from -150, 0 to -150, -50 nohead front lt 3\n")
            #out.write("set arrow from -150, -50 to 0, -50 nohead front lt 3\n")
            #out.write("set arrow from 0, -50 to 0, 0 nohead front lt 3\n")
            #out.write("set arrow from 200, 100 to 200, 330 nohead front lt 3\n")
            #out.write("set arrow from 200, 330 to 300, 330 nohead front lt 3\n")
            #out.write("set arrow from 300, 330 to 300, 100 nohead front lt 3\n")
            #out.write("set arrow from 300, 100 to 200, 100 nohead front lt 3\n")
            out.write("\n")
            out.write("set palette model RGB functions 1-gray, 1-gray, 1-gray\n")
            out.write("set isosamples 100\n")
            out.write("\n")
            out.write("sigma_x = {0}\n".format(sigma_x))
            out.write("sigma_y = {0}\n".format(sigma_y))
            out.write("rho = {0}\n".format(rho))
            out.write("splot 1.0/(2.0 * pi * sigma_x * sigma_y * sqrt(1 - rho**2) ) * exp(-1.0/2.0 * (x**2 / sigma_x**2 + y**2 / sigma_y**2 - 2.0*rho*x*y/(sigma_x*sigma_y) ) ) with pm3d\n")
            
            #out.write("set title \"Fields\"\nset xrange [-400.0 : 400.0]\nset yrange [-400.0 : 400.0]\nunset key\nset size square\nset terminal wxt size 1600,1600\nset term png\nset output \"{0}.png\"\n\n".format(file))
            
            '''
            # write the body of the fields
            for x in range(-380, 390, 40):
                for y in range(-380, 390, 40):
                    vector = (0, 0)
                    for field in fields:
                        vector = add(vector, field.get_force((x, y)))
                    if (vector[0] != float("inf") and vector[1] != float("-inf")):
                        scaling_factor = 1.0/4.0
                        out.write("set arrow from {0}, {1} to {2}, {3}\n".format(x - vector[0]/(2 / scaling_factor), y - vector[1]/(2 / scaling_factor), x + vector[0]/(2 / scaling_factor), y + vector[1]/(2 / scaling_factor)))
                        #pass
                    
            # start plot
            out.write("plot '-' with lines\n0 0 1 1\n")
                
            # end plot
            out.write("e\n");
            '''
    
    def tick(self, time_diff):
        '''Some time has passed; decide what to do next'''
        
        # Reset my set of commands (we don't want to run old commands)
        self.commands = []
        
        for bot in self.bzrc.get_mytanks():
            # ALGORITHM
            # 
            # for all_tanks
            #  if should_sample()
            #   call occgrid
            #   update bel/conf grid
            #  if picknewpoint()
            #   picknewpoint()
            #  movetopoint()
            # 
            
            # Get the tank and update it with what we received from the server
            tank = self.tanks[bot.index]
            tank.update(bot)
            
            
            self.commands.append(tank.get_desired_movement_command(time_diff, int(self.constants["tankspeed"])))

        # Send the movement commands to the server
        results = self.bzrc.do_commands(self.commands)
        
    
class Tank(object):
    
    def __init__(self, bzrc, agent, tank):
        self.bzrc = bzrc
        self.agent = agent
        self.previous_error_angle = 0
        self.previous_error_speed = 0
        self.x = None
        self.y = None
        self.update(tank)
        self.prev_x = self.x
        self.prev_y = self.y
        # These variables are now used to point to the currently estimated position of the enemy tank, and its current velocity (x and y components)
        self.target = (random.randint(-400, 400), random.randint(-400, 400))
        self.target_velocity = (0, 0)
        #print "Initial Target:", self.target
        #self.pick_point(0)
    
    def update(self, tank):
        self.prev_x = self.x
        self.prev_y = self.y
        self.index = tank.index;
        self.callsign = tank.callsign;
        self.status = tank.status;
        self.shots_avail = tank.shots_avail;
        self.time_to_reload = tank.time_to_reload;
        self.flag = tank.flag;
        self.x = tank.x;
        self.y = tank.y;
        self.angle = tank.angle;
        self.vx = tank.vx;
        self.vy = tank.vy;
        self.angvel = tank.angvel;
    
    def get_desired_movement_command(self, time_diff, maxspeed):
        # PD Controller stuff to make movement smoother
        delta_x = self.target[0] - self.x
        delta_y = self.target[1] - self.y
        #print "Delta:", (delta_x, delta_y)
        
        target_angle = math.atan2(delta_y, delta_x)
        current_angle = normalize_angle(self.angle)
        error_angle = normalize_angle(target_angle - current_angle);
        #print "Error:", int(rad2deg(error_angle)), "Target:", int(rad2deg(target_angle)), "Current:", int(rad2deg(current_angle))
        # clamp the speed to -1 to 1 (technically, 0 to 1)
        # Base the speed on the current angle as well
        target_speed = math.cos(error_angle) * maxspeed
        current_speed = math.sqrt(math.pow(self.vy, 2) + math.pow(self.vx, 2))
        error_speed = target_speed - current_speed;
        #print "Error:", int(error_speed), "Target:", int(target_speed), "Current:", int(current_speed)
        
        proportional_gain_angle = 2.25
        proportional_gain_speed = 1.0
        derivative_gain_angle = 0.5
        derivative_gain_speed = 0.1
        
        send_angvel = proportional_gain_angle * error_angle + derivative_gain_angle * ((error_angle - self.previous_error_angle) / time_diff)
        send_speed = proportional_gain_speed * error_speed + derivative_gain_speed * ((error_speed - self.previous_error_speed) / time_diff)
        
        self.previous_error_angle = error_angle
        self.previous_error_speed = error_speed
        
        magnitude = math.sqrt(delta_x**2 + delta_y**2)
        if magnitude == 0:
            magnitude = 1
        direction = (delta_x / magnitude, delta_y / magnitude)
        
        '''
        #dist((self.vx, self.vy), (0, 0))/time_diff < 1 and math.fabs(error_angle) < math.pi/6: # Did we not move very far, and were we facing the right way?
        if average_grid(self.agent.bel_grid, (self.x + 5 * direction[0] + 400, self.y + 5 * direction[1] + 400), 10) > .8 or (self.x == self.prev_x and self.y == self.prev_y): # Are we reasonably sure we're running into an obstacle right now?
            # If we are hitting an obstacle, send the max angular velocity
            send_angvel = 1
            send_speed = 1
        #    print "true"
        #else:
        #    print "false"
        '''
        send_speed = 0;
            
        return Command(self.index, send_speed, send_angvel, 1)

def main():
    # Process CLI arguments.
    try:
        execname, host, port = sys.argv
    except ValueError:
        execname = sys.argv[0]
        print >>sys.stderr, '%s: incorrect number of arguments' % execname
        print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
        sys.exit(-1)
        
    #print "Running Tyler & Morgan's Super Smart Flag Capturer"

    # Connect.
    #bzrc = BZRC(host, int(port), debug=True)
    bzrc = BZRC(host, int(port))
    
    agent = Agent(bzrc)

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()

if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4