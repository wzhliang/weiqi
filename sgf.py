from pyparsing import (Word, Literal, QuotedString, OneOrMore,
		srange, Forward, ZeroOrMore, Group)
from pprint import pprint
# from pdb import set_trace
import board
import util

_debug_ = False

# BNF from red-bean
#
#  Collection = GameTree { GameTree }
#  GameTree   = "(" Sequence { GameTree } ")"
#  Sequence   = Node { Node }
#  Node       = ";" { Property }
#  Property   = PropIdent PropValue { PropValue }
#  PropIdent  = UcLetter { UcLetter }
#  PropValue  = "[" CValueType "]"
#  CValueType = (ValueType | Compose)
#  ValueType  = (None | Number | Real | Double | Color | SimpleText |
# _	            Text | Point  | Move | Stone)


class Node(object):
	"""this class assumes that the primary property is the first one in the string.
		So files like ;C[haha]B[ab] will not work. """
	def __init__(self, name=""):
		self.name = name
		self.prop = ""
		self.children = []
		self.parent = None
		self.prev_br = None
		self.next_br = None
		self.extra = {}  # extra properties, including comment

	def set_name(self, name):
		self.name = name

	def set_property(self, prop):
		self.prop = prop

	def add_extra(self, name, value):
		self.extra[name] = value

	def get_comment(self):
		try:
			return self.extra["C"]
		except KeyError:
			return ""

	def has_comment(self):
		return "C" in self.extra

	def add_child(self, child):
		if self.num_child() > 0:
			self.children[-1].next_br = child
			child.prev_br = self.children[-1]
		self.children.append(child)
		child.parent = self

	def num_child(self):
		return len(self.children)

	def has_child(self):
		return len(self.children) > 0

	def presentable(self):
		"""a presentable node is something with
			- stones
			- move
			- comment
			- or marks"""
		if util.is_stone(self.name) or util.is_move(self.name):
			return True
		for e in self.extra:
			if util.is_extra(e):
				return True
		return False

	def is_root(self):
		return self.name == "_root_"

	def __str__(self):
		return "%s[%s]" % (self.name, self.prop)


class SGFError(Exception):
	pass


class SGFNoMoreNode(SGFError):
	pass


class SGF(object):
	def __init__(self, filename):
		# BNF
		start = Literal(";")
		text = QuotedString(quoteChar="[",
				escChar="\\",
				multiline=True,
				unquoteResults=True,
				endQuoteChar="]")
		prop_id = Word(srange("[A-Za-z]"), min=1, max=10)
		prop = prop_id + Group(OneOrMore(text))
		node = ZeroOrMore(start) + OneOrMore(prop)
		sequence = OneOrMore(node)
		branch = Forward()
		branch << "(" + sequence + ZeroOrMore(branch) + ")"
		self.game = OneOrMore(branch)

		self.sgf_content = filename
		self.moves = None
		self.__parse()
		self.current = 0

	def next_token(self):
		tok = self.moves[self.current]
		self.current += 1
		if _debug_:
			print "SGF: ", tok
		return tok

	def __parse(self):
		self.moves = self.game.parseString(self.sgf_content)

	def show(self):
		print "All moves in %s" % self.sgf_content
		pprint(self.moves)


class Game(object):
	def __init__(self, sgf_content):
		self.sgf = SGF(sgf_content)
		self.root = Node('_root_')
		self.current = self.root
		self.info = {}
		self.stack = []

	def on_move(self, propid):
		self.current.set_name(propid)
		self.current.set_property(self.sgf.next_token()[0])

	def on_stone(self, propid):
		self.current.set_name(propid)
		self.current.set_property(self.sgf.next_token().asList())

	def on_extra(self, propid):
		tok = self.sgf.next_token()
		if propid == "C":
			self.current.add_extra(propid, tok[0])
		else:
			self.current.add_extra(propid, tok.asList())

	def on_meta(self, propid):
		self.info[propid] = self.sgf.next_token()[0]

	def on_branch(self, br):
		if br == "(":
			self.stack.append(self.current)
		else:
			self.current = self.stack.pop()

	def on_node(self, n):
		"n is alwasy ';'"
		node = Node()
		self.current.add_child(node)
		self.current = node

	def build_tree(self):
		while True:
			try:
				current = self.sgf.next_token()

				if not type(current) is str:
					continue
				if util.is_move(current):
					self.on_move(current)
				elif util.is_stone(current):
					self.on_stone(current)
				elif util.is_meta(current):
					self.on_meta(current)
				elif util.is_extra(current):
					self.on_extra(current)
				elif util.is_branch(current):
					self.on_branch(current)
				elif util.is_node(current):
					self.on_node(current)
				else:
					pass
			except IndexError:
				break
		self.reset()

	def reset(self):
		self.current = self.root

	def forth(self, branch=0):
		try:
			self.current = self.current.children[branch]
			while not self.current.presentable():
				self.current = self.current.children[branch]
		except IndexError:
			raise SGFNoMoreNode

	def back(self):
		if self.current.is_root():
			raise SGFNoMoreNode
		self.current = self.current.parent

	def where(self):
		return self.current

	def branch_up(self):
		"Try move up to the previous branch"
		remove = []
		node = self.current
		while node:
			remove.append(node.prop)
			if node.prev_br:
				self.current = node.prev_br
				break
			node = node.parent
		return remove if node else []

	def branch_down(self):
		"Try move up to the previous branch"
		remove = []
		node = self.current
		while node:
			remove.append(node.prop)
			if node.next_br:
				self.current = node.next_br
				break
			node = node.parent
		return remove if node else []

	def __getattr__(self, name):
		"Gurantteed no exception"
		return self.info[name] if name in self.info else ""


class GameGui(Game):
	def __init__(self, name, _goban):
		Game.__init__(self, name)
		self.goban = _goban

	def navigate(self):
		node = self.root
		while node.has_child():
			if node.name == "B" or node.name == "W":
				self.goban.place_stone_pos(
					node.prop, board.str2color(node.name))
			node = node.children[0]

# EoF
