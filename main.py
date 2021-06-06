"""
Importieren der benötigten Bibiliotheken
"""
from dataclasses import dataclass
from tkinter import *
from tkinter import messagebox
from time import sleep
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
from configparser import ConfigParser

import pygame
import os
import sys
import random

pygame.init()

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
	mines_on_field = 10
	flagged_mines = 0
	field = []

	selected_cell = []

	fps = 60

	config = ConfigParser()
	config.read('config.ini')
	menu_ui = config['DEFAULT']['menu_ui']

	start_game = False

	"""
	Speichert die Position einzelner Zellen um eine Zelle herum.
	"""
	fields_arround = [(-1, -1), (-1, 0), (-1, 1),
					  (0, -1), (0, 1),
					  (1, -1), (1, 0), (1, 1)]

	cell_normal = None
	mine = None
	cell_marked = None

	def load_images():
		"""
		Pfade und Datein der Bilder des Spiels
		"""
		file_path = os.path.dirname(os.path.abspath(__file__))
		images = os.path.join(file_path, "images")

		# screen = pygame.display.set_mode((dimensions, dimensions))
		
		Settings.cell_normal = pygame.image.load(os.path.join(images, 'cell_normal.png')).convert_alpha()
		Settings.cell_normal = pygame.transform.scale(Settings.cell_normal, (Settings.space, Settings.space))

		Settings.mine = pygame.image.load(os.path.join(images, 'cell_bomb.png')).convert_alpha()
		Settings.mine = pygame.transform.scale(Settings.mine, (Settings.space, Settings.space))

		Settings.cell_marked = pygame.image.load(os.path.join(images, 'cell_marked.png')).convert_alpha()
		Settings.cell_marked = pygame.transform.scale(Settings.cell_marked, (Settings.space, Settings.space))

		"""
		Die For-Schleife fügt die Bilder mit der Aufschrift 1-8 einer Liste hinzu
		"""
		for n in range(9):
			Settings.selected_cell.append(pygame.transform.scale(pygame.image.load(os.path.join(images, f'cell_sel_{n}.png')).convert_alpha(), (Settings.space, Settings.space)))

