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
    'version': (0, 1, 1),
    "blender": (2, 65, 1),
    'location': 'File > Export',
    'description': 'Bundle a .blend file with the Blenderplayer',
    'warning': 'Don\'t create 64 Bit and 32 Bit executables in the same directory!',
    'wiki_url': 'https://bitbucket.org/Urfoex/bge-exporter/wiki/Home',
    'tracker_url': 'https://bitbucket.org/Urfoex/bge-exporter/issues',
    'category': 'Game Engine'}

import bpy
import os
import sys
import shutil
import tarfile
import zipfile
import urllib.request
from bpy.props import StringProperty, BoolProperty, EnumProperty


class SaveAsMultipleRuntime(bpy.types.Operator):
    bl_idname = "wm.save_as_multiple_runtime"
    bl_label = "Save As Multiple Game Engine Runtime"
    bl_options = {'REGISTER'}

    blender_version_major = str(bpy.app.version[0]) + "." + str(bpy.app.version[1])
    blender_version = blender_version_major + "." + str(bpy.app.version[2])
    default_player_path = bpy.utils.script_paths()[1] + os.sep + blender_version
    default_script_path = bpy.utils.script_paths()[1] + os.sep

    official_url = "http://download.blender.org/release/Blender" + blender_version_major + "/"
    start_blend_url = "https://bitbucket.org/Urfoex/bge-exporter/get/default.tar.gz"
    #player_url = "https://bitbucket.org/Urfoex/bge-exporter/get/" + blender_version + ".tar.gz"
    #player_local = bpy.utils.script_paths()[1] + os.sep + blender_version + ".tar.gz"

    start_blend = default_player_path + os.sep + "start.blend"
    game_name = "game"

    filepath = StringProperty(
            subtype='FILE_PATH',
            )
    bit_version = EnumProperty(
            items=[('32', '32 Bit', '32 Bit executables'), ('64', '64 Bit', '64 Bit executables')],
            name='Type',
            description='Create 32 or 64 Bit execuables',
            default='32'
            )
    create_windows_runtime = BoolProperty(
            name="For Windows",
            description="Create executable for Windows",
            default=True
            )
    create_linux_runtime = BoolProperty(
            name="For Linux",
            description="Create executable for Linux",
            default=True
            )
    create_osx_runtime = BoolProperty(
            name="For OSX",
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
        self.set_variables()
        self.get_player_files()
        self.create_game_directory()
        self.write_runtimes()
        print("Finished in %.4fs" % (time.clock() - start_time))
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.data.filepath[:-6]

        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def set_variables(self):
        print("TODO: Switch-Case release names")
        self.architecture_linux = "i686"
        self.architecture_windows = "32"
        self.architecture_osx = "i386"
        if self.bit_version == "64":
            self.architecture_linux = "x86_64"
            self.architecture_windows = "64"
            self.architecture_osx = "x86_64"

        front = "blender-" + self.blender_version_major + bpy.app.version_char
        self.windows_path_name = front + "-windows" + self.architecture_windows
        self.windows_file_name = self.windows_path_name + ".zip"
        self.linux_path_name = front + "-linux-glibc211-" + self.architecture_linux
        self.linux_file_name = self.linux_path_name + ".tar.bz2"
        self.osx_path_name = front + "-OSX_10.6-" + self.architecture_osx
        self.osx_file_name = self.osx_path_name + ".zip"

    def get_player_files(self):
        self.get_files_for(
                self.create_windows_runtime,
                self.windows_path_name,
                self.windows_file_name,
                self.un_zip
                )
        self.get_files_for(
                self.create_linux_runtime,
                self.linux_path_name,
                self.linux_file_name,
                self.un_tbz2
                )
        self.get_files_for(
                self.create_osx_runtime,
                self.osx_path_name,
                self.osx_file_name,
                self.un_zip
                )
        self.clear_osx()
        print("TODO: get player.blend from repo!")
        print("Done.")

    def clear_osx(self):
        if self.create_osx_runtime:
            osx_path = self.default_script_path + "Blender"
            if os.path.exists(osx_path):
                os.rename(osx_path, self.default_script_path + self.osx_path_name)

    def get_files_for(self, create_runtime, os_path_name, file_name, extractor):
        if create_runtime:
            local_path = self.default_script_path + os_path_name
            if os.path.exists(local_path):
                print("Using:", local_path)
            else:
                self.get_external_files(file_name, extractor)

    def get_external_files(self, file_name, extractor):
        self.get_remote_file(file_name)
        who = self.default_script_path + file_name

        if os.path.exists(who):
            extractor(who, self.default_script_path)
        else:
            print("Could not find:", who)

    def get_remote_file(self, file_name):
        file_url = self.official_url + file_name
        local_file = self.default_script_path + os.sep + file_name
        if os.path.exists(local_file):
            print("Using:", local_file)
        else:
            print("Getting files from:", file_url)
            print("Putting to:", local_file)
            print("Downloading...")
            urllib.request.urlretrieve(file_url, local_file, reporthook)

    def un_tbz2(self, who, where):
        print("Extracting:", who)
        print("To:", where)
        tbz2_file = tarfile.open(who, 'r')
        tbz2_file.extractall(path=where)
        tbz2_file.close()

    def un_zip(self, who, where):
        print("Extracting:", who)
        print("To:", where)
        zip_file = zipfile.ZipFile(who, 'r')
        zip_file.extractall(path=where)
        zip_file.close()

    def create_game_directory(self):
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)

    def write_runtimes(self):
        print("TODO")

        self.set_runtimepaths()

        if self.create_windows_runtime:
            self.write_windows_runtime()
        if self.create_linux_runtime:
            self.write_linux_runtime()
        if self.create_osx_runtime:
            self.write_osx_runtime()
        self.write_blend()
        self.write_python()

    def set_runtimepaths(self):
        self.windows_runtime = self.default_script_path + self.windows_path_name + os.sep
        self.linux_runtime = self.default_script_path + self.linux_path_name + os.sep
        self.osx_runtime = self.default_script_path + self.osx_path_name + os.sep

    def player_exists(self, player_path):
        return os.path.isfile(player_path) or (os.path.exists(player_path) and player_path.endswith('.app'))

    def create_player(self, player_path, target_path):
        import struct
        print("TODO: right blend file")
        return

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
        src = os.path.join(python_path, bpy.app.version_string.split()[0]) + os.sep + "python" + os.sep
        dst = os.path.join(self.filepath, bpy.app.version_string.split()[0])
        if not os.path.exists(dst):
            os.mkdir(dst)
        dst = dst + os.sep + "python" + os.sep
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
                shutil.copy2(e, target)

    def copy_dll(self):
        print("Copying DLLs...")
        for file in [i for i in os.listdir(self.windows_runtime) if i.lower().endswith('.dll')]:
            src = os.path.join(self.windows_runtime, file)
            dst = os.path.join(self.filepath, file)
            shutil.copy2(src, dst)
        print("Done.")

    def write_runtime(self, player_path, target_path, player_name):
        player = os.path.join(player_path, player_name)
        if not self.player_exists(player):
            print({'ERROR'}, "Could not find", player)
            return
        print("Player:", player)
        print("Target:", target_path)
        print("Path:", player_path)
        self.create_player(player, target_path)
        self.copy_python(player_path)

    def write_linux_runtime(self):
        target = self.filepath + os.sep + self.game_name + "_linux_" + self.bit_version + ".bin"
        self.write_runtime(
                player_path=self.linux_runtime,
                target_path=target,
                player_name='blenderplayer'
                )
        os.chmod(target, 0o755)

    def write_windows_runtime(self):
        self.write_runtime(
                player_path=self.windows_runtime,
                target_path=self.filepath + os.sep + self.game_name + "_windows_" + self.bit_version + ".exe",
                player_name='blenderplayer.exe'
                )
        self.copy_dll()

    def write_osx_runtime(self):
        player_path = os.path.join(self.osx_runtime, 'blenderplayer.app')
        target_path = self.filepath + os.sep + self.game_name + "_osx_" + self.bit_version + ".app"
        print("Player:", player_path)
        print("Target:", target_path)
        if not self.player_exists(player_path):
            print({'ERROR'}, "Could not find", player_path)
            return
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
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
