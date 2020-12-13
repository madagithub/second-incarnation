import os, pty, serial, time

master, slave = pty.openpty()
name = os.ttyname(slave)
print(f'Opening port on {name}...')

input()
print('Starting')

while True:
	print('Before read')
	char = os.read(master, 1)
	print(f'Read {char}')
	if char == b'1':
		print('Activating...')
		os.write(master, bytes('1', 'utf-8'))
		time.sleep(3)
		print('Deactivating...')
		os.write(master, bytes('0', 'utf-8'))
	if char == b'2':
		os.write(master, bytes('2', 'utf-8'))
