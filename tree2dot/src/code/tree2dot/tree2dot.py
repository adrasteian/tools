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
import random
import sys
import shutil
import stat

def fg4bg(bg_color):

	if bg_color.startswith('gray'):
		if bg_color=='gray':
			return 'white'

		value = int(bg_color.replace('gray',''))
		if value<70:
			#print 'gray' + str(value) + '> white'
			return 'white'
		else:
			#print 'gray' + str(value) + '> black'
			return 'black'

	try:
		return {
			'burlywood3':'white','burlywood4':'white',
			'darkorange':'white', 'darkorange1':'white', 'darkorange2':'white', 'darkorange3':'white', 'darkorange4':'white',
			'dodgerblue':'white', 'dodgerblue1':'white', 'dodgerblue2':'white', 'dodgerblue3':'white', 'dodgerblue4':'white',
			'olivedrab':'white', 'olivedrab3':'white', 'olivedrab4':'white',
			'orangered':'white', 'orangered1':'white', 'orangered2':'white', 'orangered3':'white', 'orangered4':'white',
			'pink3':'white', 'pink4':'white'
			}[bg_color]
	except:
		#print 'fg4bg('+ bg_color + ')'
		return 'black'

def get_label(name):

	return name.replace('-','_')

def filteredName(path, name):

	fqn = os.path.normpath(os.path.join(path,name))
	md5 = hashlib.md5()
	try:
		md5.update(fqn.encode())
	except:
		fqn = os.path.normpath(os.path.join(path,name.split(' ')[0]))
		print 'ERROR: <' + path + '> <' + name + '> try ' + fqn

	hex = md5.hexdigest()

	dotfile.write("// path: <"+path+"> name: <"+name+"> fqn: <"+fqn+">\n")
	dotfile.write("// hex: <"+hex+">\n")

	return hex


def processfile(dirname, fname, phase, fontcolor):
	#print "<"+dirname+"> <"+fname+">"

	name = filteredName(dirname, fname)

	gvFileLabel = "gv_f_" + name
	gvFilenameLabel = "gv_fl_" + name

	if phase==0 or phase==2:

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
					xtra = '<br/>Size: '+str(dstsize)

				if args.md5:
					xtra = xtra+'<br/>MD5: '+dstmd5

		dotfile.write(gvFileLabel + " [shape=point]\n")
		if fname in args.redfiles:
			dotfile.write(gvFilenameLabel+'[label=< <b>' + fname + '</b>' + xtra+' >, shape=ellipse, color=red, fontcolor=' + fontcolor + ']\n')
		elif fname in args.greenfiles:
			dotfile.write(gvFilenameLabel+'[label=< <b>' + fname + '</b>' + xtra+' >, shape=ellipse, color=green, fontcolor=' + fontcolor + ']\n')
		elif fname in args.amberfiles:
			dotfile.write(gvFilenameLabel+'[label=< <b>' + fname + '</b>' + xtra+' >, shape=ellipse, color=orange, fontcolor=' + fontcolor + ']\n')
		else:
			dotfile.write(gvFilenameLabel+'[label=< <b>' + fname + '</b>' + xtra+' >, shape=none, fontcolor=' + fontcolor + ']\n')
		dotfile.write(gvFileLabel + ' -> ' + gvFilenameLabel + '\n')
		dotfile.write('\n')

	return gvFileLabel


def processdir(dirname, dname, phase, emit_label):
	#print "<"+dirname+"> <"+dname+">"

	name = filteredName(dirname,dname)

	gvDirLabel = "gv_d_"+name
	gvDirnameLabel = "gv_dl_" + name

	if emit_label:
		if phase==0 or phase==2:
			dotfile.write(gvDirLabel + " [shape=point]\n")
			dotfile.write(gvDirnameLabel+'[label=< <b>' + dname + '</b> >, shape=folder, fillcolor=' + args.foldercolor + ', style=filled]\n')
			dotfile.write(gvDirLabel + ' -> ' + gvDirnameLabel + '\n')
			dotfile.write('\n')

	return gvDirLabel


