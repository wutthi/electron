#!/usr/bin/env python

import glob
import os
import re
import shutil
import subprocess
import sys
import stat
import urllib
import tarfile

from lib.config import LIBCHROMIUMCONTENT_COMMIT, BASE_URL, PLATFORM, \
                       get_target_arch, get_chromedriver_version, \
                       get_zip_name
from lib.util import scoped_cwd, rm_rf, get_electron_version, make_zip, \
                     execute, electron_gyp


ELECTRON_VERSION = get_electron_version()
TARGET_ARCH = get_target_arch()

SOURCE_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
EIKON_3RDPARTY_DIST_DIR = os.path.join(SOURCE_ROOT, 'eikon-3rdparty-dist', ELECTRON_VERSION)
OUT_DIR = os.path.join(SOURCE_ROOT, 'out', 'R')

DIST_BIN_DIR = os.path.join(EIKON_3RDPARTY_DIST_DIR, TARGET_ARCH, 'bin')
DIST_LIB_DIR = os.path.join(EIKON_3RDPARTY_DIST_DIR, TARGET_ARCH, 'lib')
DIST_INC_DIR = os.path.join(EIKON_3RDPARTY_DIST_DIR, 'includes')
							
PROJECT_NAME = electron_gyp()['project_name%']
PRODUCT_NAME = electron_gyp()['product_name%']

TARGET_BINARIES = {
  'darwin': [
  ],
  'win32': [
    '{0}.exe'.format(PROJECT_NAME),  # 'electron.exe'
    'content_shell.pak',
    'd3dcompiler_47.dll',
    'icudtl.dat',
    'libEGL.dll',
    'libGLESv2.dll',
    'ffmpeg.dll',
    'node.dll',
    'blink_image_resources_200_percent.pak',
    'content_resources_200_percent.pak',
    'ui_resources_200_percent.pak',
    'views_resources_200_percent.pak',
    'xinput1_3.dll',
    'natives_blob.bin',
    'snapshot_blob.bin',
  ],
  'linux': [
    PROJECT_NAME,  # 'electron'
    'content_shell.pak',
    'icudtl.dat',
    'libffmpeg.so',
    'libnode.so',
    'blink_image_resources_200_percent.pak',
    'content_resources_200_percent.pak',
    'ui_resources_200_percent.pak',
    'views_resources_200_percent.pak',
    'natives_blob.bin',
    'snapshot_blob.bin',
  ],
}
TARGET_DIRECTORIES = {
  'darwin': [
    '{0}.app'.format(PRODUCT_NAME),
  ],
  'win32': [
    'resources',
    'locales',
  ],
  'linux': [
    'resources',
    'locales',
  ],
}


def main():
  rm_rf(EIKON_3RDPARTY_DIST_DIR)
  os.makedirs(EIKON_3RDPARTY_DIST_DIR)

  force_build()
  create_version()
  copy_binaries()
  copy_libraries()
  copy_headers()
  create_zip()
    
  rm_rf(EIKON_3RDPARTY_DIST_DIR)
  
  # upload_to_azure()

  
def force_build():
  build = os.path.join(SOURCE_ROOT, 'script', 'build.py')
  execute([sys.executable, build, '-c', 'Release'])


def copy_binaries():
  
  os.makedirs(DIST_BIN_DIR)
  
  for binary in TARGET_BINARIES[PLATFORM]:
    shutil.copy2(os.path.join(OUT_DIR, binary), DIST_BIN_DIR)

  for directory in TARGET_DIRECTORIES[PLATFORM]:
    shutil.copytree(os.path.join(OUT_DIR, directory),
                    os.path.join(DIST_BIN_DIR, directory),
                    symlinks=True)

def copy_libraries():
  
  os.makedirs(DIST_LIB_DIR)
  urllib.urlretrieve('https://atom.io/download/atom-shell/' + ELECTRON_VERSION + '/win-x64/iojs.lib', os.path.join(DIST_LIB_DIR, 'electron.lib'))

  
