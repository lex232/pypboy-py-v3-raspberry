import io
import os
import xml.etree.ElementTree as ET
import requests
import numpy 
from numpy.fft import fft 
from math import log10 
import math
import pygame


class Maps(object):

	nodes = {}
	ways = []
	tags = []
	origin = None
	width = 0
	height = 0

	SIG_PLACES = 3
	GRID_SIZE = 0.001

	def __init__(self, *args, **kwargs):
		super(Maps, self).__init__(*args, **kwargs)

	def float_floor_to_precision(self, value, precision):
		for i in range(precision):
			value *= 10
		value = math.floor(value)
		for i in range(precision):
			value /= 10
		return value

	def fetch_grid(self, coords):
		# lat = self.float_floor_to_precision(coords[0], self.SIG_PLACES)
		# lng = self.float_floor_to_precision(coords[1], self.SIG_PLACES)
		# print lat, lng
		lat = coords[0]
		lng = coords[1]

		return self.fetch_area([
				lng - self.GRID_SIZE,
				lat - self.GRID_SIZE,
				lng + self.GRID_SIZE,
				lat + self.GRID_SIZE
		])

	def fetch_area(self, bounds):
		self.width = (bounds[2] - bounds[0]) / 2
		self.height = (bounds[3] - bounds[1]) / 2
		self.origin = (
				bounds[0] + self.width,
				bounds[1] + self.height
		)

		cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache')
		os.makedirs(cache_dir, exist_ok=True)
		cache_key = "%.6f_%.6f_%.6f_%.6f" % (bounds[0], bounds[1], bounds[2], bounds[3])
		cache_file = os.path.join(cache_dir, "map_%s.xml" % cache_key)

		if os.path.exists(cache_file):
			print("[Map loaded from cache]")
			with open(cache_file, 'r', encoding='UTF-8') as f:
				xml_text = f.read()
		else:
			url = "http://www.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (
							bounds[0],
							bounds[1],
							bounds[2],
							bounds[3]
					)
			print("[Fetching maps... (%f, %f) to (%f, %f)]" % (
							bounds[0],
							bounds[1],
							bounds[2],
							bounds[3]
					))
			try:
				response = requests.get(url, timeout=60)
				response.raise_for_status()
			except Exception as e:
				print("[Map fetch error: %s]" % e)
				return
			xml_text = response.text
			try:
				with open(cache_file, 'w', encoding='UTF-8') as f:
					f.write(xml_text)
			except Exception as e:
				print("[Map cache write error: %s]" % e)

		self.nodes = {}
		self.ways = []
		self.tags = []
		try:
			context = ET.iterparse(io.StringIO(xml_text), events=('end',))
			for event, elem in context:
				if elem.tag == 'node':
					node_id = elem.get('id')
					lat, lon = elem.get('lat'), elem.get('lon')
					if lat and lon:
						self.nodes[node_id] = (lat, lon)
						node_tags = {t.get('k'): t.get('v') for t in elem.findall('tag')}
						if 'name' in node_tags and 'amenity' in node_tags:
							self.tags.append((float(lat), float(lon), node_tags['name'], node_tags['amenity']))
					elem.clear()
				elif elem.tag == 'way':
					waypoints = []
					for nd in elem.findall('nd'):
						ref = nd.get('ref')
						if ref in self.nodes:
							lat, lon = self.nodes[ref]
							waypoints.append((float(lat), float(lon)))
					if len(waypoints) >= 2:
						self.ways.append(waypoints)
					elem.clear()
		except Exception as e:
			print("[Map parse error: %s]" % e)

	def fetch_overpass(self, coords, radius):
		lat, lon = coords[0], coords[1]
		self.ways  = []
		self.nodes = {}
		self.tags  = []
		self.width  = radius
		self.height = radius
		self.origin = (lon, lat)
		query = (
			"[out:xml][bbox:%f,%f,%f,%f];"
			"(way[\"highway\"~\"motorway|trunk|primary\"];);"
			"out geom;"
		) % (lat - radius, lon - radius, lat + radius, lon + radius)
		try:
			r = requests.get(
				"https://overpass-api.de/api/interpreter",
				params={"data": query},
				timeout=30,
			)
			r.raise_for_status()
		except Exception as e:
			print("[Overpass error: %s]" % e)
			return
		try:
			root = ET.fromstring(r.text.encode("UTF-8"))
			for way in root.iter('way'):
				pts = []
				for nd in way.findall('nd'):
					lat, lon = nd.get('lat'), nd.get('lon')
					if lat and lon:
						pts.append((float(lat), float(lon)))
				if len(pts) >= 2:
					self.ways.append(pts)
		except Exception as e:
			print("[Overpass data error: %s]" % e)

	def fetch_by_coordinate(self, coords, range):
		lat, lon = coords[0], coords[1]
		return self.fetch_area((
				lon - range,
				lat - range,
				lon + range,
				lat + range
		))

	def transpose_ways(self, dimensions, offset, flip_y=True):
		width = dimensions[0]
		height = dimensions[1]
		w_coef = width / self.width / 2
		h_coef = height / self.height / 2
		transways = []
		for way in self.ways:
			transway = []
			for waypoint in way:
				lat = waypoint[1] - self.origin[0]
				lng = waypoint[0] - self.origin[1]
				wp = [
						(lat * w_coef) + offset[0],
						(lng * h_coef) + offset[1]
				]
				if flip_y:
					wp[1] *= -1
					wp[1] += offset[1] * 2
				transway.append(wp)
			transways.append(transway)
		return transways

	def transpose_tags(self, dimensions, offset, flip_y=True):
		width = dimensions[0]
		height = dimensions[1]
		w_coef = width / self.width / 2
		h_coef = height / self.height / 2
		transtags = []
		for tag in self.tags:
			lat = tag[1] - self.origin[0]
			lng = tag[0] - self.origin[1]
			wp = [
							tag[2],
							(lat * w_coef) + offset[0],
							(lng * h_coef) + offset[1],
							tag[3]
			]
			if flip_y:
				wp[2] *= -1
				wp[2] += offset[1] * 2
			transtags.append(wp)
		return transtags