def processtree(treename, subgraphs, phase):
	# os.mkdir("_"+treename)

	if phase==0:
  		dotfile.write("gv_dl_" + filteredName(treename,'') + ' [label=< <b>' + treename + '</b> >, shape=box]\n')

	skipdirs = args.skipdirs
	skipfiles = args.skipfiles
	skipsegs = args.skipsegs
	for path, dirnames, filenames in os.walk(treename):

		#print 'Path <'+path+'>'

		#segments = os.path.split(path)
		segments = path.split(os.path.sep)
		if args.depth>0 and len(segments)>args.depth:
			continue


		#	Don't show folders in paths that have dotted segments unless
		#	option to "unhide" them has been provided...

		processfiles = True
		for segment in segments:

			if not args.unhide and segment.startswith("."):
				processfiles = False
				break

			if segment in skipsegs:
				processfiles = False
				break

		if processfiles==True:
			files = None
			for dname in dirnames:
				if not args.unhide and dname.startswith("."):
					continue

				if dname in skipsegs:
					continue

				dpath = os.path.join(path,dname)
				skip = False
				for skipdir in skipdirs:
					if dpath==skipdir and args.retaintopdirs:
						# dpath is the top-level folder to be skipped but command line
						# option to retain the top-level folder in the final graph has
						# been specified so allow this one into the graph...
						break
					elif dpath.startswith(skipdir):
						# ...below a folder in the skipdirs list so don't let it into
						# the graph...
						skip = True
						#print '...skipping (<'+skipdir+'>)'
						break
				if skip:
					continue

				# If sub-graphs have been provided iterate the list and determine if
				# this folder lies within the top-level subgraph folder. If we are
				# building main folder/file graph (phase<2) then skip this folder.
				# If we are building subgraphs (phase>1) then process the folder as
				# normal...
				if not subgraphs==None:
					insubgraph = False
					dpath = os.path.join(path,dname)
					for subgraph in subgraphs:
						insubgraph = dpath.startswith(subgraph['path'])
						#insubgraph = dpath.startswith(subgraph)

						issubgraph = dpath == subgraph['path']
						if insubgraph:
							#print str(phase) + ":" + dpath + " in " + subgraph
							break

					emit_label = True
					if phase<2 and insubgraph:
						if issubgraph:
							emit_label = False
						else:
							continue
					elif phase==3 and issubgraph:
						# ...prevents emission of unneeded link from parent to subgraph
						# as subgraph will appear in parent's list of child links...
						continue

					if phase>1 and not insubgraph:
						continue
				else:
					emit_label = True

				if files==None:
					files = ""
				files = files + " -> " + processdir(path, dname, phase, emit_label)

			if not args.xfiles:

				for fname in filenames:

					if not args.unhide and fname.startswith("."):
						continue

					if fname.endswith(".chm") or fname.endswith("~"):
						continue

					if fname in skipfiles:
						continue

					skip = False
					for skipdir in skipdirs:
						if path.startswith(skipdir):
							skip = True
							break
					if skip:
						continue

					# ...similarly sub-graphs have been provided so iterate the list and
					# determine if this file lies within the top-level subgraph folder. If we are
					# building main folder/file graph (phase<2) then skip this folder.
					# If we are building subgraphs (phase>1) then process the folder as
					# normal...
					fontcolor = 'black'
					if not subgraphs==None:
						insubgraph = False
						for subgraph in subgraphs:
							insubgraph = path.startswith(subgraph['path'])
							#insubgraph = path.startswith(subgraph)
							if insubgraph:
								#print str(phase) + ":" + path + " in " + subgraph
								fontcolor = fg4bg(subgraph['color'])
								break
						if phase<2 and insubgraph:
							continue
						if phase>1 and not insubgraph:
							continue

					if files==None:
						files = ""
					files = files + " -> " + processfile(path, fname, phase, fontcolor)

			if phase==1 or phase==3:

				if not files==None:

					head, tail = os.path.split(path)

					dotfile.write("    // path: <"+path+">\n")
					#dotfile.write("    // head: <"+head+">\n")
					#dotfile.write("    // tail: <"+tail+">\n")

					dotfile.write("    {\n")
					dotfile.write("    rank=same;\n")
					#dotfile.write("    gv_dl_" + filteredName(head,tail) + files + " [arrowhead=none, weight=0]\n")
					#dotfile.write("    gv_dl_" + filteredName(head,tail) + files + " [constraint=false, arrowhead=none]\n")
					dotfile.write("    gv_dl_" + filteredName(head,tail) + files + " [arrowhead=none]\n")
					dotfile.write("    }\n\n")

