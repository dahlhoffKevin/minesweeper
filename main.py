"""
Importieren der benötigten Bibiliotheken
"""
from dataclasses import dataclass
from tkinter import *
from tkinter import messagebox
from time import sleep
import pygame
import os
import sys
import random

"""
Verwaltet die Einstellungen des Spiels
"""
class Settings:
	"""
	Einstellungen für das Spiel selbst
	"""
	dimensions = 495
	grid = 9
	space = dimensions // grid # 55
	title = 'Minesweeper - Dahlhoff'

	mines = 10
	flagged_mines = 0
	field = []

	selected_cell = []

	fps = 60

	"""
	Speichert die Position einzelner Zellen um eine Zelle herum.
	"""
	fields_arround = [(-1, -1), (-1, 0), (-1, -1),
					  (0, -1), (0, 1),
					  (1, -1), (1, 0), (1, 1)]

	"""
	Pfade und Datein der Bilder des Spiels
	"""
	file_path = os.path.dirname(os.path.abspath(__file__))
	images = os.path.join(file_path, "images")

	screen = pygame.display.set_mode((dimensions, dimensions))
	
	cell_normal = pygame.image.load(os.path.join(images, 'cell_normal.png')).convert_alpha()
	cell_normal = pygame.transform.scale(cell_normal, (space, space))

	mine = pygame.image.load(os.path.join(images, 'cell_bomb.png')).convert_alpha()
	mine = pygame.transform.scale(mine, (space, space))

	cell_marked = pygame.image.load(os.path.join(images, 'cell_marked.png')).convert_alpha()
	cell_marked = pygame.transform.scale(cell_marked, (space, space))

	"""
	Die For-Schleife fügt die Bilder mit der Aufschrift 1-8 einer Liste hinzu
	"""
	for n in range(9):
		selected_cell.append(pygame.transform.scale(pygame.image.load(os.path.join(images, f'cell_sel_{n}.png')).convert_alpha(), (space, space)))


"""
Zellenklasse
"""
"""
'@dataclass' sorgt dafür, dass eine __init__() Methode erzeugt wird,
die die Klassenvariablen als Argumente enthält.
"""
@dataclass
class Cell():
	"""
	Eigenschaften der Zelle
	"""
	row : int
	column : int
	mine : bool = False
	selected : bool = False
	marked : bool = False
	mines_arround : int = 0
	
	"""
	Zeichnet das entsprechende Bild auf den Bildschirm
	Sobald eine Zelle angeklickt wird, wird geprüft ob diese eine Bombe ist,

	Sollte die Zelle nicht angeklickt werden, wird geprüft, ob diese Markierte wurde oder nicht
	"""
	def update(self):
		pos = (self.column * Settings.space, self.row * Settings.space)
		if self.selected:
			if self.mine:
				Settings.screen.blit(Settings.mine, pos)
			else:
				Settings.screen.blit(Settings.selected_cell[self.mines_arround], pos)
		else:
			if self.marked:
				Settings.screen.blit(Settings.cell_marked, pos)
			else:
				Settings.screen.blit(Settings.cell_normal, pos)

	"""
	Diese Funktion berechnet für jede einzelne Zelle, wie viele Minen sich in ihrem Umfeld befinden.
	Dazu wird auch beachtet, ob sich die Zelle in einer der vier Ecken des Spiels befindet.
	"""
	def calc_mines_arround(self):
		for pos in Settings.fields_arround:
			new_row = self.row + pos[0]
			new_column = self.column + pos[1]
			if new_row >= 0 and new_row < Settings.grid and new_column >= 0 and new_column < Settings.grid:
				if Settings.field[new_row * Settings.grid + new_column].mine:
					self.mines_arround += 1


