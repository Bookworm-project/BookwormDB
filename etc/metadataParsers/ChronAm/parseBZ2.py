import tarfile
import os
import re

try:
	os.makedirs("../../../files/texts/")
except OSError:
	pass

output=open("../../../files/texts/input.txt","w")

input="downloads/batch_az_manzanita_ver01.tar.bz2"



class tarball(object):
	def __init__(self,filename):
		self.input = tarfile.open(filename)
	def __iter__(self):
		return self
	def next(self):
		info = self.input.next()
		try:
			name = info.name
		except AttributeError:
			raise StopIteration
		if name[-1:-5:-1]=="txt.":
			#ie, the last four characters are '.txt'; skips directories and XML files.
			content = self.input.extractfile(info).read()
			return name + "\t" + re.sub("\n","",content)
		else:
			#if it's not text, recurse through the next line.
			#May break by recursion limit if the file contains less than 1% .txt files.
			return next(self)

extractor = tarball(input)

for file in extractor:
	print file