def check_parameters(argv):
	parser = argparse.ArgumentParser(description='Generate a DOT file representing a folder/file tree')

	parser.add_argument('-a', '--amberfiles',	type=str, required=False, help='Highlight files in comma separated list with amber ellipse')
	parser.add_argument(	  '--bluesubgraphs',	type=str, required=False, help='Comma separated list of subgraphs with blue background')
	parser.add_argument('-d', '--depth',  		type=int, required=False, help='Limit tree walk to this depth')
	parser.add_argument('-f', '--foldercolor',	type=str, required=False, help='Set folder fill color X11 color scheme see https://www.graphviz.org/doc/info/colors.html')
	parser.add_argument(	  '--fawnsubgraphs',	type=str, required=False, help='Comma separated list of subgraphs with fawn background')
	parser.add_argument('-g', '--greenfiles',	type=str, required=False, help='Highlight files in comma separated list with green ellipse')
	parser.add_argument(	  '--graysubgraphs',	type=str, required=False, help='Comma separated list of subgraphs with gray background')
	parser.add_argument(	  '--greensubgraphs',	type=str, required=False, help='Comma separated list of subgraphs with green background')
	parser.add_argument('-m', '--md5',			default=False, action="store_true", help='Show file MD5')
	parser.add_argument(	  '--orangesubgraphs',	type=str, required=False, help='Comma separated list of subgraphs with orange background')
	parser.add_argument('-o', '--output',		type=str, required=False, help='Output .dot file')
	parser.add_argument(	  '--pinksubgraphs',	type=str, required=False, help='Comma separated list of subgraphs with pink background')
	parser.add_argument(	  '--redsubgraphs',	type=str, required=False, help='Comma separated list of subgraphs with red background')
	parser.add_argument('-r', '--redfiles',		type=str, required=False, help='Highlight files in comma separated list with red ellipse')
	parser.add_argument(      '--retaintopdirs',	default=False, action="store_true", help='Retain top-level folders nominated for skipping')
	parser.add_argument('-s', '--size',			default=False, action="store_true", help='Show file size')
	parser.add_argument(      '--skipdirs', 	type=str, required=False,  help='Exclude folders if path starts with any of comma separated list')
	parser.add_argument(      '--skipfiles', 	type=str, required=False,  help='Exclude files')
	parser.add_argument(      '--skipsegs', 	type=str, required=False,  help='Exclude folders if path contains any of the segments in comma separated list')
	parser.add_argument(	  '--subgraphblue',	type=str, required=False, help='Blue color to use for subgraph fill')
	parser.add_argument(	  '--subgraphfawn',	type=str, required=False, help='Fawn color to use for subgraph fill')
	parser.add_argument(	  '--subgraphgreen',	type=str, required=False, help='Green color to use for subgraph fill')
	parser.add_argument(	  '--subgraphorange',	type=str, required=False, help='Orange color to use for subgraph fill')
	parser.add_argument(	  '--subgraphpink',	type=str, required=False, help='Pink color to use for subgraph fill')
	parser.add_argument('-t', '--tree',    		type=str, required=True,  help='Tree to represent')
	parser.add_argument('-u', '--unhide',		default=False, action="store_true", help='Show files and folders that begin with "."')
	parser.add_argument(      '--xfiles',		default=False, action="store_true", help='Exclude files, only show folders')

	parser.add_argument('-v', '--verbose',		default=False, action="store_true", help='Increase output verbosity')

	args = parser.parse_args()

	amberfiles = args.amberfiles
	if amberfiles==None:
		amberfiles = ''
	args.amberfiles = amberfiles.split(',')

	if args.depth==None:
		args.depth=0

	if args.foldercolor==None:
		args.foldercolor='white'

	greenfiles = args.greenfiles
	if greenfiles==None:
		greenfiles = ''
	args.greenfiles = greenfiles.split(',')

	if args.output==None:
		args.output = args.tree.replace('.','_').replace(' ', '')

	if not args.output.endswith(".dot"):
		args.output = args.output+".dot"

	redfiles = args.redfiles
	if redfiles==None:
		redfiles = ''
	args.redfiles = redfiles.split(',')

	skipdirs = args.skipdirs
	if skipdirs==None:
		skipdirs = ''
	args.skipdirs = skipdirs.split(',')

	skipfiles = args.skipfiles
	if skipfiles==None:
		skipfiles = ''
	args.skipfiles = skipfiles.split(',')

	skipsegs = args.skipsegs
	if skipsegs==None:
		skipsegs = ''
	args.skipsegs = skipsegs.split(',')

	return args