"""
Diese Klasse baut das Spielfeld auf
"""
class Playground_builder():
	"""
	Baut das Grundgerüst auf
	"""
	def area_builder(self):
		for n in range(Settings.grid * Settings.grid):
			Settings.field.append(Cell(n // Settings.grid, n % Settings.grid))

	"""
	Positioniert die Bomben auf dem Spielfeld
	Es werden maximal 10 Bomben platziert
	"""
	def mine_placer(self):
		while Settings.mines > 0:
			x = random.randrange(Settings.grid * Settings.grid)
			if not Settings.field[x].mine:
				Settings.field[x].mine = True
				Settings.mines -= 1

		for ob in Settings.field:
			ob.calc_mines_arround()


class Game(object):
	def __init__(self):
		self.screen = Settings.screen
		pygame.display.set_mode([Settings.dimensions, Settings.dimensions])
		pygame.display.set_caption(Settings.title)

		self.clock = pygame.time.Clock()
		self.done = False

		self.playground_builder = Playground_builder()
		self.playground_builder.area_builder()
		self.playground_builder.mine_placer()

	"""
	floodFill ist ein bekannter Algorithmus, welcher in diesem Fall
	alle angeklickten Zellen überprüft. Sollte es sich um eine leere Zelle handeln,
	prüft der Algorithmus, ob die Zellen drumherum ebenfalls leer sind. Sobald dies
	der Fall ist, wird die angeklickte Zelle und alle leeren angrenzenden Felder
	aufgedeckt.

	Die Methode wird für jedes angeklicktes Feld aufgerufen.
	"""
	def floodFill(self, row, column):
		for pos in Settings.fields_arround:
			new_row = row + pos[0] # Speichert die x Koordinate
			new_column = column + pos[1] # Speichert die y Koordinate
			
			# Überprüft, ob die neuen Positionen außerhalb des Spielfels liegen
			if new_row >= 0 and new_row < Settings.grid and new_column >= 0 and new_column < Settings.grid:

				# Speichert die neue Zelle
				cell = Settings.field[new_row * Settings.grid + new_column]

				"""
				Sobald die neue Zelle eine leere Zelle ist
				und nicht bereits angeklickt wurde, wird diese aufgedeckt und der
				Algorithmus startet von neu.

				Sollte die neue Zelle keine leere Zelle sein oder bereits angeklickt worden sein,
				wird diese aufgedeckt und der Algorithmus stoppt.
				"""
				if cell.mines_arround == 0 and not cell.selected:
					cell.selected = True
					self.floodFill(new_row, new_column)
				else:
					cell.selected = True

	"""
	Diese Methode beendet das Spiel oder startet es neu
	"""
	def play_again(self, again):
		if again == 'yes':
			os.execv(sys.executable, ['python'] + sys.argv)
			sys.exit()
		else:
			self.done = True

	"""
	Diese Methode überprüft eine angeklickte Zelle.
	Ist die Zelle beispielsweise eine Bombe, ist das Spiel verloren

	Ebenfalls ist es möglich, Zellen mit einer Flagge zu versehen
	"""
	def check_cell(self):
		mouse_x, mouse_y = pygame.mouse.get_pos()
		column = mouse_x // Settings.space # Berechnet die Reihe der Zelle in relation zu der x Position der Maus
		row = mouse_y // Settings.space # Berechnet die Reihe der Zelle in relation zu der x Position der Maus
		x = row * Settings.grid + column # Speicher die entsprechende Position der Zelle
		cell = Settings.field[x] # Speichert die entsprechende Zelle bei der bereits in 'x' festgelegten Position

		"""
		Sobald die rechte Maustaste gegrückt wird,
		wird die entsprechende Zelle mit einer Flagge versehen.
		Sollte die Zelle bereits mit einer Flagge versehen worden sein, wird
		die Flagge entfernt.

		Gleichzeitig wird geprüft, ob vielleicht bereits alle Bomben markiert wurden,
		ist das der Fall, ist das Spiel gewonnen.
		"""
		if pygame.mouse.get_pressed()[2]:
			cell.marked = not cell.marked
			if cell.marked == False:
				if cell.mine:
					Settings.flagged_mines += 1
					if Settings.flagged_mines == Settings.mines:
						main = Tk()
						main.withdraw()
						question = messagebox.askquestion('Gewonnen!', 'Möchtest du es nochmal versuchen?', icon='question')
						self.play_again(question)
			else:
				Settings.flagged_mines -= 1

		"""
		An dieser Stelle wird überprüft, ob die angeklickte Zelle ein Bombenfeld ist,
		ist das der Fall, ist das Spiel verloren.

		Zugleich wird überprüft, ob die Zelle eine leere Zelle ist,
		ist das der Fall, wird der FloodFill Algorithmus dazu verwendet,
		um alle anliegenden leeren Zellen aufzudecken.
		"""
		if pygame.mouse.get_pressed()[0]:
			cell.selected = True
			if cell.mines_arround == 0 and not cell.mine:
				self.floodFill(row, column)
			if cell.mine:
				# for ob in Settings.field:
				# 	ob.selected = True
				main = Tk()
				main.withdraw()
				question = messagebox.askquestion('Verloren!', 'Möchtest du es nochmal versuchen?', icon='question')
				self.play_again(question)

	"""
	Hauptspielschleife
	"""
	def run(self):
		while self.done is not True:
			self.clock.tick(Settings.fps)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.done = True

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_q:
						sys.exit()

				if event.type == pygame.MOUSEBUTTONDOWN:
					self.check_cell()

			self.update()
			pygame.display.flip()

	def update(self):
		for ob in Settings.field:
			ob.update()

if __name__ == '__main__':
	game = Game()
	game.run()
	pygame.quit()