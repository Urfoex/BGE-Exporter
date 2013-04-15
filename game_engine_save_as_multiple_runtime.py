# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# building on top of Moguris work #

bl_info = {
	'name': 'Save As Multiple Game Engine Runtime',
	'author': 'Manuel Bellersen (Urfoex)',
	'version': (0, 0, 1),
	"blender": (2, 66, 0),
	'location': 'File > Export',
	'description': 'Bundle a .blend file with the Blenderplayer',
	'warning': 'Currently only 64 bit support',
	'wiki_url': '',
	'tracker_url': '',
	'category': 'Game Engine'}

import bpy
import os
import sys
import shutil
import tempfile
from bpy.props import *


class SaveAsMultipleRuntime(bpy.types.Operator):
	bl_idname = "wm.save_as_multiple_runtime"
	bl_label = "Save As Multiple Game Engine Runtime"
	bl_options = {'REGISTER'}
	
	#if sys.platform == 'darwin':
		# XXX, this line looks suspicious, could be done better?
		#blender_bin_dir_darwin = '/' + os.path.join(*bpy.app.binary_path.split('/')[0:-4])
		#ext = '.app'
	#else:
		#blender_bin_path = bpy.app.binary_path
		#blender_bin_dir = os.path.dirname(blender_bin_path)
		#ext = os.path.splitext(blender_bin_path)[-1].lower()

	blender_version = str(bpy.app.version[0]) + "." + str(bpy.app.version[1]) + "." + str(bpy.app.version[2])
	default_player_path = bpy.utils.script_paths()[1] + os.sep + blender_version
	
	player_url = "https://bitbucket.org/Urfoex/bge-exporter/get/" + blender_version + ".tar.gz"

	blender_bin_dir_linux = default_player_path + os.sep + "linux_64" + os.sep
	blender_bin_dir_windows = default_player_path + os.sep + "windows_64" + os.sep
	blender_bin_dir_darwin = default_player_path + os.sep +"osx_64" + os.sep + "Blender" + os.sep

	default_player_path_linux = os.path.join(blender_bin_dir_linux, 'blenderplayer')
	default_player_path_windows = os.path.join(blender_bin_dir_windows, 'blenderplayer.exe')
	default_player_path_osx = os.path.join(blender_bin_dir_darwin, 'blenderplayer.app')

	filepath = StringProperty(
			subtype='FILE_PATH',
			)
	#copy_python = BoolProperty(
			#name="Copy Python",
			#description="Copy bundle Python with the runtime",
			#default=True,
			#)

    
	def execute(self, context):
		import time
		start_time = time.clock()
		print("Saving runtime to %r" % self.filepath)
		self.get_player_files()
		self.create_directories()
		self.WriteRuntime(player_path=self.default_player_path_linux,
					output_path=self.filepath + os.sep + "bin_linux_64",
					copy_python=True,
					#copy_python=self.copy_python,
					copy_dlls=False,
					target_os='LINUX',
					report=self.report,
					)
		self.WriteRuntime(player_path=self.default_player_path_windows,
					output_path=self.filepath + os.sep + "bin_windows_64",
					copy_python=True,
					#copy_python=self.copy_python,
					copy_dlls=True,
					target_os='WINDOWS',
					report=self.report,
					)
		self.WriteRuntime(player_path=self.default_player_path_osx,
					output_path=self.filepath + os.sep + "bin_osx_64",
					copy_python=True,
					#copy_python=self.copy_python,
					copy_dlls=False,
					target_os='OSX',
					report=self.report,
					)
		
		print("Finished in %.4fs" % (time.clock()-start_time))
		return {'FINISHED'}

	def invoke(self, context, event):
		if not self.filepath:
			ext = '.app' if sys.platform == 'darwin' else os.path.splitext(bpy.app.binary_path)[-1]
			self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ext)

		wm = context.window_manager
		wm.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def get_player_files(self):
		print("Getting files from:", self.player_url)
		print("Putting to:", self.default_player_path)
	
	def create_directories(self):
		if not os.path.exists(self.filepath):
			os.makedirs(self.filepath)
	
	def CopyPythonLibs(dst, overwrite_lib, report=print):
		import platform

		# use python module to find python's libpath
		src = os.path.dirname(platform.__file__)

		# dst points to lib/, but src points to current python's library path, eg:
		#  '/usr/lib/python3.2' vs '/usr/lib'
		# append python's library dir name to destination, so only python's
		# libraries would be copied
		if os.name == 'posix':
			dst = os.path.join(dst, os.path.basename(src))

		if os.path.exists(src):
			write = False
			if os.path.exists(dst):
				if overwrite_lib:
					shutil.rmtree(dst)
					write = True
			else:
				write = True
			if write:
				shutil.copytree(src, dst, ignore=lambda dir, contents: [i for i in contents if i == '__pycache__'])
		else:
			report({'WARNING'}, "Python not found in %r, skipping python copy" % src)
        
	def WriteAppleRuntime(self, player_path, output_path, copy_python, overwrite_lib):
		# Enforce the extension
		if not output_path.endswith('.app'):
			output_path += '.app'

		# Use the system's cp command to preserve some meta-data
		os.system('cp -R "%s" "%s"' % (player_path, output_path))
		
		bpy.ops.wm.save_as_mainfile(filepath=os.path.join(output_path, "Contents" + os.sep + "Resources" + os.sep + "game.blend"),
									relative_remap=False,
									compress=False,
									copy=True,
									)
		
		# Python doesn't need to be copied for OS X since it's already inside blenderplayer.app
		
	def WriteRuntime(self, player_path, output_path, copy_python, overwrite_lib, copy_dlls, target_os, report=print):
		import struct

		# Check the paths
		if not os.path.isfile(player_path) and not(os.path.exists(player_path) and player_path.endswith('.app')):
			report({'ERROR'}, "The player could not be found! Runtime not saved")
			return
		
		# Check if we're bundling a .app
		if player_path.endswith('.app'):
			self.WriteAppleRuntime(player_path, output_path, copy_python, overwrite_lib)
			return
			
		# Enforce "exe" extension on Windows
		if player_path.endswith('.exe') and not output_path.endswith('.exe'):
			output_path += '.exe'
		
		# Get the player's binary and the offset for the blend
		file = open(player_path, 'rb')
		player_d = file.read()
		offset = file.tell()
		file.close()
		
		# Create a tmp blend file (Blenderplayer doesn't like compressed blends)
		tempdir = tempfile.mkdtemp()
		blend_path = os.path.join(tempdir, bpy.path.clean_name(output_path))
		bpy.ops.wm.save_as_mainfile(filepath=blend_path,
									relative_remap=False,
									compress=False,
									copy=True,
									)
		blend_path += '.blend'
		
		# Get the blend data
		blend_file = open(blend_path, 'rb')
		blend_d = blend_file.read()
		blend_file.close()

		# Get rid of the tmp blend, we're done with it
		os.remove(blend_path)
		os.rmdir(tempdir)
		
		# Create a new file for the bundled runtime
		output = open(output_path, 'wb')
		
		# Write the player and blend data to the new runtime
		print("Writing runtime...", end=" ")
		output.write(player_d)
		output.write(blend_d)
		
		# Store the offset (an int is 4 bytes, so we split it up into 4 bytes and save it)
		output.write(struct.pack('B', (offset>>24)&0xFF))
		output.write(struct.pack('B', (offset>>16)&0xFF))
		output.write(struct.pack('B', (offset>>8)&0xFF))
		output.write(struct.pack('B', (offset>>0)&0xFF))
		
		# Stuff for the runtime
		output.write(b'BRUNTIME')
		output.close()
		
		print("done")
		
		# Make the runtime executable on Linux
		if target_os == 'LINUX':
			os.chmod(output_path, 0o755)
			
		## Copy bundled Python
		blender_dir = self.blender_bin_dir_linux if target_os == 'LINUX' else self.blender_bin_dir_windows
		runtime_dir = os.path.dirname(output_path)
		
		if copy_python:
			print("Copying Python files...", end=" ")
			src = os.path.join(blender_dir, bpy.app.version_string.split()[0])
			dst = os.path.join(runtime_dir, bpy.app.version_string.split()[0])
			print("from", src, "to", dst)
			shutil.copytree(src=src, dst=dst)
			print("done")

		# And DLLs
		if copy_dlls:
			print("Copying DLLs...", end=" ")
			for file in [i for i in os.listdir(blender_dir) if i.lower().endswith('.dll')]:
				src = os.path.join(blender_dir, file)
				dst = os.path.join(runtime_dir, file)
				shutil.copy2(src, dst)

			print("done")


def menu_func(self, context):
	self.layout.operator(SaveAsMultipleRuntime.bl_idname)


def register():
	bpy.utils.register_module(__name__)

	bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
	bpy.utils.unregister_module(__name__)

	bpy.types.INFO_MT_file_export.remove(menu_func)


if __name__ == "__main__":
	register()
