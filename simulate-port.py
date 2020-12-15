import os, pty, serial, time

master, slave = pty.openpty()
name = os.ttyname(slave)
print(f'Opening port on {name}...')

print('Starting')

while True:
	char = os.read(master, 1)
	if char == b'1':
		print('Activating...')
		os.write(master, bytes('1', 'utf-8'))
		time.sleep(12)
		print('Deactivating...')
		os.write(master, bytes('0', 'utf-8'))
	if char == b'2':
		os.write(master, bytes('2', 'utf-8'))
