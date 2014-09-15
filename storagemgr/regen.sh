#!/bin/bash

rm storagemgr/storagemgr.db
manage.py syncdb --noinput
manage.py manage_root add /mnt/samba
manage.py manage_root exclude_dir "\.git"
manage.py manage_root exclude_dir "\.svn"
manage.py manage_root exclude_dir "\.cache"
manage.py manage_root exclude_dir "\.compiz"
manage.py manage_root exclude_dir "\.config"
manage.py manage_root exclude_dir "\.dbus"
manage.py manage_root exclude_dir "\.ecryptfs"
manage.py manage_root exclude_dir "\.gconf"
manage.py manage_root exclude_dir "\.gnome2"
manage.py manage_root exclude_dir "\.gnome2_private"
manage.py manage_root exclude_dir "\.gstreamer-0.10"
manage.py manage_root exclude_dir "\.java"
manage.py manage_root exclude_dir "\.kde"
manage.py manage_root exclude_dir "\.local"
manage.py manage_root exclude_dir "\.mozilla"
manage.py manage_root exclude_dir "\.mplayer"
manage.py manage_root exclude_dir "\.pki"
manage.py manage_root exclude_dir "\.Private"
manage.py manage_root exclude_dir "\.Skype"
manage.py manage_root exclude_dir "\.vim"
manage.py manage_root exclude_dir "VirtualBox VMs"
manage.py quick_scan
