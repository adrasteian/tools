#! /usr/bin/env python

#===================================================================================
#
#	Copyright (c) 2019 Simon Butler
#
#	Permission is hereby granted, free of charge, to any person obtaining a copy
#	of this software and associated documentation files (the "Software"), to deal
#	in the Software without restriction, including without limitation the rights
#	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#	copies of the Software, and to permit persons to whom the Software is
#	furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in all
#	copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#	SOFTWARE.
#
#===================================================================================

#	Generate DOT file representing folder/file tree

import argparse
import hashlib
import os
import sys
import shutil
import stat

def filteredName(path, name):

	fqn = os.path.normpath(os.path.join(path,name))
	md5 = hashlib.md5()
	md5.update(fqn.encode())
	hex = md5.hexdigest()

	dotfile.write("// path: <"+path+"> name: <"+name+"> fqn: <"+fqn+">\n")
	dotfile.write("// hex: <"+hex+">\n")

	return hex


def processfile(dirname, fname, phase):
	#print "<"+dirname+"> <"+fname+">"

	name = filteredName(dirname, fname)

	gvFileLabel = "gv_f_" + name
	gvFilenameLabel = "gv_fl_" + name

	if phase==0:

		xtra = ''
		if args.size or args.md5:
			dstfilename = os.path.join(dirname,fname)
			if os.path.exists(dstfilename):

				shellcmd = "md5sum '"+dstfilename+"' > _md5sum.txt"
				os.system(shellcmd)

				md5file = open("_md5sum.txt","r")
				for line in md5file:
					line = line.rstrip().lstrip()
					if line.endswith(dstfilename):
						break
				md5file.close()

				dstsize = os.stat(dstfilename)[stat.ST_SIZE]
				dstmd5 = line.split()[0]

				if args.size:
					xtra = '\nSize: '+str(dstsize)

				if args.md5:
					xtra = xtra+'\nMD5: '+dstmd5

		dotfile.write(gvFileLabel + " [shape=point]\n")
		dotfile.write(gvFilenameLabel+'[label="' + fname + xtra+'", shape=none]\n')
		dotfile.write(gvFileLabel + ' -> ' + gvFilenameLabel + '\n')
		dotfile.write('\n')

	return gvFileLabel


def processdir(dirname, dname, phase):
	#print "<"+dirname+"> <"+dname+">"

	name = filteredName(dirname,dname)

	gvDirLabel = "gv_d_"+name
	gvDirnameLabel = "gv_dl_" + name

	if phase==0:
		dotfile.write(gvDirLabel + " [shape=point]\n")
		dotfile.write(gvDirnameLabel+'[label="' + dname + '", shape=folder]\n')
		dotfile.write(gvDirLabel + ' -> ' + gvDirnameLabel + '\n')
		dotfile.write('\n')

	return gvDirLabel


def processtree(treename, phase):
	# os.mkdir("_"+treename)

	if phase==0:
  		dotfile.write("gv_dl_" + filteredName(treename,'') + ' [label="' + treename + '" shape=box]\n')

	#skipdirs = ["merged", "intermediates", "generated" ]

	skipdirs = args.skipdirs.split(',')
	for path, dirnames, filenames in os.walk(treename):

		#segments = os.path.split(path)
		segments = path.split(os.path.sep)
		if args.depth>0 and len(segments)>args.depth:
			continue

		processfiles = True
		for segment in segments:

			if not args.unhide and segment.startswith("."):
				processfiles = False
				break

			if segment in skipdirs:
				processfiles = False
				break


		if processfiles==True:
			files = None
			for dname in dirnames:
				if not args.unhide and dname.startswith("."):
					continue

				if dname in skipdirs:
					continue

				if files==None:
					files = ""
				files = files + " -> " + processdir(path, dname, phase)

			if not args.xfiles:
				for fname in filenames:
					if not args.unhide and fname.startswith("."):
						continue

					if fname.endswith(".chm") or fname.endswith("~"):
						continue

					if files==None:
						files = ""
					files = files + " -> " + processfile(path, fname, phase)

			if phase==1:

				if not files==None:

					head, tail = os.path.split(path)

					dotfile.write("    // path: <"+path+">\n")
					#dotfile.write("    // head: <"+head+">\n")
					#dotfile.write("    // tail: <"+tail+">\n")

					dotfile.write("    {\n")
					dotfile.write("    rank=same;\n")
					dotfile.write("    gv_dl_" + filteredName(head,tail) + files + " [arrowhead=none]\n")
					dotfile.write("    }\n\n")

def check_parameters(argv):
	parser = argparse.ArgumentParser(description='Generate a DOT file representing a folder/file tree')

	parser.add_argument('-d', '--depth',  	type=int, required=False, help='Limit tree walk to this depth')
	parser.add_argument('-m', '--md5',		default=False, action="store_true", help='Show file MD5')
	parser.add_argument('-o', '--output',	type=str, required=False, help='Output .dot file')
	parser.add_argument('-s', '--size',		default=False, action="store_true", help='Show file size')
	parser.add_argument(      '--skipdirs', type=str, required=False,  help='Exclude folders if path contains any of the dirs')
	parser.add_argument('-t', '--tree',    	type=str, required=True,  help='Tree to represent')
	parser.add_argument('-u', '--unhide',	default=False, action="store_true", help='Show files and folders that begin with "."')
	parser.add_argument(      '--xfiles',	default=False, action="store_true", help='Exclude files, only show folders')

	parser.add_argument('-v', '--verbose',	default=False, action="store_true", help='Increase output verbosity')

	args = parser.parse_args()

	if args.depth==None:
		args.depth=0

	if args.output==None:
		args.output = args.tree.replace('.','_').replace(' ', '')

	if not args.output.endswith(".dot"):
		args.output = args.output+".dot"

	if args.skipdirs==None:
		args.skipdirs = ''

	print args.skipdirs

	return args


args = check_parameters(sys.argv)

dotfile = open(args.output, 'w')
dotfile.write('digraph tree {\n')
dotfile.write('    graph [fontname = "helvetica"]\n')
dotfile.write('    node [fontname = "helvetica"]\n')
dotfile.write('    edge [fontname = "helvetica"]\n')
dotfile.write('    rankdir=LR;\n')

# Phase 0: Generate all component elements
processtree(args.tree, 0)

# Phase 1: Generate links to parents
processtree(args.tree, 1)

dotfile.write("}")
dotfile.close()
