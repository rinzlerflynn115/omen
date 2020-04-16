import sqlite3

class OmenDBConnector:
	def __init__(self):
		self.db = 'library.db'
		self.table = 'filenames'
		self.connection = None

	def connect(self):
		if self.connection != None:
			self.connection.close()

		self.connection = sqlite3.connect(self.db)

	def close(self):
		if self.connection == None:
			return

		self.connection.close()

	def insert(self, filename, title, artist):
		if self.connection == None:
			return

		sql = 'INSERT INTO {} VALUES (\'{}\', \'{}\', \'{}\')'.format(self.table, filename, title, artist)
		cursor = self.connection.cursor()
		return cursor.execute(sql)

	def remove(self, filename):
		if self.connection == None:
			return
		print(filename)
		sql = 'DELETE FROM {} WHERE FILENAME = {}'.format(self.table, filename)
		cursor = self.connection.cursor()
		return cursor.execute(sql)

	def get(self, filename):
		if self.connection == None:
			return

		sql = 'SELECT * FROM {} WHERE FILENAME = {}'.format(self.table, filename)
		cursor = self.connection.cursor()
		return cursor.execute(sql)

	def exec(self, sql):
		if self.connection == None:
			return

		cursor = self.connection.cursor()
		return cursor.execute(sql)

	def drop(self):
		if self.connection == None:
			return

		sql = 'DELETE FROM {}'.format(self.table)
		cursor = self.connection.cursor()
		return cursor.execute(sql)