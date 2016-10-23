"""
Rewrite of first code to clarify
"""

##############################################
# imports
import numpy as np
import numpy.linalg as nplin
import matplotlib.pyplot as plt
import MySolarSystem as M
import LeapFrog as lf
import scipy.interpolate as scp


##############################################
# functions

def e_theta(theta, r):
    """
    transforms desired angle off of radial 
    vector to angle off of 1. axis.
    returns radians. arcatn2 input is (y, x)
    """
    theta = theta + np.arctan2(r[1], r[0])
    return theta

def launchPosition(r, R, e_theta, theta):
    """
    position along surface of planet 0 to
    launch from.
    r is the position vector of the planet, 
    R is the radius of the planet, 
    e_theta is function above
    theta is angle from r in radians. 
    """
    return r + R*e_theta(theta, r)

def accelerate(r, m): 
    """
    calculates acceleration on body
    from gravitational pull from 
    body of mass m at a distance r
    """
    r_ = np.linalg.norm(r) # lenght of distance
    return -( G*m*r )/( r_**3 )

def planetvelocity(nr, time, epsilon): 
    """
    Approximating momentary velocity from 2 close
    positions around a time "time".
    nr is which planet,
    epsilon is the small variation across which we
    want to approximate velocity from. 
    """
    Dr = (
        pos_func(time+epsilon)[:,nr] 
        - pos_func(time-epsilon)[:,nr]
         ) # delta r
    Dt = 2.*epsilon # delta t
    return Dr / Dt

def journey(rs, vs, t, dt, t_end):
    """
    simulations of journey between planets. 
    rs is the satellite position vector. 
    vs is the satellite velocity vector. 
    t is the initial time of launch.
    dt is the distance in time per step.
    """
    # half-step of velocity:
    half = np.zeros(2)
    for j in range(N+1):
        # set v0 to v_{1/2}
        if j < N:
            half += lf.v0_half( vs[0], accelerate( rs[0,:] - pos_func(t)[:,j], m[j]), dt )
        else: 
            half += lf.v0_half( vs[0], accelerate( rs[0,:], m[j] ), dt )
    vs[0] += half
    
    # initiating variables for storing least distance and timestamp.
    rs1_m = np.zeros(2)
    rs1_m = rs1_m+4 # AU
    ts1_m = 0 # yrs.
    counts = 0
    # fulfilling the integration proper:
    i = 0
    maxDistance = np.linalg.norm(pos_func(t)[:,1]+r_stable+0.001)
#    while nplin.linalg.norm(rs) < maxDistance:
    while t < t_end:
    # iterate over planets for acceleration
        rs[i+1] = rs[i]
        vs[i+1] = vs[i]
        for j in range(N+1):
            #Leapfrog takes r, v, a, dt, var
            if j < N:
                # iterating over all the planets
                sat  = (
                    lf.LeapFrog( (rs[i] - pos_func(t)[:,j]), vs[i], accelerate,
                        dt, m[j]) )
                rs[i+1] += sat[0]
                vs[i+1] += sat[1]

            else:
                # pull of star.
                sat = lf.LeapFrog( rs[i,:], vs[i], accelerate, dt, m[j] )
                rs[i+1] += sat[0]
                vs[i+1] += sat[1]
        t += dt
        R = pos_func(t)[:,1] - rs[i+1]
        if nplin.linalg.norm(R) < nplin.linalg.norm(rs1_m):
            rs1_m = R
            ts1_m = t
#        print 'relative distance', (
#            abs(nplin.linalg.norm(rs) - maxDistance)/maxDistance )
#        counts += 1
#    print 'counts:', counts
    return rs, vs, t, rs1_m, rs1_m

###############################################################
# stating constants:
G = 4*np.pi**2 #AU**3yr**-2M_s**-1  gravitational constant
T = 10000 #1e4 K temperature in Kelvin
AU = 149597870700 #m in 1 AU
M_sol = 1.9891e30 #kg in 1 solar mass
m_sat = 1100/M_sol # placeholder satelite mass


####################
# collectim simulation data from planet_orbits
T_max = 25 #yrs, timespan of simulation
n = 20000 # nr. of timesteps per year.
t_steps = n*T_max #timesteps for entire simulation