def valid_cell(x, y):
	return y > -1 and y < Settings.grid and x > -1 and x < Settings.grid

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
				game.screen.blit(Settings.mine, pos)
			else:
				game.screen.blit(Settings.selected_cell[self.mines_arround], pos)
		else:
			if self.marked:
				game.screen.blit(Settings.cell_marked, pos)
			else:
				game.screen.blit(Settings.cell_normal, pos)

	"""
	Diese Funktion berechnet für jede einzelne Zelle, wie viele Minen sich in ihrem Umfeld befinden.
	Dazu wird auch beachtet, ob sich die Zelle in einer der vier Ecken des Spiels befindet.
	"""
	def calc_mines_arround(self):
		for pos in Settings.fields_arround:
			new_row = self.row + pos[0] # Speichert die X Position einer umliegenden Zelle
			new_column = self.column + pos[1] # Speichert die Y Position einer umliegenden Zelle
				
			"""
			Prüft, ob die neu ausgewählt Zelle eine Bombe ist und ob die Zelle im Spielfeld liegt, ist das der Fall,
			wird der Wert 'mines_arround' für die entsprechende Zelle erhöht.
			"""
			if valid_cell(new_row, new_column) and Settings.field[new_row * Settings.grid + new_column].mine:
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
	an einer zufällig bestimmten Position.
	"""
	def mine_placer(self):
		while Settings.mines > 0:
			x = random.randrange(Settings.grid * Settings.grid)
			if not Settings.field[x].mine:
				Settings.field[x].mine = True
				Settings.mines -= 1

class Game(QtWidgets.QMainWindow):
	def __init__(self):
		super(Game, self).__init__()
		self.screen = pygame.display.set_mode((Settings.dimensions, Settings.dimensions))
		pygame.display.set_mode([Settings.dimensions, Settings.dimensions])
		pygame.display.set_caption(Settings.title)
		Settings.load_images()

		self.msg = QMessageBox

		self.clock = pygame.time.Clock()
		self.done = False

		self.playground_builder = Playground_builder()
		self.playground_builder.area_builder()
		self.playground_builder.mine_placer()

		self.hit = False

		for ob in Settings.field:
			ob.calc_mines_arround()

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
			if not cell.marked:
				if cell.mine:
					Settings.flagged_mines += 1
					cell.marked = True
					if Settings.flagged_mines >= Settings.mines_on_field:
						choice = QMessageBox.question(self, 'Gewonnen!', "Möchtest du es nochmal versuchen?", QMessageBox.Yes | QMessageBox.No)
						if choice == QMessageBox.Yes:
							self.play_again('yes')
						else:
							sys.exit()
						self.msg.show()
					
			else:
				Settings.flagged_mines -= 1
				cell.marked = not cell.marked
				
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

			if cell.mine == True:
				for ob in Settings.field:
					if ob.mine == True:
						self.hit = True

	def show_message(self, head, text):
		main = Tk()
		main.withdraw()
		question = messagebox.askquestion(head, text, icon='question')
		return question

	"""
	Hauptspielschleife
	"""
	def run(self):
		while self.done is not True:
			self.clock.tick(Settings.fps)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.done = True

				"""
				Beendet das Spiel, sobald 'q' gedrückt wurde
				"""
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_q:
						sys.exit()
				
				"""
				Jede Zelle wird bei jedem Mausklick überprüft
				"""
				if event.type == pygame.MOUSEBUTTONDOWN:
					self.check_cell()

			"""
			Sobald das Spiel verloren ist,
			wird dem Spieler die Frage gestellt,
			ob er das Spiel noch einmal spielen möchte.
			"""
			if self.hit:
				choice = QMessageBox.question(self, 'Verloren!', "Möchtest du es nochmal versuchen?", QMessageBox.Yes | QMessageBox.No)
				if choice == QMessageBox.Yes:
					self.play_again('yes')
				else:
					sys.exit()
				self.msg.show()

			self.update()
			pygame.display.flip()
	
	def update(self):
		for ob in Settings.field:
			ob.update()

"""
Klasse für das Startmenu
"""
class Menu_UI(QtWidgets.QMainWindow):
	def __init__(self):
		"""
		Lädt die UI des Menus
		"""
		super(Menu_UI, self).__init__()
		uic.loadUi(Settings.menu_ui, self)

		self.msg = QMessageBox()

		self.button_play.clicked.connect(self.play)

	"""
	Lädt die Einstellungen für die jeweilige Schwierigkeit
	"""
	def play(self):
		difficulty = self.lineedit_diff.text()

		if difficulty == '1':
			Settings.dimensions = 495
			Settings.grid = 9
			Settings.mines = 10
			Settings.mines_on_field = 10
			Settings.space = 495 // 9
			self.close()
			Settings.start_game = True

		elif difficulty == '2':
			Settings.dimensions = 880
			Settings.grid = 16
			Settings.mines = 40
			Settings.mines_on_field = 40
			Settings.space = 880 // 16
			self.close()
			Settings.start_game = True

		elif difficulty == '3':
			Settings.dimensions = 880
			Settings.grid = 16
			Settings.mines = 40
			Settings.mines_on_field = 40
			Settings.space = 880 // 16
			self.close()
			Settings.start_game = True

		else:
			"""
			Wird ausgeführt, wenn eine ungültige Schwierigkeit eingetragen werden sollte
			"""
			self.msg.setIcon(QMessageBox.Critical)
			self.msg.setText('Keine gültige Schwierigkeit')
			self.msg.setWindowTitle('Invalid difficulty')
			self.msg.show()


if __name__ == '__main__':
	"""
	Schleife wird abgebrochen,
	sobald eine Schwierigkeit gewählt wurde
	"""
	while True:
		if Settings.start_game:
			game = Game()
			game.run()
			break
		app = QtWidgets.QApplication(sys.argv)
		menuui = Menu_UI()
		menuui.show()

		app.exec_()
		pygame.quit()
