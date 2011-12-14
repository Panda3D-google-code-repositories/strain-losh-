###########################################################
###                                                     ###
### Panda3D Configuration File -  User-Editable Portion ###
###                                                     ###
###########################################################

# Uncomment one of the following lines to choose whether you should
# run using OpenGL or DirectX rendering.

load-display pandagl
#load-display pandadx9
#load-display pandadx8
#load-display tinydisplay

window-type  none
window-title Strain

# These control the placement and size of the default rendering window.

#win-origin 50 50
win-size 800 600

# Uncomment this line if you want to run Panda fullscreen instead of
# in a window.

fullscreen #f

# The framebuffer-hardware flag forces it to use an accelerated driver.
# The framebuffer-software flag forces it to use a software renderer.
# If you don't set either, it will use whatever's available.

framebuffer-hardware #t
framebuffer-software #f

# These set the minimum requirements for the framebuffer.
# A value of 1 means: get as many bits as possible,
# consistent with the other framebuffer requirements.

depth-bits 1
color-bits 1
alpha-bits 0
stencil-bits 0
multisamples 0

# These control the amount of output Panda gives for some various
# categories.  The severity levels, in order, are "spam", "debug",
# "info", "warning", and "error"; the default is "info".  Uncomment
# one (or define a new one for the particular category you wish to
# change) to control this output.

notify-level warning
default-directnotify-level warning

# These specify where model files may be loaded from.  You probably
# want to set this to a sensible path for yourself.  $THIS_PRC_DIR is
# a special variable that indicates the same directory as this
# particular Config.prc file.

##model-path    $MAIN_DIR
##model-path    $THIS_PRC_DIR/..
##model-path    $THIS_PRC_DIR/../models

# This enable the automatic creation of a TK window when running
# Direct.

want-directtools  #f
want-tk           #f

# Enable/disable performance profiling tool and frame-rate meter

want-pstats            #f
show-frame-rate-meter  #t
frame-rate-meter-scale        0.03
frame-rate-meter-side-margin  0.1

# Enable audio using the FMOD audio library by default:

audio-library-name p3fmod_audio

# Enable the use of the new movietexture class.

use-movietexture #t

# The new version of panda supports hardware vertex animation, but it's not quite ready

hardware-animated-vertices #f

# Enable the model-cache, but only for models, not textures.

model-cache-dir $MAIN_DIR/tmp
model-cache-textures #f

# This option specifies the default profiles for Cg shaders.
# Setting it to #t makes them arbvp1 and arbfp1, since these
# seem to be most reliable. Setting it to #f makes Panda use
# the latest profile available.
# This default profile can be overriden by any profile setting
# from within the application.

basic-shaders-only #f

#for setting a fixed framerate of N frames per second
##clock-mode limited
##clock-frame-rate 32

#Set this true to interpolate character animations between frames,
#or false to hold each frame until the next one is ready
interpolate-frames 1

#custom app resources dirs
model-path $MAIN_DIR/data/models/
model-path $MAIN_DIR/data/fonts/
model-path $MAIN_DIR/data/shaders/
model-path $MAIN_DIR/data/textures/
sound-path $MAIN_DIR/data/sounds/
particle-path $MAIN_DIR/data/particles/

# Set this true to yield the timeslice at the end of the frame to be more polite to other applications that are trying to run.
yield-timeslice #t

# Custom Strain parameters
server-ip 127.0.0.1
server-port 56005