from PyQt5.QtCore import pyqtSignal, pyqtSlot, QDir, QSize, Qt
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QListWidget, QMainWindow, QMessageBox, QPushButton, QSlider, QSizePolicy, QStyle, QVBoxLayout, QWidget
import json
import os
from ImageDisplay import ImageDisplay
from omen_db_connector import OmenDBConnector

formats = ['mp3', 'wav']

mode = 'Release'
if True:
	mode = 'Debug'

def log(data):
	global mode
	if mode == 'Debug':
		print(data)

class MainWindow(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.file_root = self.loadFileDir()
		while self.file_root == None:
			self.promptForMusicFiles()
		self.initDB()
		self.initUI()
		self.scanDirectory()
		self.updateDB()
		self.loadFiles()
		self.art_disp.setImage('{}/4x4=12/art.png'.format(self.file_root))

	def browseFileRoot(self):
		folder = QFileDialog.getExistingDirectory(self, 'Select Music Folder', QDir.homePath())
		if folder == '':
			return
		self.file_root = folder.replace('\\', '/')
		if os.path.isfile('data.json'):
			with open('data.json', 'r') as file:
				data = json.load(file)
			data['file_root'] = self.file_root
			with open('data.json', 'w') as file:
				json.dump(data, file)
		else:
			with open('data.json', 'w') as file:
				json.dump({'file_root': self.file_root}, file)

	def initDB(self):
		self.db = OmenDBConnector()
		self.db.connect()
		self.db.drop()

	def initUI(self):
		self.track_list = OmenTrackList()
		self.art_disp = OmenArtworkDisplay()
		self.sidebar = OmenSidebar()
		self.controls = OmenControlPanel()
		self.progress = OmenProgressBar()

		self.sidebar.resizeEventCreated.connect(self.resizeControls)
		self.art_disp.setMaximumWidth(320)

		sidebar_layout = QVBoxLayout()
		sidebar_layout.addWidget(self.sidebar, 1)
		sidebar_layout.addWidget(self.art_disp, 0)

		top_layout = QHBoxLayout()
		top_layout.addLayout(sidebar_layout, 0)
		top_layout.addWidget(self.track_list, 1)

		bottom_layout = QHBoxLayout()
		bottom_layout.addWidget(self.controls, 1)
		bottom_layout.addWidget(self.progress, 1)

		layout = QVBoxLayout()
		layout.addLayout(top_layout, 1)
		layout.addLayout(bottom_layout, 0)

		self.central_widget = QWidget()
		self.central_widget.setLayout(layout)

		self.setCentralWidget(self.central_widget)

		self.setMinimumSize(1440, 810)

	def loadFileDir(self):
		if not os.path.isfile('data.json'):
			return None
		with open('data.json', 'r') as file:
			data = json.load(file)
		return data['file_root'] if 'file_root' in data.keys() else None

	def loadFiles(self):
		for file in self.filenames:
			self.track_list.addItem(file)

	def promptForMusicFiles(self):
		alert = QMessageBox()
		alert.setText('This looks like a first run, please browse for your music folder so your files can be loaded.')
		alert.setWindowTitle('Set file location.')
		alert.setMinimumSize(300, 100)
		browse_button = QPushButton('Browse...')
		browse_button.clicked.connect(self.browseFileRoot)
		alert.addButton(browse_button, 0)
		alert.exec()
		return

	def resizeControls(self, event):
		self.controls.setMaximumWidth(self.sidebar.width() - 1)
		self.controls.resizeEvent(QResizeEvent(QSize(self.sidebar.width() - 1, self.controls.height()), self.controls.size()))

	def scanDirectory(self):
		self.filenames = []
		dir_list = [x for x in os.listdir(self.file_root) if os.path.isdir('{}/{}'.format(self.file_root, x))]
		file_list = [x for x in os.listdir(self.file_root) \
			if os.path.isfile('{}/{}'.format(self.file_root, x)) and x.split('.')[-1] in formats]
		
		for directory in dir_list:
			for file in os.listdir('{}/{}'.format(self.file_root, directory)):
				self.filenames.append(file)
		self.filenames += file_list

	def updateDB(self):
		#add/update all found files
		for file in self.filenames:
			self.db.insert(file, 'none', 'none')
		#pull the whole list
		result = self.db.exec('SELECT filename FROM filenames')
		#anything not in the found list is removed from db
		for file in result:
			if file[0] not in self.filenames:
				self.db.remove(file[0])

class OmenTrackList(QListWidget):
	def __init__(self, parent=None):
		super().__init__(parent)

class OmenArtworkDisplay(ImageDisplay):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.initUI()

	def initUI(self):
		self.resize(self.width(), self.width())
		self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

	def resizeEvent(self, event):
		size = event.size()
		old_size = event.oldSize()
		size = QSize(size.width(), size.width())
		self.setMinimumHeight(self.width())
		super().resizeEvent(QResizeEvent(size, old_size))

class OmenSidebar(QListWidget):
	resizeEventCreated = pyqtSignal(QResizeEvent)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.initUI()

	def initUI(self):
		self.addItem('Tracks')
		self.addItem('Artists')
		self.addItem('Albums')
		self.addItem('Playlists')
		self.setCurrentRow(0)

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self.resizeEventCreated.emit(event)

class OmenControlPanel(QWidget):
	rewindPressed = pyqtSignal()
	rewindReleased = pyqtSignal()
	playClicked = pyqtSignal()
	forwardPressed = pyqtSignal()
	forwardReleased = pyqtSignal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.playing = False
		self.initUI()

	def initUI(self):
		self.rev_button = QPushButton()
		self.play_button = QPushButton()
		self.fwd_button = QPushButton()

		self.rev_button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaSeekBackward')))
		self.play_button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaPlay')))
		self.fwd_button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaSeekForward')))

		self.rev_button.pressed.connect(lambda: self.rewindPressed.emit())
		self.rev_button.released.connect(lambda: self.rewindReleased.emit())
		self.play_button.clicked.connect(self.onPlayClicked)
		self.fwd_button.pressed.connect(lambda: self.forwardPressed.emit())
		self.fwd_button.released.connect(lambda: self.forwardReleased.emit())

		layout = QHBoxLayout()
		layout.addWidget(self.rev_button)
		layout.addWidget(self.play_button)
		layout.addWidget(self.fwd_button)

		self.setLayout(layout)

	def onPlayClicked(self):
		if self.playing:
			self.play_button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaPlay')))
			self.playing = False
		else:
			self.play_button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_MediaPause')))
			self.playing = True
		self.playClicked.emit()

class OmenProgressBar(QSlider):
	def __init__(self, parent=None):
		super().__init__(Qt.Horizontal, parent)