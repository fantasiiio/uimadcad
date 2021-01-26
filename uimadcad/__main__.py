
if __name__ == '__main__':
	from uimadcad.gui import *

	import sys, os, locale
	from PyQt5.QtCore import Qt, QTimer
	from PyQt5.QtWidgets import QApplication
	# set Qt opengl context sharing to avoid reinitialization of scenes everytime, (this is for pymadcad display)
	QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
	print('start qt ...')
	# setup Qt application
	app = QApplication(sys.argv)
	print('ok')
	app.setApplicationName('madcad')
	app.setApplicationVersion(version)
	app.setApplicationDisplayName('madcad v{}'.format(version))
	
	# set locale settings to default to get correct 'repr' of glm types
	locale.setlocale(locale.LC_NUMERIC, 'C')
	
	# start software
	madcad = Madcad()
	main = MainWindow(madcad)
	
	def startup():
		if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
			madcad.open_file(sys.argv[1])
		madcad.active_sceneview.adjust()
	
	QTimer.singleShot(100, startup)
	main.show()
	sys.exit(app.exec())
