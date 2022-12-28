import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import shutil
import time


def tweak_xyz(dfx, dfy, dfz, final):
    def tweak(df):
        return (df
                .assign(Average=df
                        .Raw
                        .rolling(wind, center=True, min_periods=1)
                        .mean()
                        )
                .Average)

    dt = dfx.Time[1] - dfx.Time[0]
    wind = int(.010 // dt)
    return (pd.concat([dfx.Time, tweak(dfx), tweak(dfy), tweak(dfz)],
                      axis=1,
                      keys=['Time', 'X', 'Y', 'Z'])
            .query(f'Time < {final}'))


def image_process(x, y, z, rpy, oiv, final, camerarate):
    
    try:
        oiv = float(oiv)
        final = float(final)
        camerarate = float(camerarate)
    except ValueError:
        print('WARNING: oiv, final, or camerarate could not be cast as a floating point number')
        return False


    labelfontsize = 14
    titlefontsize = 20

    if not os.path.exists(os.path.join(os.path.dirname(x), 'generated_images')):
        os.makedirs(os.path.join(os.path.dirname(x), 'generated_images'))

    my_directory = os.path.join(os.path.dirname(x), 'generated_images')

    # read in 2-3 seconds of data and then query it to the final time
    try:
        dfx = pd.read_csv(x, skiprows=[0, 1, 2, 4], usecols=[0, 1], nrows=60000)
        dfy = pd.read_csv(y, skiprows=[0, 1, 2, 4], usecols=[0, 1], nrows=60000)
        dfz = pd.read_csv(z, skiprows=[0, 1, 2, 4], usecols=[0, 1], nrows=60000)
        dfRPY = pd.read_csv(rpy, skiprows=[0, 1, 2, 4], nrows=60000).query(f'Time < {final}')
    except:
        print('WARNING: something went wrong while reading input '
              'files. Double check that you are uploading the correct files.')
        return False

    try:
        xyz = tweak_xyz(dfx, dfy, dfz, final)
    except AttributeError:
        print('WARNING: input files are not in the correct format, or they are corrupted. Cancelling the operation.')
        return False

    # separate the columns into numpy arrays
    timedata = xyz.Time.to_numpy()
    Xaccel_Avg = xyz.X.to_numpy()
    Yaccel_Avg = xyz.Y.to_numpy()
    Zaccel_Avg = xyz.Z.to_numpy()
    Rolldata = dfRPY['Roll Angle'].to_numpy()
    Pitchdata = dfRPY['Pitch Angle'].to_numpy()
    Yawdata = dfRPY['Yaw Angle'].to_numpy()

    # plotting
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex=True, figsize=(30, 8), dpi=64) #gives 512*1920 images

    ax1.plot([oiv, oiv], [min(Xaccel_Avg) - 4, max(Xaccel_Avg) + 4], 'r--', lw=1, label='Time of OIV')  # plot OIV
    ax1.plot(timedata, Xaccel_Avg, 'b:', lw=.6)  # plot all the X data with a light dotted line
    line1, = ax1.plot(timedata[0:0], Xaccel_Avg[0:0], 'b-', lw=2)

    ax2.plot(timedata, Yaccel_Avg, 'b:', lw=.6)  # plot all the X data with a light dotted line
    line2, = ax2.plot(timedata[0:0], Yaccel_Avg[0:0], 'b-', lw=2)  # st

    ax3.plot(timedata, Zaccel_Avg, 'b:', lw=.6)  # plot all the Z data with a light dotted line
    line3, = ax3.plot(timedata[0:0], Zaccel_Avg[0:0], 'b-', lw=2)  #

    ax4.plot(timedata, Rolldata, 'b:', lw=.6)  # plot all the Roll data with a light dotted line
    line4, = ax4.plot(timedata[0:0], Rolldata[0:0], 'b-', lw=2, label='Roll')

    ax4.plot(timedata, Pitchdata, 'r:', lw=.6)  # plot all the Pitch data with a light dotted line
    line5, = ax4.plot(timedata[0:0], Pitchdata[0:0], 'r-', lw=2, label='Pitch')

    ax4.plot(timedata, Yawdata, 'k:', lw=.6)  # plot all the Pitch data with a light dotted line
    line6, = ax4.plot(timedata[0:0], Yawdata[0:0], 'k-', lw=2, label='Yaw')

    ax1.legend()  # legend on ax1 for OIV
    ax4.legend()  # legend on ax3 for Roll and Pitch

    ax2.set_ylabel('Lat Accel (G)', fontsize=labelfontsize)
    ax3.set_ylabel('Vert Accel (G)', fontsize=labelfontsize)  # Z

    ax4.set_xlabel('Time (sec)', fontsize=labelfontsize)
    ax3.set_xlabel('Time (sec)', fontsize=labelfontsize)
    ax1.set_ylabel('Long Accel (G)', fontsize=labelfontsize)  # X
    ax4.set_ylabel('Angles (degrees)', fontsize=labelfontsize)

    ax1.set_xlim([0, final + .005])  # set x limits to 0 and +5 ms, ShareX = true
    ax1.set_ylim([min(Xaccel_Avg) - 2, max(Xaccel_Avg) + 2])  # set y limits -4 and +4 data
    ax4.set_ylim([min([min(Rolldata), min(Pitchdata), min(Yawdata)]) - 1,
                  max([max(Rolldata), max(Pitchdata), max(Yawdata)]) + 1])  # set y limits -4 and +4 data

    ax2.set_ylim([min(Yaccel_Avg) - 2, max(Yaccel_Avg) + 2])  # set y limits -4 and +4 data
    ax3.set_ylim([min(Zaccel_Avg) - 2, max(Zaccel_Avg) + 2])  # set y limits -4 and +4 data

    ax1.grid()
    ax2.grid()
    ax3.grid()
    ax4.grid()

    plt.subplots_adjust(wspace=0.1)

    # for the 10 frames before impact,
    # these plots will not 'move' but the text in the title should update each time
    for i in range(10):
        ax1.set_title(f"t={i - 10:6.0f} ms a=      g", fontsize=titlefontsize)
        ax4.set_title(f"t={i - 10:6.0f} ms R=      P=     Y=     ", fontsize=titlefontsize)
        ax2.set_title(f"t={i - 10:6.0f} ms a=      g", fontsize=titlefontsize)
        ax3.set_title(f"t={i - 10:6.0f} ms a=      g", fontsize=titlefontsize)

        plt.draw()  # required for the set_xdata command to activate
        imgfilename = os.path.join(my_directory, f'{i+1}.png')
        print(f"... saving {imgfilename}")  # keep the user updated where were are at
        plt.savefig(imgfilename, transparent=False)  # save the figure as a png file.

    dt = timedata[1] - timedata[0]
    samples_per_sec = 1 / dt
    increment = samples_per_sec / camerarate
    num_images = int(final/dt//increment)

    for ind in range(num_images):

        x = int(ind * increment)  # every 30 samples

        line1.set_xdata(timedata[0:x+1])
        line1.set_ydata(Xaccel_Avg[0:x+1])

        line2.set_xdata(timedata[0:x+1])
        line2.set_ydata(Yaccel_Avg[0:x+1])

        line3.set_xdata(timedata[0:x+1])
        line3.set_ydata(Zaccel_Avg[0:x+1])

        line4.set_xdata(timedata[0:x+1])
        line4.set_ydata(Rolldata[0:x+1])

        line5.set_xdata(timedata[0:x+1])
        line5.set_ydata(Pitchdata[0:x+1])

        line6.set_xdata(timedata[0:x+1])
        line6.set_ydata(Yawdata[0:x+1])

        ax1.set_title(f"t={timedata[x]:6.0f} ms a={Xaccel_Avg[x]:6.2f} g", fontsize=titlefontsize)

        ax2.set_title(f"t={timedata[x]:6.0f} ms a={Yaccel_Avg[x]:6.2f} g", fontsize=titlefontsize)

        ax3.set_title(f"t={timedata[x]:6.0f} ms a={Zaccel_Avg[x]:6.2f} g", fontsize=titlefontsize)

        ax4.set_title(f"t={timedata[x]:6.0f} ms R={Rolldata[x]:5.1f} P={Pitchdata[x]:5.1f} Y={Yawdata[x]:5.1f}",
                      fontsize=titlefontsize)

        plt.draw()  # required for the set_xdata command to activate

        imgfilename = os.path.join(my_directory, f'{ind+10}.png')
        print(f"... saving {imgfilename}")  # keep the user updated where were are at
        plt.savefig(imgfilename, transparent=False)  # # save the figure as a png file

    return True


def image_process_asi(x, y, z, rpy, asi, oiv, final, camerarate):

    try:
        oiv = float(oiv)
        final = float(final)
        camerarate = float(camerarate)
    except ValueError:
        print('WARNING: oiv, final, or camerarate could not be cast as a floating point number')
        return False

    labelfontsize = 14
    titlefontsize = 20

    if not os.path.exists(os.path.join(os.path.dirname(x), 'generated_images')):
        os.makedirs(os.path.join(os.path.dirname(x), 'generated_images'))

    my_directory = os.path.join(os.path.dirname(x), 'generated_images')

    # read in 2-3 seconds of data and then query it to the final time
    try:
        dfx = pd.read_csv(x, skiprows=[0, 1, 2, 4], usecols=[0, 1], nrows=60000)
        dfy = pd.read_csv(y, skiprows=[0, 1, 2, 4], usecols=[0, 1], nrows=60000)
        dfz = pd.read_csv(z, skiprows=[0, 1, 2, 4], usecols=[0, 1], nrows=60000)
        dfRPY = pd.read_csv(rpy, skiprows=[0, 1, 2, 4], nrows=60000).query(f'Time < {final}')
        dfASI = pd.read_csv(asi, skiprows=[0, 1, 2, 4], nrows=60000).query(f'Time < {final}')
    except:
        print('WARNING: something went wrong while reading input '
              'files. Double check that you are uploading the correct files.')
        return False

    try:
        xyz = tweak_xyz(dfx, dfy, dfz, final)
    except AttributeError:
        print('WARNING: input files are not in the correct format, or they are corrupted. Cancelling the operation.')
        return False

    # separate the columns into numpy arrays
    timedata = xyz.Time.to_numpy()
    Xaccel_Avg = xyz.X.to_numpy()
    Yaccel_Avg = xyz.Y.to_numpy()
    Zaccel_Avg = xyz.Z.to_numpy()
    Rolldata = dfRPY['Roll Angle'].to_numpy()
    Pitchdata = dfRPY['Pitch Angle'].to_numpy()
    Yawdata = dfRPY['Yaw Angle'].to_numpy()
    ASIdata = dfASI.ASI.to_numpy()

    # plotting
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex=True, figsize=(30, 8), dpi=64)  # gives 512*1920 images

    ax1.plot([oiv, oiv], [min(Xaccel_Avg) - 4, max(Xaccel_Avg) + 4], 'r--', lw=1, label='Time of THIV')  # plot OIV
    ax1.plot(timedata, Xaccel_Avg, 'b:', lw=.6)  # plot all the X data with a light dotted line
    line1, = ax1.plot(timedata[0:0], Xaccel_Avg[0:0], 'b-', lw=2)

    ax2.plot(timedata, ASIdata, 'b:', lw=.6)  # plot all the X data with a light dotted line
    line7, = ax2.plot(timedata[0:0], ASIdata[0:0], 'b-', lw=2)  # st

    ax3.plot(timedata, Yaccel_Avg, 'b:', lw=.6)  # plot all the X data with a light dotted line
    line2, = ax3.plot(timedata[0:0], Yaccel_Avg[0:0], 'b-', lw=2, label='Y Accel')  # st

    ax3.plot(timedata, Zaccel_Avg, 'r:', lw=.6)  # plot all the Z data with a light dotted line
    line3, = ax3.plot(timedata[0:0], Zaccel_Avg[0:0], 'r-', lw=2, label='Z Accel')  #

    ax4.plot(timedata, Rolldata, 'b:', lw=.6)  # plot all the Roll data with a light dotted line
    line4, = ax4.plot(timedata[0:0], Rolldata[0:0], 'b-', lw=2, label='Roll')

    ax4.plot(timedata, Pitchdata, 'r:', lw=.6)  # plot all the Pitch data with a light dotted line
    line5, = ax4.plot(timedata[0:0], Pitchdata[0:0], 'r-', lw=2, label='Pitch')

    ax4.plot(timedata, Yawdata, 'k:', lw=.6)  # plot all the Pitch data with a light dotted line
    line6, = ax4.plot(timedata[0:0], Yawdata[0:0], 'k-', lw=2, label='Yaw')

    ax1.legend()  # legend on ax1 for OIV
    ax3.legend()  # legend on ax3 for Y and Z
    ax4.legend()  # legend on ax4 for Roll and Pitch

    ax2.set_ylabel('ASI', fontsize=labelfontsize)
    ax3.set_ylabel('Lat & Vert Accel (G)', fontsize=labelfontsize)  # Z
    ax4.set_xlabel('Time (sec)', fontsize=labelfontsize)
    ax3.set_xlabel('Time (sec)', fontsize=labelfontsize)
    ax1.set_ylabel('Long Accel (G)', fontsize=labelfontsize)  # X
    ax4.set_ylabel('Angles (degrees)', fontsize=labelfontsize)

    ax1.set_xlim([0, final + .005])  # set x limits to 0 and +5 ms, ShareX = true
    ax1.set_ylim([min(Xaccel_Avg) - 2, max(Xaccel_Avg) + 2])  # set y limits -4 and +4 data
    ax4.set_ylim([min([min(Rolldata), min(Pitchdata), min(Yawdata)]) - 1,
                  max([max(Rolldata), max(Pitchdata), max(Yawdata)]) + 1])  # set y limits -4 and +4 data

    ax2.set_ylim([0, max(ASIdata) + .2])  # set asi limits
    ax3.set_ylim([min([min(Yaccel_Avg), min(Zaccel_Avg)]) - 2, max([max(Yaccel_Avg), max(Zaccel_Avg)]) + 2])

    ax1.grid()
    ax2.grid()
    ax3.grid()
    ax4.grid()

    plt.subplots_adjust(wspace=0.1)

    # for the 10 frames before impact,
    # these plots will not 'move' but the text in the title should update each time
    for i in range(10):
        ax1.set_title(f"t={i - 10:6.0f} ms a=      g", fontsize=titlefontsize)
        ax4.set_title(f"t={i - 10:6.0f} ms R=      P=     Y=     ", fontsize=titlefontsize)
        ax2.set_title(f"t={i - 10:6.0f} ms ASI=      ", fontsize=titlefontsize)
        ax3.set_title(f"t={i - 10:6.0f} ms a_y=   g, a_z=    g", fontsize=titlefontsize)

        plt.draw()  # required for the set_xdata command to activate
        imgfilename = os.path.join(my_directory, f'{i + 1}.png')
        print(f"... saving {imgfilename}")  # keep the user updated where were are at
        plt.savefig(imgfilename, transparent=False)  # save the figure as a png file.

    dt = timedata[1] - timedata[0]
    samples_per_sec = 1 / dt
    increment = samples_per_sec / camerarate
    num_images = int(final / dt // increment)

    for ind in range(num_images):
        x = int(ind * increment)  # every 30 samples

        line1.set_xdata(timedata[0:x + 1])
        line1.set_ydata(Xaccel_Avg[0:x + 1])

        line2.set_xdata(timedata[0:x + 1])
        line2.set_ydata(Yaccel_Avg[0:x + 1])

        line3.set_xdata(timedata[0:x + 1])
        line3.set_ydata(Zaccel_Avg[0:x + 1])

        line4.set_xdata(timedata[0:x + 1])
        line4.set_ydata(Rolldata[0:x + 1])

        line5.set_xdata(timedata[0:x + 1])
        line5.set_ydata(Pitchdata[0:x + 1])

        line6.set_xdata(timedata[0:x + 1])
        line6.set_ydata(Yawdata[0:x + 1])

        line7.set_xdata(timedata[0:x + 1])
        line7.set_ydata(ASIdata[0:x + 1])

        ax1.set_title(f"t={timedata[x]:6.0f} ms a={Xaccel_Avg[x]:6.2f} g", fontsize=titlefontsize)

        ax2.set_title(f"t={timedata[x]:6.0f} ms ASI={ASIdata[x]:6.2f}", fontsize=titlefontsize)

        ax3.set_title(f"t={timedata[x]:6.0f} ms a_y={Yaccel_Avg[x]:6.2f} g, a_z={Zaccel_Avg[x]:6.2f} g",
                      fontsize=titlefontsize)

        ax4.set_title(f"t={timedata[x]:6.0f} ms R={Rolldata[x]:5.1f} P={Pitchdata[x]:5.1f} Y={Yawdata[x]:5.1f}",
                      fontsize=titlefontsize)

        plt.draw()  # required for the set_xdata command to activate

        imgfilename = os.path.join(my_directory, f'{ind + 10}.png')
        print(f"... saving {imgfilename}")  # keep the user updated where were are at
        plt.savefig(imgfilename, transparent=False)  # # save the figure as a png file

    return True
