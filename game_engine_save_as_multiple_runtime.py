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
	'version': (0, 0, 5),
	"blender": (2, 66, 1),
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
import tarfile
import urllib.request
from bpy.props import StringProperty, BoolProperty


class SaveAsMultipleRuntime(bpy.types.Operator):
	bl_idname = "wm.save_as_multiple_runtime"
	bl_label = "Save As Multiple Game Engine Runtime"
	bl_options = {'REGISTER'}

	blender_version = str(bpy.app.version[0]) + "." + str(bpy.app.version[1]) + "." + str(bpy.app.version[2])
	default_player_path = bpy.utils.script_paths()[1] + os.sep + blender_version

	player_url = "https://bitbucket.org/Urfoex/bge-exporter/get/" + blender_version + ".tar.gz"
	player_local = bpy.utils.script_paths()[1] + os.sep + blender_version + ".tar.gz"

	blender_bin_dir_linux = default_player_path + os.sep + "linux_64" + os.sep
	blender_bin_dir_windows = default_player_path + os.sep + "windows_64" + os.sep
	blender_bin_dir_darwin = default_player_path + os.sep + "osx_64" + os.sep + "Blender" + os.sep

	default_player_path_linux = os.path.join(blender_bin_dir_linux, 'blenderplayer')
	default_player_path_windows = os.path.join(blender_bin_dir_windows, 'blenderplayer.exe')
	default_player_path_osx = os.path.join(blender_bin_dir_darwin, 'blenderplayer.app')

	start_blend = default_player_path + os.sep + "start.blend"
	game_name = "game"

	filepath = StringProperty(
			subtype='FILE_PATH',
			)
	create_windows_runtime = BoolProperty(
			name="Create executable for Windows",
			description="Create executable for Windows",
			default=True
			)
	create_linux_runtime = BoolProperty(
			name="Create executable for Linux",
			description="Create executable for Linux",
			default=True
			)
	create_osx_runtime = BoolProperty(
			name="Create executable for OSX",
			description="Create executable for OSX",
			default=True
			)

	def execute(self, context):
		import time
		start_time = time.clock()
		print("Saving runtime to", self.filepath)
		self.game_name = bpy.path.basename(bpy.data.filepath)[:-6]
		if not self.game_name:
			self.game_name = "game"
		self.get_player_files()
		self.create_directories()
		self.write_runtimes()
		print("Finished in %.4fs" % (time.clock() - start_time))
		return {'FINISHED'}

	def invoke(self, context, event):
		if not self.filepath:
			self.filepath = bpy.data.filepath[:-6]

		wm = context.window_manager
		wm.fileselect_add(self)
		return {'RUNNING_MODAL'}

	def get_player_files(self):
		print("Getting files from:", self.player_url)
		print("Putting to:", self.default_player_path)

		if not  os.path.exists(self.player_local):
			self.get_remote_tgz()
		if not  os.path.exists(self.default_player_path):
			#os.mkdir(self.default_player_path)
			self.unzip_tgz()
		print("Done.")

	def get_remote_tgz(self):
		print("Downloading...")
		urllib.request.urlretrieve(self.player_url, self.player_local, reporthook)
		#remote_zip = urllib.request.urlopen(self.player_url)
		#local_zip = open(self.player_local, 'wb')
		#local_zip.write(remote_zip.readall())
		#local_zip.close()

	def unzip_tgz(self):
		print("Extracting outer...")
		p = bpy.utils.script_paths()[1] + os.sep
		tgz_file = tarfile.open(self.player_local, 'r:gz')
		to_rename = os.path.join(p, os.path.commonprefix(tgz_file.getnames()))
		tgz_file.extractall(path=p)
		tgz_file.close()

		os.rename(to_rename, self.default_player_path)

		print("Extracting inner...")
		for archive in os.listdir(self.default_player_path):
			if archive.endswith(".tar.gz"):
				print("Extracting ", archive)
				tgz_file = tarfile.open(os.path.join(self.default_player_path, archive), 'r:gz')
				tgz_file.extractall(path=self.default_player_path)
				tgz_file.close()
				os.remove(os.path.join(self.default_player_path, archive))

	def create_directories(self):
		if not os.path.exists(self.filepath):
			os.makedirs(self.filepath)

	def write_runtimes(self):
		if self.create_windows_runtime:
			self.write_windows_runtime()
		if self.create_linux_runtime:
			self.write_linux_runtime()
		if self.create_osx_runtime:
			self.write_osx_runtime()
		self.write_blend()
		self.write_python()

	def player_exists(self, player_path):
		return os.path.isfile(player_path) or (os.path.exists(player_path) and player_path.endswith('.app'))

	def create_player(self, player_path, target_path):
		import struct

		# Get the player's binary and the offset for the blend
		file = open(player_path, 'rb')
		player_d = file.read()
		offset = file.tell()
		file.close()

		# Get the blend data
		blend_file = open(self.start_blend, 'rb')
		blend_d = blend_file.read()
		blend_file.close()

		# Create a new file for the bundled runtime
		output = open(target_path, 'wb')

		# Write the player and blend data to the new runtime
		print("Writing runtime...")
		output.write(player_d)
		output.write(blend_d)

		# Store the offset (an int is 4 bytes, so we split it up into 4 bytes and save it)
		output.write(struct.pack('B', (offset >> 24) & 0xFF))
		output.write(struct.pack('B', (offset >> 16) & 0xFF))
		output.write(struct.pack('B', (offset >> 8) & 0xFF))
		output.write(struct.pack('B', (offset >> 0) & 0xFF))

		# Stuff for the runtime
		output.write(b'BRUNTIME')
		output.close()

		print("Done.")

	def copy_python(self, python_path):
		## Copy bundled Python
		print("Copying Python files...")
		src = os.path.join(python_path, bpy.app.version_string.split()[0])
		dst = os.path.join(self.filepath, bpy.app.version_string.split()[0])
		if not os.path.exists(dst):
			os.mkdir(dst)
		print("from", src, "to", dst)
		self.recursive_copy(src, dst)

		print("Done.")

	def recursive_copy(self, src, dst):
		for entry in os.listdir(src):
			e = os.path.join(src, entry)
			target = os.path.join(dst, entry)
			if os.path.isdir(e):
				if not os.path.exists(target):
					os.mkdir(target)
				self.recursive_copy(e, os.path.join(dst, entry))
			else:
				#print("Copying:", e, "to", target)
				shutil.copy2(e, target)

	def copy_dll(self):
		print("Copying DLLs...")
		for file in [i for i in os.listdir(self.blender_bin_dir_windows) if i.lower().endswith('.dll')]:
			src = os.path.join(self.blender_bin_dir_windows, file)
			dst = os.path.join(self.filepath, file)
			shutil.copy2(src, dst)
		print("Done.")

	def write_runtime(self, player_path, target_path, python_path):
		if not self.player_exists(player_path):
			print({'ERROR'}, "Could not find", player_path)
			return
		print("Player:", player_path)
		print("Target:", target_path)
		print("Python:", python_path)
		self.create_player(player_path, target_path)
		self.copy_python(python_path)

	def write_linux_runtime(self):
		target = self.filepath + os.sep + self.game_name + "_linux_64.bin"
		self.write_runtime(
				player_path=self.default_player_path_linux,
				target_path=target,
				python_path=self.blender_bin_dir_linux
				)
		os.chmod(target, 0o755)

	def write_windows_runtime(self):
		self.write_runtime(
				player_path=self.default_player_path_windows,
				target_path=self.filepath + os.sep + self.game_name + "_windows_64.exe",
				python_path=self.blender_bin_dir_windows
				)
		self.copy_dll()

	def write_osx_runtime(self):
		player_path = self.default_player_path_osx
		target_path = self.filepath + os.sep + self.game_name + "_osx_64.app"
		print("Player:", player_path)
		print("Target:", target_path)
		if not self.player_exists(player_path):
			print({'ERROR'}, "Could not find", player_path)
			return
		shutil.copytree(src=player_path, dst=target_path)
		shutil.copy2(src=self.start_blend, dst=os.path.join(target_path, "Contents" + os.sep + "Resources" + os.sep + "game.blend"))

	def write_blend(self):
		blend_path = os.path.join(self.filepath, self.game_name + ".blend")
		bpy.ops.wm.save_as_mainfile(
				filepath=blend_path,
				relative_remap=False,
				compress=True,
				copy=True,
				)

	def write_python(self):
		game_blend_file = self.game_name + ".blend"
		python_text = """import bge

def load_game_blend(cont):
	bge.logic.startGame(\""""
		python_text += game_blend_file
		python_text += """\")"""
		python_file = open(self.filepath + os.sep + "start_game.py", "w")
		python_file.write(python_text)
		python_file.close()


def reporthook(blocknum, blocksize, totalsize):
	# Thanks to J.F. Sebastian
	# http://stackoverflow.com/questions/13881092/download-progressbar-for-python-3/13895723#13895723
	readsofar = blocknum * blocksize
	if totalsize > 0:
		percent = readsofar * 1e2 / totalsize
		s = "\r%5.1f%% %*d / %d" % (percent, len(str(totalsize)), readsofar, totalsize)
		sys.stderr.write(s)
		if readsofar >= totalsize:  # near the end
			sys.stderr.write("\n")
	else:  # total size is unknown
		sys.stderr.write("read %d\n" % (readsofar,))


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
