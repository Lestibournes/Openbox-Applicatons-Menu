# MIT License

# Copyright (c) 2020 Yitzchak Schwarz

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from xdg.IconTheme import getIconPath
from xdg.DesktopEntry import DesktopEntry
import glob
import json
import re
import os
from gi.repository import Gio
import sys

def getIcon(icon_name):
	if icon_name:
		for theme_name in config["icons"]:
			try:
				icon_file = getIconPath(icon_name, theme=theme_name.strip())
				if icon_file: return icon_file
			except TypeError: pass
		try:
			icon_file = getIconPath(icon_name)
			if icon_file: return icon_file
		except TypeError: pass

	return ""

#initializations:
home = os.path.expanduser("~")

#the config file:
config_filename = sys.argv[1].replace("~", home)
config = json.loads(open(config_filename, "r").read())

if not config["icons"]:
	# gsettings get org.gnome.desktop.interface icon-theme
	config["icons"] = [Gio.Settings.new("org.gnome.desktop.interface").get_string("icon-theme")]

#which desktop environment-exlusives to include:
environments = [ environment.lower().strip() for environment in config["environments"].split(",") if environment]

#getting all the .desktop files:
if config["sources"]["launchers"]: dirs = [value.strip() for value in config["sources"]["launchers"] if value]

launcher_files = []

for dir in dirs: launcher_files += glob.glob(dir.strip().replace("~", home) + "/*.desktop")

#getting .desktop files from /snap:
if config["sources"]["snap"]: launcher_files += glob.glob(config["sources"]["snap"] +  "/*/current/meta/gui/*.desktop")

#flatpak:
if config["sources"]["flatpak"]: launcher_files += glob.glob(config["sources"]["flatpak"] + "/exports/share/applications/*.desktop")

#construct the menus:
menus = {}

for menu in config["menus"]:
	menus[menu] = {
		"applications": [],
		"categories": [],
		"exclusions": [],
		"icon": getIcon(config["menus"][menu]["icon"])
	}

	# Categories:
	menus[menu]["categories"] = [value.lower().strip() for value in config["menus"][menu]["categories"] if value]

	# Exclusions:
	menus[menu]["exclusions"] = [value.lower().strip() for value in config["menus"][menu]["exclude"] if value]

menus["Other"] = {
	"applications": [],
	"categories": [],
	"exclusions": [],
	"icon": getIcon("applications-other")
}

old_applications = {}

if config["files"]["cache"]:
	if "--rebuild" not in sys.argv:
		cache_source = open(config["files"]["cache"].strip().replace("~", home), 'r')
		cache_old = cache_source.read()

		if cache_source.readable() and len(cache_old) > 2:
			old_applications = json.loads(cache_old)

applications = {}
update_cache = False
executables = []

# Reading all the .desktop files into memory:
for file in launcher_files:
	if os.path.isfile(file) and file not in old_applications:
		desktop_file = DesktopEntry(file)

		update_cache = True
		application = {
			"name": desktop_file.getName(), # the name to be displayed out of all the names
			"icon": {
				"name": desktop_file.getIcon(), # the name of the icon
				"selected": "", # the path that will be used
			},
			"exec": desktop_file.getExec(), # The command to be executed when launching the app
			"visible": not desktop_file.getHidden() and not desktop_file.getNoDisplay(), # whether the app is to be displayed or not. Depends on isShown and ShowOnlyIn.
			"environments": [value.lower() for value in desktop_file.getOnlyShowIn() if value], # the different environments this app is to appear in. If empty, it will appear in all environments. This depends on ShowOnlyIn
			"categories": [value.lower() for value in desktop_file.getCategories() if value], # the different application categories this app belongs to
			"menus": [], # the different application menus this app belongs to
		}

		application["exec"] = application["exec"].replace("%u", "").replace("%U", "").replace("%f", "").replace("%F", "").strip()

		# Set the icon name for snap applications:
		match = re.compile(r'(\/snap\/.+\/current)\/meta\/gui\/.+\.desktop').search(file)
		if match: application["icon"]["name"] = application["icon"]["name"].replace("${SNAP}", match.group(1))

		# Get the icon file paths
		application["icon"]["selected"] = getIcon(application["icon"]["name"])
		
		# Prevent duplication:
		if application["exec"] in executables: application["visible"] = False
		if application["exec"] not in executables: executables.append(application["exec"])
		
		# Check the environment:
		if application["environments"] and application["visible"]:
			application["visible"] = False

			for environment in application["environments"]:
				if environment in environments:
					application["visible"] = True
		
		applications[file] = application

	elif file in old_applications:
		applications[file] = old_applications[file]

# Add to menus:
for application in applications:
	if applications[application]["visible"] and applications[application]["categories"]:
		for menu in config["menus"]:
			for category in applications[application]["categories"]:
				if category in menus[menu]["exclusions"]: break
				if category in menus[menu]["categories"]:
					menus[menu]["applications"].append(applications[application])
					applications[application]["menus"].append(menu)
					break
	elif applications[application]["visible"]:
		menus["Other"]["applications"].append(applications[application])
		applications[application]["menus"].append("Other")

# Create the xml:
sort = False
reverse = False

if "sorting" in config and config["sorting"] == "ascending".lower():
	sort = True
elif "sorting" in config and config["sorting"] == "descending".lower():
	sort = True
	reverse = True

output = '<?xml version="1.0" encoding="UTF-8" ?>\n<openbox_pipe_menu xmlns="http://openbox.org/"  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  xsi:schemaLocation="http://openbox.org/">\n\n'

if config["files"]["header"]:
	output += open(config["files"]["header"].strip().replace("~", home), "r").read()

if sort:
	for menu in sorted(menus, key=lambda menu: menu, reverse=reverse):
		if len(menus[menu]["applications"]) > 0:
			output +='<menu id="openbox-' + menu + '" label="' + menu + '" icon="' + menus[menu]["icon"] + '">\n'
			
			for app in sorted(menus[menu]["applications"], key=lambda a: a["name"], reverse=reverse):
				output += '\t<item label="' + app["name"] + '" icon="' + app["icon"]["selected"] + '">\n'
				output += '\t\t<action name="Execute"><command><![CDATA[' + app["exec"] + ']]></command></action>\n'
				output += '\t</item>\n'

			output += '</menu>\n'
else:
	for menu in menus:
		if len(menus[menu]["applications"]) > 0:
			output +='<menu id="openbox-' + menu + '" label="' + menu + '" icon="' + menus[menu]["icon"] + '">\n'

			for app in menus[menu]["applications"]:
				output += '\t<item label="' + app["name"] + '" icon="' + app["icon"]["selected"] + '">\n'
				output += '\t\t<action name="Execute"><command><![CDATA[' + app["exec"] + ']]></command></action>\n'
				output += '\t</item>\n'

			output += '</menu>\n'

if config["files"]["footer"]:
	output += open(config["files"]["footer"].strip().replace("~", home), "r").read()

output += '</openbox_pipe_menu>'

if config["files"]["output"]:
	open(config["files"]["output"].strip().replace("~", home), "w").write(output.replace("&", "&amp;"))

else:
	print(output)

if config["files"]["cache"] and update_cache:
	json.dump(applications, open(config["files"]["cache"].strip().replace("~", home), 'w'), indent=4)