###################
#loading arrays
infile = open('positionsHomePlanet.npy', 'rb')
pos_p = np.load(infile)
time = np.linspace(0, T_max, t_steps) 

pos_func = scp.interpolate.interp1d(time, pos_p)
pos_p0 = pos_func(time[0])

#####################
# data from MySolarSystem
print '----------------------------------------------------------'
syst = M.Myseed() # instancing solar system with seed
N = M.Nplanets(syst) # nr. of planets in system
phi0 = M.init_angle(syst) # initial angles in shared orbital plane
m_s = M.starmass(syst) # mass of star [solar masses]
m_p = M.p_mass(syst) # mass of planet [solar masses]
m = np.append(m_p, m_s) # array of mass of sun and planets
R_p = M.p_radius(syst) #radius of planets[km]
R_p = R_p/AU #planet radius in AU

#########
#escape velocity
v_esc = np.sqrt( (2*G*m_p[0]) / R_p[0] ) 
k = 10
r_stable = R_p[1] * np.sqrt( (m_s / m[1]) * (1./k) )
print '----------------------------------------------------------'


################################################################
# estimating shortest distance between planets 0 and 1.
print '----------------------------------------------------------'
r_min = nplin.linalg.norm(abs(pos_p0[:,1] - pos_p0[:,0]))
r_ = nplin.linalg.norm(r_min)
t_min = 2 # initial value for least time, yrs
t = 3.7
dt = 1e-6
count = 0
#having narrowed search iteratively
while t < 3.71:
    r = pos_func(t)[:,1] - pos_func(t)[:,0]
    r_ = nplin.linalg.norm(r)
    if r_ < r_min:
        t_min = t
        r_min = r_
    t += dt
    count += 1

print '----------------------------------------------------------'
print 'least distance [AU]: ', r_min
print 'at time [yrs]: ', t_min
print '----------------------------------------------------------'


#################################################################
#################################################################
# Satellite launch at planet 1

#########
# Launch criteria
theta = np.pi # 90 degrees in radians
rp0 = pos_func(t_min)[:,0]
eps = 1e-9 # the small breadth epsilon for velocity
day = 1./365 # 1 day's portion of year 

# generating with functions
r0 = launchPosition( rp0, R_p[0], e_theta, theta )

v0 = v_esc * e_theta( theta, rp0 ) + planetvelocity( 0, t_min, eps )*2


# Launch
length1 = int(np.shape(pos_p)[2]*0.1)

rs_launch = np.zeros( (length1, 2) )
vs_launch = np.zeros( (length1, 2) )
vs_launch[0] = v0
rs_launch[0] = r0

dt = 1e-7
t = t_min
tl_end = t + (day)

#print 'initial acceleration'
#print accelerate( rs_launch[0,:] - pos_func(t)[:,j], m[j])

rs_launch, vs_launch, t, rsl_m, tsl_m = (
    journey( rs_launch, vs_launch, t, dt, tl_end )
        )

#print 'rsl_m', rsl_m
################ rsl_m == 1...... #########################
##########################################################
########################################################

#####################################################################
# plotting journey
print '----------------------------------------------------------'
print 'visualizing'
#satelite
plt.plot( rs_launch[0,0], rs_launch[0,1], 'ro', label=('sat start') )
plt.plot( pos_func(t_min)[0,0], pos_func(t_min)[1,0], 'bo', 
    label=('planet 0 at time 3.71 yrs') )
plt.plot( rs_launch[:,0], rs_launch[:,1], 'r', label=('satellite') )
#least distance satellite
#plt.plot( rsl_m[0], rsl_m[1], color=('black'), marker=('v'), label=('least dist') )
plt.plot( pos_func(tsl_m)[0,1], pos_func(tsl_m)[1,1], 'ys', label=('planet least') )
#least distance planets
plt.plot( pos_func(t_min)[0,0], pos_func(t_min)[1,0], 'bo', 
    label=('planet 0 at time 3.71 yrs') )
plt.plot( pos_func(t_min)[0,1], pos_func(t_min)[1,1], 'bo', 
    label=('planet 1 at time 3.71 yrs') )
# planet orbits
for nr in range(N):
    plt.plot( pos_p[0, nr], pos_p[1, nr], label=('planet '+str(nr)) )
plt.legend()
plt.axis('equal')
plt.show()
print '----------------------------------------------------------'