args = check_parameters(sys.argv)

subgraphs = []
if not args.bluesubgraphs==None:
	subgraphcolor = args.subgraphblue
	if subgraphcolor==None:
		subgraphcolor = 'dodgerblue'
		subgraphcolor = subgraphcolor + ['', '1', '2', '3', '4'][random.randint(0,4)]
	subgraphs = subgraphs + [ { 'color':subgraphcolor, 'path':os.path.join(args.tree, subgraph) } for subgraph in args.bluesubgraphs.split(',')]

if not args.fawnsubgraphs==None:
	subgraphcolor = args.subgraphfawn
	if subgraphcolor==None:
		subgraphcolor = 'burlywood'
		subgraphcolor = subgraphcolor + ['', '1', '2', '3', '4'][random.randint(0,4)]
	subgraphs = subgraphs + [ { 'color':subgraphcolor, 'path':os.path.join(args.tree, subgraph) } for subgraph in args.fawnsubgraphs.split(',')]

if not args.graysubgraphs==None:
	subgraphcolor = 'gray' + str(random.randint(40,99))
	subgraphs = subgraphs + [ { 'color':subgraphcolor, 'path':os.path.join(args.tree, subgraph) } for subgraph in args.graysubgraphs.split(',')]

if not args.greensubgraphs==None:
	subgraphcolor = args.subgraphgreen
	if subgraphcolor==None:
		subgraphcolor = 'olivedrab'
		subgraphcolor = subgraphcolor + ['', '1', '2', '3', '4'][random.randint(0,4)]
	subgraphs = subgraphs + [ { 'color':subgraphcolor,'path':os.path.join(args.tree, subgraph) } for subgraph in args.greensubgraphs.split(',')]

if not args.orangesubgraphs==None:
	subgraphcolor = args.subgraphorange
	if subgraphcolor==None:
		subgraphcolor = 'darkorange'
		subgraphcolor = subgraphcolor + ['', '1', '2', '3', '4'][random.randint(0,4)]
	subgraphs = subgraphs + [ { 'color':subgraphcolor,'path':os.path.join(args.tree, subgraph) } for subgraph in args.orangesubgraphs.split(',')]

if not args.pinksubgraphs==None:
	subgraphcolor = args.subgraphpink
	if subgraphcolor==None:
		subgraphcolor = 'pink'
		subgraphcolor = subgraphcolor + ['', '1', '2', '3', '4'][random.randint(0,4)]
	subgraphs = subgraphs + [ { 'color':subgraphcolor,'path':os.path.join(args.tree, subgraph) } for subgraph in args.pinksubgraphs.split(',')]

