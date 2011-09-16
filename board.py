#!/usr/bin/python
#from pdb import set_trace
from debug import debug_trace

EMPTY = 0
BLACK = 1
WHITE = 2
WALL = 3

__pos = "ABCDEFGHIJKLMNOPQRS"
__num = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
	12, 13, 14, 15, 16, 17, 18, 19]

__pdict = dict(zip(__pos, __num))
__ndict = dict(zip(__num, __pos))

def valid_color(color):
	return color == BLACK or color == WHITE

def str2color(s):
	if s == "B":
		return BLACK
	elif s == "W":
		return WHITE
	else:
		return 0

def enemy(color):
	if color == BLACK:
		return WHITE
	elif color == WHITE:
		return BLACK
	else:
		raise IndexError

def pos2xy(pos):
	""" convert pos like 'ab' to x, y"""
	x = __pdict[pos.upper()[0]]
	y = __pdict[pos.upper()[1]]
	return x, y

def xy2pos(x, y):
	"""convert (x,y) to 'ab' like pos"""
	return __ndict[x] + __ndict[y]

def pos2id(pos):
	"""obsolete: convert pos like 'ab' to 1D array id"""
	x = __pdict[pos.upper()[0]]
	y = __pdict[pos.upper()[1]]
	return xy2id(x, y)

def xy2id(x, y):
	"""obsolete: convert (x,y) to 1D array id"""
	return x * 19 + y

def pos2xy(pos):
	x = __pdict[pos.upper()[0]]
	y = __pdict[pos.upper()[1]]
	return (x, y)
	
def id2xy(_id):
	"""obsolete: convert id to (x,y)"""
	return divmod(_id, 19)

def id2pos(_id):
	"""obsolete: convet id to 'ab' like pos """
	x, y = divmod(_id, 19)
	return __ndict[x] + __ndict[y]

class BoardError(Exception):
	pass

class Board(object):
	def __init__(self, size = 19):
		self.size = size
		self.points = (size+2)*(size+2)
		self.data = []
		self.data.append([WALL] * 21)
		for i in range(1, 20):
			self.data.append([EMPTY] * 21)
		self.data.append([WALL] * 21)
		self.clear()

	def clear(self):
		for i in range(21):
			self.data[i][0] = WALL
			self.data[i][20] = WALL

	def valid_id(self, _id):
		#FIXME obsolete
		return True

	def valid_xy(self, x, y):
		"This only verifies the valid x, y for a stone"
		if x > 0 and x <= self.size and y > 0 and y <= self.size:
			return True
		else:
			return False

	def place_stone_pos(self, pos, color):
		if pos == "": # Allow pass
			print "PASS"
		else:
			x, y = pos2xy(pos)
			self.place_stone_xy(x, y, color)

	def place_stone_id(self, _id, color):
		"obsolete"
		if not valid_color(color) or not self.valid_id(_id):
			raise BoardError("Invalid color.")

		if self.data[_id] != EMPTY:
			print "Warning: remove when removing stone is implemented"
			#raise BoardError

		self.data[_id] = color

	def place_stone_xy(self, x, y, color):
		if not self.valid_xy(x, y):
			raise BoardError("Invalid position.")
		if not valid_color(color):
			raise BoardError("Invalid color.")

		self.data[x][y] = color

	def has_liberty(self, x, y):
		if (self.data[x-1][y] == EMPTY or
			self.data[x+1][y] == EMPTY or
			self.data[x][y-1] == EMPTY or
			self.data[x][y+1] == EMPTY):
			return True
		else:
			return False

	def is_alive(self, x, y, color, cluster):
		""" Decide if a cluster of stones is alive. x, y is a seed inside the cluster.
			cluster will hold all the stones that are NOT alive when this method finishes.
		"""
		if self.data[x][y] != color:
			return False

		if self.has_liberty(x, y):
			return True

		if (x, y) in cluster:
			return False

		cluster.append((x, y))

		# Check neighbours
		if self.is_alive(x-1, y, color, cluster):
			return True
		if self.is_alive(x+1, y, color, cluster):
			return True
		if self.is_alive(x, y-1, color, cluster):
			return True
		if self.is_alive(x, y+1, color, cluster):
			return True

		return False

	def remove_stones(self, cluster):
		print "remove_stones()", cluster
		for x, y in cluster:
			self.data[x][y] = EMPTY

	def neighbours_xy(self, x, y):
		"returns a list of positions that's neighbour to (x,y)"
		nb = []
		if self.valid_xy(x-1, y):
			nb.append((x-1, y))
		if self.valid_xy(x+1, y):
			nb.append((x+1, y))
		if self.valid_xy(x, y-1):
			nb.append((x, y-1))
		if self.valid_xy(x, y+1):
			nb.append((x, y+1))

		return nb

	def neighbours_pos(self, pos):
		"handy wrapper of neighbours_xy() that takes in 'ab' like pos"
		x, y = pos2xy(pos)
		return self.neighbours_xy(x, y)

	def play_xy(self, x, y, color):
		"""Play a stone at the position. Update board data when stones are captured.
		Returns the captures stone. """
		print "play_xy(%d,%d,%d)" % (x, y, color)
		#if x == 5 and y == 19:
			#debug_trace()
		if not self.valid_xy(x, y) or not valid_color(color):
			raise BoardError("Invalid stone color.")
		if self.data[x][y] != EMPTY:
			raise BoardError("Position occupied.");

		self.data[x][y] = color

		all_dead = []
		nb = self.neighbours_xy(x, y)
		for nx, ny in nb:
			clust = []
			if (nx, ny) in all_dead:
				continue
			if not self.is_alive(nx, ny, enemy(color), clust ):
				all_dead.extend(clust)

		if len(all_dead) == 0 and not self.is_alive(x, y, color, []):
			self.data[x][y] = EMPTY
			raise BoardError("Suicide not allowed") # Scuicide not allowed

		if len(all_dead) > 0:
			self.remove_stones(all_dead)

		return all_dead

	def play_pos(self, pos, color):
		x, y = pos2xy(pos)
		return self.play_xy(x, y, color)