class SoundSpectrum: 
	""" 
	Obtain the spectrum in a time interval from a sound file. 
	""" 

	left = None 
	right = None 
	
	def __init__(self, filename, force_mono=False): 
		""" 
		Create a new SoundSpectrum instance given the filename of 
		a sound file pygame can read. If the sound is stereo, two 
		spectra are available. Optionally mono can be forced. 
		""" 
		# Get playback frequency 
		nu_play, format, stereo = pygame.mixer.get_init() 
		self.nu_play = 1./nu_play 
		self.format = format 
		self.stereo = stereo 

		# Load sound and convert to array(s) 
		sound = pygame.mixer.Sound(filename)
		a = pygame.sndarray.array(sound) 
		a = numpy.array(a) 
		if stereo: 
			if force_mono: 
				self.stereo = 0 
				self.left = (a[:,0] + a[:,1])*0.5 
			else: 
				self.left = a[:,0] 
				self.right = a[:,1] 
		else: 
			self.left = a 

	def get(self, data, start, stop): 
		""" 
		Return spectrum of given data, between start and stop 
		time in seconds. 
		""" 
		duration = stop-start 
		# Filter data 
		start = int(start/self.nu_play) 
		stop = int(stop/self.nu_play) 
		N = stop - start 
		data = data[start:stop] 

		# Get frequencies 
		frequency = numpy.arange(N/2)/duration 

		# Calculate spectrum 
		spectrum = fft(data)[1:1+N/2] 
		power = (spectrum).real 

		return frequency, power 

	def get_left(self, start, stop): 
		""" 
		Return spectrum of the left stereo channel between 
		start and stop times in seconds. 
		""" 
		return self.get(self.left, start, stop) 

	def get_right(self, start, stop): 
		""" 
		Return spectrum of the left stereo channel between 
		start and stop times in seconds. 
		""" 
		return self.get(self.right, start, stop) 

	def get_mono(self, start, stop): 
		""" 
		Return mono spectrum between start and stop times in seconds. 
		Note: this only works if sound was loaded as mono or mono 
		was forced. 
		""" 
		return self.get(self.left, start, stop) 

class LogSpectrum(SoundSpectrum): 
	""" 
	A SoundSpectrum where the spectrum is divided into 
	logarithmic bins and the logarithm of the power is 
	returned. 
	""" 

	def __init__(self, filename, force_mono=False, bins=20, start=1e2, stop=1e4): 
		""" 
		Create a new LogSpectrum instance given the filename of 
		a sound file pygame can read. If the sound is stereo, two 
		spectra are available. Optionally mono can be forced. 
		The number of spectral bins as well as the frequency range 
		can be specified. 
		""" 
		SoundSpectrum.__init__(self, filename, force_mono=force_mono) 
		start = log10(start) 
		stop = log10(stop) 
		step = (stop - start)/bins 
		self.bins = 10**numpy.arange(start, stop+step, step) 

	def get(self, data, start, stop): 
		""" 
		Return spectrum of given data, between start and stop 
		time in seconds. Spectrum is given as the log of the 
		power in logatithmically equally sized bins. 
		""" 
		f, p = SoundSpectrum.get(self, data, start, stop) 
		bins = self.bins 
		length = len(bins) 
		result = numpy.zeros(length) 
		ind = numpy.searchsorted(bins, f) 
		for i,j in zip(ind, p): 
			if i<length: 
				result[i] += j 
		return bins, result 