if not args.redsubgraphs==None:
	subgraphcolor = 'orangered' + ['', '1', '2', '3', '4'][random.randint(0,4)]
	subgraphs = subgraphs + [ { 'color':subgraphcolor,'path':os.path.join(args.tree, subgraph) } for subgraph in args.redsubgraphs.split(',')]

#subgraphs = [ 'samples', 'internal/ta_build', 'internal/ca_build', 'swp', 'tools', 'lib/THPAgent', 'wip' ]
#subgraphs = [ os.path.join(args.tree, subgraph) for subgraph in subgraphs]
#subgraphs = [ { 'color':'gray', 'path':os.path.join(args.tree, subgraph) } for subgraph in subgraphs]



dotfile = open(args.output, 'w')
dotfile.write('digraph tree {\n')
dotfile.write('    graph [fontname = "helvetica"]\n')
dotfile.write('    node [fontname = "helvetica"]\n')
dotfile.write('    edge [fontname = "helvetica"]\n')
dotfile.write('    rankdir=LR;\n')

if len(subgraphs)==0:
	subgraphs = None

if not args.skipdirs==None:
	# Rebuild list with each dir prefixed with tree name...
	args.skipdirs = [os.path.join(args.tree, skipdir) for skipdir in args.skipdirs]



# Phase 0: Generate all component elements
processtree(args.tree, subgraphs, 0)

# Phase 1: Generate links to parents
processtree(args.tree, subgraphs, 1)

if not subgraphs==None:
	c = 0
	for subgraph in subgraphs:

		head, tail = os.path.split(subgraph['path'])

		subgraphcolor = subgraph['color']

		dotfile.write('subgraph cluster_' + str(c) + ' {\n')
		dotfile.write('    label=< <b><font point-size="25">' + tail + '</font></b> >;\n')
		dotfile.write('    style=filled;\n')
		dotfile.write('    fillcolor=' + subgraphcolor + ';\n')
		dotfile.write('    fontcolor=' + fg4bg(subgraphcolor) + ';\n')

		#dotfile.write('    rankdir = TB;\n')

		# Phase 2: Generate all component elements
		processtree(args.tree, [ subgraph ] , 2)

		# Phase 3: Generate links to parents
		processtree(args.tree, [ subgraph ], 3)

		dotfile.write('}\n')

		c = c + 1

	color = 'gray90'
	key = 'Key'
	dotfile.write('    subgraph cluster_key {\n')
	dotfile.write('        label=< <b><font point-size="25">' + key + '</font></b> >;\n')
	dotfile.write('        style=filled;\n')
	dotfile.write('        fillcolor=' + color + ';\n')
	dotfile.write('        fontcolor=' + fg4bg(color) + ';\n')
	dotfile.write('        rankdir=LR;\n')

	for subgraph in subgraphs:
		print subgraph

		fillcolor = subgraph['color']
		dotfile.write('        subgraph cluster_' + fillcolor + ' {\n')
		dotfile.write('            label="";\n')
		dotfile.write('            color=invis;\n')

		head, tail = os.path.split(subgraph['path'])
		dotfile.write('            ' + fillcolor+'[label="", shape=box, fillcolor=' + fillcolor + ', style=filled, width=0.5]\n')
		dotfile.write('            ' + get_label(tail)+'[label=< <b>' + tail + '</b> >, shape=none]\n')
		dotfile.write('        }\n')

	for subgraph in subgraphs:
		subgraphcolor = subgraph['color']
		head, tail = os.path.split(subgraph['path'])
		dotfile.write('        ' + subgraphcolor + ' -> '+ get_label(tail) + '[ color="invis",arrowhead=none ]\n')
	dotfile.write('    }\n')


dotfile.write("}")
dotfile.close()


