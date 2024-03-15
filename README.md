# Second Incarnation

## General
This exhibit provides a UI that interacts with Didi Vardi's machine.
The opening screen allows activating the machine with a button.
While the machine is running, it is possible to browse each machine part description using main screen buttons.
Once the machines stops, a cooldown timer is shown and the exhibit counts down the time until it will be operational again, showing the UI with the activation button again.

## Installation & Run
The exhibit runs using python 3 on linux, using the pygame engine.

After the latest python 3 installation, use:

```
pip3 install pygame
pip3 install pyserial
```

To install all necessary packages.

Then, to run, go to the root project dir and run:

```
python3 second-incarnation.py
```

## Config
The exhibit supports a vast array of configurations using a config json file located in assets/config/config.json
Following is a complete description of all options:

### defaultLanguage

Specifies the default language loaded on startup (he/en/ar).
Note that the prefix to put here should be identical to the prefix defined in the language array (see details below).

### languages

This is an array specifying all the language configurations the exhibit supports.
For each language, the prefix defines its prefix (en/he/ar) to be used in the defaultLanguage config (see above), and the rtl states if the language is rtl or not (true/false).

Here's an example of a language definition:

```
{
    "prefix": "en",
    "rtl": false
}
```

### subscreenButtons

This is an array configuring the location of all machine parts screens (and the in memory of Ron Vardi screen).
For each button, the x and y coordinates of its top left corner are specified with keys x and y (x increasing from left to right, y increasing from top to bottom),
the various image file names are specified for the regular button image (image key), the tapped button image (tappedImage key) and the image showing the screen itself after the button is clicked (screenImage key). The image filename should be specified without any path, and placed in assets/images/ar for the Arabic version, assets/images/en for the Hebrew version and assets/images/he for the Hebrew version. The name must be identical in all languages, as specified in the config.
Finally, the name key gives a name for the button, which will be shown in the log when it is clicked.

Here's an example of a subscreenButton defintiion:

```
{
    "x": 486,
    "y": 685,
    "name": "BROWN",
    "image": "1-button.png",
    "tappedImage": "1-button-tapped.png",
    "screenImage": "1.png"
}
```

### showFPS

This key can be set to true to show an FPS (frames per second) value and measure performance issues. FPS should be ideally between 30 and 60.

### touch, touchDeviceName, touchMaxX, touchMaxY

These 4 keys define the characteristics of the touch screen connected to the exhibit.
touch should be set to true for the exhibit to use touch (otherwise a mouse is supported).
touchDeviceName is a partial name that is used to match the touch screen device. Use a partial name that is also unique.
You can enumerate all linux devices using this command:

```
lsinput
```

Finally, the touchMaxX and touchMaxY represent the logical screen resolution that evdev works with.
The exhibit will convert these coordinates to the actual screen resolution coordinates.
These usually change with the screen size, and are usually 4096x4096 but can also be 2048x2048 and 1024x1024, or other numbers potentially.
The best way to find out the proper value, is to add print statements in the TouchScreen.py file, in the readTouch method, in case the event type is ecodes.EV_ABS.

Like this:
```
elif event.type == ecodes.EV_ABS:
	absEvent = categorize(event)

	if absEvent.event.code == 0:
		currX = absEvent.event.value
	elif absEvent.event.code == 1:
		currY = absEvent.event.value

	print(currx, curry)
```

Then, run the exhibit, and touch various corners of the screen. It will be very easy to conclude on the max value sknowing they are a power of 2.

## Log
The exhibit supports a rotating log named second-incarnation.log in the root directory, that logs the following events:
* START (the exhibit loads)
* INIT (exhibit initalization is done)
* RESET (exhibit was idle for 300 seconds, goes back to showing home screen)
* PLAY (machine was activated)
* HOME (home button was clicked, out of any sub screen)
* SUBSCREEN,NAME (subscreen named NAME button was clicked and moved to, names are specified in config.json in the subscreenButtons array, and the key name of every object in this array)
* LANGUAGE_CHANGED,prefix (lngaugaed changed to prefix: en/ar/he)
* ERROR,Failed to open serial port (when serial port could not be opened)
* ERROR,Failed to write to serial port (when serial port could not be written to)
* ERROR,Failed to read from serial port (when serial port could not be read from)
* ERROR,Error occured! (when a general error occured)


## Serial Port Interface
The exhibit requires a serial port connection the machine, so it can activate it, and know when it stopped working.
When the exhibit wants to activate the machine, it sends a 1 byte to the serial port. It then waits for either a stop (a 0 byte) or an emergency stop (a 2 byte).
When they arrive, it knows the machine has stopped, and then shows a cool down timer of 3 minutes.
If the serial signal fails to arrive, then after 15 minutes the exhibit assumes the machines stopped without signaling so, and continues to the cool down timer.
Also, if sending the command fails, the exhibit retries until successful.

The machine should be connected to the linux serial port /dev/ttyUSB0.
If it uses another port, the code needs to be updated accordingly, as it is hard-coded two times into the exhibit code.
For testing purposes when the machine is not at hand, a simulation script exists in the root directory, called simulate-port.py.

When running it like this:
```
python3 simulate-port.py
```

It gives this example input:
```
Opening port on /dev/ttys009...
Starting
```

If you then take the device name and replace the regular device name with it in the exhibit code (both in the constant and one more place), then the simulated port will "act" as the machine.
i.e. it will get the 1 byte call, simulate activation of the machine and time passing by, then send 1 when over.
It will right Activating... or Deactivating... in due time.

Using this script to check the exhibit is very useful.
Remember to bring back the device name to the default one when done.