def copy_headers():

  os.makedirs(DIST_INC_DIR)
  
  # Download and extract archive from Atom Shell server
  iojs_targz_file = os.path.join(EIKON_3RDPARTY_DIST_DIR, 'iojs.tar.gz')
  urllib.urlretrieve('https://atom.io/download/atom-shell/' + ELECTRON_VERSION + '/iojs-' + ELECTRON_VERSION + '.tar.gz', iojs_targz_file)
  tfile = tarfile.open(iojs_targz_file, 'r:gz')
  tfile.extractall(EIKON_3RDPARTY_DIST_DIR)
  tfile.close()
  os.remove(iojs_targz_file)
  iojs_targz_dir = os.path.join(EIKON_3RDPARTY_DIST_DIR, 'iojs-' + ELECTRON_VERSION)
  
  # Helper header
  shutil.copy2(os.path.join(SOURCE_ROOT, 'eikon-3rdparty-dist', 'includes', 'electron.h'), os.path.join(DIST_INC_DIR))
  
  # Node headers
  SRC_NODE_DIR = os.path.join(iojs_targz_dir, 'src')
  DIST_NODE_DIR = os.path.join(DIST_INC_DIR, 'node')
  os.makedirs(DIST_NODE_DIR)
  for inc_file in glob.glob(os.path.join(SRC_NODE_DIR, '*.h')):
    shutil.copy2(os.path.join(SRC_NODE_DIR, inc_file), DIST_NODE_DIR)
	
  # V8 headers
  SRC_V8_DIR = os.path.join(iojs_targz_dir, 'deps', 'v8', 'include')
  DIST_V8_DIR = os.path.join(DIST_INC_DIR, 'v8')
  os.makedirs(DIST_V8_DIR)
  for inc_file in glob.glob(os.path.join(SRC_V8_DIR, '*.h')):
    shutil.copy2(os.path.join(SRC_V8_DIR, inc_file), DIST_V8_DIR)
  os.makedirs(os.path.join(DIST_V8_DIR, 'libplatform'))
  shutil.copy2(os.path.join(SRC_V8_DIR, 'libplatform', 'libplatform.h'), os.path.join(DIST_V8_DIR, 'libplatform'))

  # UV headers
  SRC_UV_DIR = os.path.join(iojs_targz_dir, 'deps', 'uv', 'include')
  DIST_UV_DIR = os.path.join(DIST_INC_DIR, 'uv')
  os.makedirs(DIST_UV_DIR)
  for inc_file in glob.glob(os.path.join(SRC_UV_DIR, '*.h')):
    shutil.copy2(os.path.join(SRC_UV_DIR, inc_file), DIST_UV_DIR)
	
  # ZLib headers
  SRC_ZLIB_DIR = os.path.join(iojs_targz_dir, 'deps', 'zlib')
  DIST_ZLIB_DIR = os.path.join(DIST_INC_DIR, 'zlib')
  os.makedirs(DIST_ZLIB_DIR)
  for inc_file in glob.glob(os.path.join(SRC_ZLIB_DIR, '*.h')):
    shutil.copy2(os.path.join(SRC_ZLIB_DIR, inc_file), DIST_ZLIB_DIR)
	
  # HTTP Parser
  SRC_HTTP_DIR = os.path.join(iojs_targz_dir, 'deps', 'http_parser')
  DIST_HTTP_DIR = os.path.join(DIST_INC_DIR, 'http_parser')
  os.makedirs(DIST_HTTP_DIR)
  for inc_file in glob.glob(os.path.join(SRC_HTTP_DIR, '*.h')):
    shutil.copy2(os.path.join(SRC_HTTP_DIR, inc_file), DIST_HTTP_DIR)	
  
  # NaN headers
  SRC_NAN_DIR = os.path.join(SOURCE_ROOT, 'eikon-3rdparty-dist', 'includes', 'nan')	
  DIST_NAN_DIR = os.path.join(DIST_INC_DIR, 'nan')
  os.makedirs(DIST_NAN_DIR)
  for inc_file in glob.glob(os.path.join(SRC_NAN_DIR, '*.h')):
    shutil.copy2(os.path.join(SRC_NAN_DIR, inc_file), DIST_NAN_DIR)

  # Clean-up
  rm_rf(iojs_targz_dir)

  
def create_version():
  with open(os.path.join(EIKON_3RDPARTY_DIST_DIR, 'version.txt'), 'w') as version_file:
    version_file.write(ELECTRON_VERSION)

	
def create_zip():

  shutil.make_archive(os.path.join(SOURCE_ROOT, 'eikon-3rdparty-dist', 'out', 'electron', ELECTRON_VERSION), 'zip', EIKON_3RDPARTY_DIST_DIR)

  
def upload_to_azure():
  
  subprocess.call(os.path.join(SOURCE_ROOT, 'eikon-3rdparty-dist', 'upload3rdparties.exe') + ' -i ' + os.path.join(SOURCE_ROOT, 'eikon-3rdparty-dist', 'out')  + ' -g')
  
if __name__ == '__main__':
  sys.exit(main())
