import RPi.GPIO as GPIO
import Adafruit_DHT
import requests
from time import sleep, time
from atexit import register as register_at_exit
from json import loads
import matplotlib.pyplot as plt

WAIT_SECONDS = 1
API_URL = "localhost:5000" #This URL should be changed to the real API once deployed

def exit_handler():
	"""Clean up GPIO pins when process is finished"""
	GPIO.cleanup()
	print("Cleaning up GPIO pins")

  
def getMAC(interface='eth0'):
	"""Return the MAC address of the specified interface"""
	try:
		str = open('/sys/class/net/%s/address' %interface).read()
	except:
		str = "00:00:00:00:00:00"
	return str[0:17]

def send_data(humidity, temperature, mac_address):
	"""Sends data to AWS in JSON format
	
	Keyword arguments:
	humidity -- the value of humidity in percentage
	temperature -- the value of temperature in celsius
	
	"""
	if humidity is None or temperature is None:
		return
	data = {
		"humidity": humidity,
		"temperature": temperature,
		"mac_address": mac_address,
	}
	print(data)

	try:
		requests.post(API_URL + '/store', data=data)
	except requests.exceptions.RequestException as err:
		print("Whoops. Something went wrong: {}".format(err))
	except Exception as inst:
		print("Whoops. Unknow exception: {}".format(inst))


def generate_graph():
	"""Generate a graph with matplot lib of all temperatures"""
	print("Generating image of the last data saved")

	past_hour = int(time() - 3600)
	response = requests.get("{}/search?from={}&json=True".format(API_URL, past_hour))
	items = response.json()
	
	timestamps = [int(item['timestamp']) for item in items]
	temperatures = [float(item['temperature']) for item in items]
	humidities = [float(item['humidity']) for item in items]
	
	fig, ax1 = plt.subplots()
	color = 'tab:red'
	ax1.set_xlabel('timestamp')
	ax1.set_ylabel('temperature', color=color)
	ax1.plot(timestamps, temperatures, '+', color=color)
	ax1.tick_params(axis='y', labelcolor=color)
	
	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

	color = 'tab:blue'
	ax2.set_ylabel('humidity', color=color)  # we already handled the x-label with ax1
	ax2.plot(timestamps, humidities, 'o', color=color)
	ax2.tick_params(axis='y', labelcolor=color)

	fig.tight_layout()  # otherwise the right y-label is slightly clipped
	plt.show()

def main():
	"""Read temperature and humidity from DHT11 sensor"""
	sensor_pin = 26
	button_pin = 19

	sensor = Adafruit_DHT.DHT11
	GPIO.setmode(GPIO.BCM)
	
	GPIO.setup(button_pin, GPIO.IN)
	
	mac_address = getMAC('wlan0')

	while True:
		humidity, temperature = Adafruit_DHT.read_retry(sensor, sensor_pin)
		send_data(humidity, temperature, mac_address)
		
		timeout = time() + WAIT_SECONDS
		while (time() < timeout):
			if GPIO.input(button_pin):
				generate_graph()
		
if __name__ == '__main__':
	print("Starting to read temperature and humidity")
	register_at_exit(exit_handler)
	main()
