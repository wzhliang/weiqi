#!/usr/bin/python

import unittest
from board import *
from sgf import *
from pdb import set_trace
from pprint import pprint

class GameGui(Game):
	def __init__(self, name, _goban):
		Game.__init__(self, name)
		self.goban = _goban
		self.build_tree()

	def navigate(self):
		node = self.root
		while node:
			if node.name == "B" or node.name == "W":
				self.goban.play_pos( node.prop, board.str2color(node.name) ) 
				print "##############################################"
				pprint(self.goban.data)
			try:
				node = node.children[0]
			except IndexError:
				break

	def navigate_back(self):
		node = None
		while True:
			self.forth()
			node = self.where()
			if is_stone(node.name):
				self.goban.play_pos( node.prop, board.str2color(node.name) ) 
				print "##############################################"
				pprint(self.goban.data)
			if not node.has_child():
				break

		while node:
			if is_stone(node.name):
				x, y = pos2xy(node.prop)
				self.goban.remove_stones([(x, y)]) 
				print "##############################################"
				print node.get_comment().decode("euc-cn")
				pprint(self.goban.data)
			node = self.back()



class BoardTest(unittest.TestCase):
	def test_a(self):
		print "\n========= a =============\n"
		pan = Board()
		game = GameGui("sgf/kj.sgf", pan)
		game.navigate()

	def test_b(self):
		print "\n========= b =============\n"
		pan = Board()
		game = GameGui("sgf/kj.sgf", pan)
		game.navigate_back()

	def test_c(self):
		print "\n========= c =============\n"
		pan = Board()
		game = GameGui("sgf/branch.sgf", pan)
		game.navigate()

	def test_d(self):
		print "\n========= d =============\n"
		pan = Board()
		game = GameGui("sgf/branch.sgf", pan)
		for i in range(4):
			game.forth()
		self.assertEqual(game.where().num_child(), 2)
		game.forth()
		self.assertEqual(game.where().prop, "nc")
		game.branch_down()
		self.assertEqual(game.where().prop, "nd")
		game.branch_up()
		self.assertEqual(game.where().prop, "nc")

	def test_e(self):
		print "\n========= e =============\n"
		pan = Board()
		game = GameGui("sgf/bug.sgf", pan)
		game.navigate()
		pprint(pan.data)

	def test_f(self):
		print "\n========= f =============\n"
		pan = Board()
		game = GameGui("sgf/yijian-ttimm.sgf", pan)
		meta = game.sgf.meta
		self.assertEqual(meta["PB"], "ttimm")
		self.assertEqual(meta["PW"], "yijian")
		self.assertEqual(meta["BR"], "1k")
		self.assertEqual(meta["WR"], "1k")
		self.assertEqual(meta["RE"], "W+10.50")

unittest.main()
