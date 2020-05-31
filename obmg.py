# MIT License

# Copyright (c) 2020 Yitzchak Schwarz

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import glob
import json
import re
import os
from gi.repository import Gio
import sys

def setIcon(item):
	if os.path.isfile(item["icon"]["name"]):
		item["icon"]["selected"] = item["icon"]["name"]
	else:
		for theme_name in theme_names:
			for folder in theme_folders[theme_name]:
				item["icon"]["files"] = [os.path.join(dp, f) for dp, dn, filenames in os.walk(folder) for f in filenames if os.path.splitext(f)[0] == item["icon"]["name"] and os.path.splitext(f)[1] in extensions]
				if item["icon"]["files"]:
					break
			if len(item["icon"]["files"]) > 0:
					break
		
		if not item["icon"]["files"]:
			for folder in [value.strip().replace("~", home) for value in config["global"]["icons"]["folders"].split(",") if value]:
				icon_files = glob.glob(os.path.join(folder, "*"))

				if icon_files:
					for file in icon_files:
						if os.path.isfile(file) and os.path.basename(file) == item["icon"]["name"] or (os.path.splitext(os.path.basename(file))[0] == item["icon"]["name"] and os.path.splitext(os.path.basename(file))[1] in extensions):
							item["icon"]["selected"] = file
							break
		
		# Select the icon file to use:
		item["icon"]["scalable"] = [file for file in item["icon"]["files"] if scalable_icon_size.search(file)]
		item["icon"]["files"] = [file for file in item["icon"]["files"] if fixed_icon_size.search(file)]

		reverse = False
		if config["global"]["icons"]["preference"] == "bigger": reverse = True

		item["icon"]["files"] = sorted(item["icon"]["files"], key=(lambda file: int(fixed_icon_size.search(file).group(2))), reverse=reverse)
		
		temp = None
		
		for file in item["icon"]["files"]:
			if not reverse:
				if int(fixed_icon_size.search(file).group(2)) >= int(config["global"]["icons"]["minimum"]):
					item["icon"]["selected"] = file
					break
				else:
					temp = file
			elif reverse:
				if int(fixed_icon_size.search(file).group(2)) <= int(config["global"]["icons"]["maximum"]):
					item["icon"]["selected"] = file
					break
				else:
					temp = file
		if not item["icon"]["selected"] and temp:
			item["icon"]["selected"] = temp

		elif not item["icon"]["selected"] and item["icon"]["scalable"]: item["icon"]["selected"] = item["icon"]["scalable"][0]

#initializations:
home = os.path.expanduser("~")

#the config file:
config_filename = sys.argv[1].replace("~", home)
config = json.loads(open(config_filename, "r").read())

#language preferences:
langs = config["global"]["language"].split(",")

for i in range(len(langs)):
	langs[i] = langs[i].lower().strip()

#which desktop environment-exlusives to include:
environments = [ environment.lower().strip() for environment in config["global"]["environments"].split(",") if environment]

#icons parameters:
min = int(config["global"]["icons"]["minimum"])
max = int(config["global"]["icons"]["maximum"])
fixed_icon_size = re.compile(r'\/(.+)\/(\d+)(?:x\d+(?:@2x)?)?(?:\/(?:.*))*\/(.*)\.(.+)')
scalable_icon_size = re.compile(r'\/(.+)\/scalable\/(.*)\.(.+)')
extensions = [".png", ".svg", ".xpm"] # filename extensions for icon files

# Icon Themes:
theme_names = []
theme_folders = {}

regex = re.compile(r'^Inherits\s*=\s*(.+(?:.+))')
names = [name.strip() for name in config["global"]["icons"]["theme"].split(",") if name]
paths = [value.strip().replace("~", home) for value in config["global"]["icons"]["themes"].split(",") if value]
themes_top = [os.path.join(path.strip().replace("~", home), name) for name in names for path in paths]

for item in themes_top:
	themes = []
	themes.append(item)

	while len(themes) > 0:
		theme = themes.pop(0)
		if (os.path.exists(os.path.join(theme, "index.theme"))):
			theme_name = os.path.basename(theme)

			if theme_name not in theme_names:
				theme_names.append(theme_name)
				theme_folders[theme_name] = []

			if theme not in theme_folders[theme_name]:
				theme_folders[theme_name].append(theme)

			for line in open(os.path.join(theme, "index.theme"), "r").read().splitlines():
				match = regex.search(line.rstrip())

				if (match):
					themes += [os.path.join(os.path.dirname(theme), t.strip()) for t in match.group(1).split(",")]
					break

#getting all the .desktop files:
if config["global"]["sources"]["launchers"]:
	dirs = config["global"]["sources"]["launchers"].split(",")

launcher_files = []

for dir in dirs:
	launcher_files += glob.glob(dir.strip().replace("~", home) + "/*.desktop")

#getting .desktop files from /snap:
if config["global"]["sources"]["snap"]:
	launcher_files += glob.glob(config["global"]["sources"]["snap"] +  "/*/current/meta/gui/*.desktop")

#flatpak:
if config["global"]["sources"]["flatpak"]:
	launcher_files += glob.glob(config["global"]["sources"]["flatpak"] + "/exports/share/applications/*.desktop")

	for folder in glob.glob(config["global"]["sources"]["flatpak"] + "/exports/share/icons/*"):
		theme_name = os.path.basename(folder)

		if theme_name not in theme_names:
			theme_names.append(theme_name)
			theme_folders[theme_name] = []

		if folder not in theme_folders[theme_name]:
			theme_folders[theme_name].append(folder)

#construct the menus:
menus = {}

for menu in config["menus"]:
	menus[menu] = {
		"applications": [],
		"categories": [],
		"exclusions": [],
		"icon": {
				"name": config["menus"][menu]["icon"], # the name of the icon
				"selected": "", # the path that will be used
				"files": {}, # a dictionary mapping icon sizes to the paths where the icons can be found
				"scalable": ""
			},
	}

	# Categories:
	menus[menu]["categories"] = [value.lower().strip() for value in config["menus"][menu]["categories"].split(",") if value]

	# Exclusions:
	menus[menu]["exclusions"] = [value.lower().strip() for value in config["menus"][menu]["exclude"].split(",") if value]

menus["Other"] = {
	"applications": [],
	"categories": [],
	"exclusions": [],
	"icon": {
			"name": "applications-other", # the name of the icon
			"selected": "", # the path that will be used
			"files": {}, # a dictionary mapping icon sizes to the paths where the icons can be found
			"scalable": ""
		},
}

# Set the menu icons:
for menu in menus:
	setIcon(menus[menu])

old_applications = {}

if config["global"]["files"]["cache"]:
	if "--rebuild" not in sys.argv:
		cache_source = open(config["global"]["files"]["cache"].strip().replace("~", home), 'r')
		cache_old = cache_source.read()

		if cache_source.readable() and len(cache_old) > 2:
			old_applications = json.loads(cache_old)

applications = {}
update_cache = False
executables = []

# Reading all the .desktop files into memory:
for file in launcher_files:
	if os.path.isfile(file) and file not in old_applications:
		update_cache = True
		application = {
			"name": "", # the name to be displayed out of all the names
			"names": {
				"default": ""
			}, # a dictionary mapping language codes to name strings. The default name will be stored in "default"
			"icon": {
				"name": "", # the name of the icon
				"selected": "", # the path that will be used
				"files": {}, # a dictionary mapping icon sizes to the paths where the icons can be found
				"scalable": "" # a scalable icon
			},
			"exec": "", # The command to be executed when launching the app
			"visible": True, # whether the app is to be displayed or not. Depends on isShown and ShowOnlyIn.
			"environments": [], # the different environments this app is to appear in. If empty, it will appear in all environments. This depends on ShowOnlyIn
			"categories": [], # the different application categories this app belongs to
			"menus": [], # the different application menus this app belongs to
		}

		reading_names = False # whether we are in the name area.
		
		for line in open(file, "r").read().splitlines():
			line = line.strip()

			if line == "[Desktop Entry]":
				reading_names = True
			elif re.match(r'\[.+\]', line) is not None:
				reading_names = False
			
			if reading_names:
				# Hidden:
				if line == "NoDisplay=true": application["visible"] = False

				# Categories:
				match = re.compile(r'^Categories\s*=\s*(.+)').search(line)
				if match: application["categories"] = [value.lower().strip() for value in match.group(1).split(";") if value]

				# Environments:
				match = re.compile(r'^OnlyShowIn\s*=\s*(.+)').search(line)
				if match: application["environments"] = [value.lower().strip() for value in match.group(1).split(";") if value]

				# Excecutable:
				match = re.compile(r'^Exec=(.*)').search(line)
				if match: application["exec"] = match.group(1).replace("%u", "").replace("%U", "").replace("%f", "").replace("%F", "").strip()

				# Icon:
				match = re.compile(r'^Icon=(.+)').search(line)
				if match: application["icon"]["name"] = match.group(1)

				# Names:
				match = re.compile(r'^Name(?:\[([a-zA-Z][a-zA-Z])(?:_([a-zA-Z][a-zA-Z]))?\])?=(.*)').search(line)
				if (match):
					language = None
					country = None
					name = None

					if (match.group(1) is not None): language = match.group(1).lower()
					if (match.group(2) is not None): country = match.group(2).lower()
					if (match.group(3) is not None): name = match.group(3)
					
					if language is not None:
						if country is not None and language + "_" + country in langs:
							application["names"][language + "_" + country] = name
						elif language in langs:
							application["names"][language] = name
						else: # Do I really need this?
							for lang in langs:
								if lang.startswith(language):
									application["names"][language] = name
					else:
						application["names"]["default"] = name
		
		# Prevent duplication:
		if application["exec"] in executables: application["visible"] = False
		if application["exec"] not in executables: executables.append(application["exec"])

		# Select the name:
		for lang in langs:
			if lang.startswith("en"):
				application["name"] = application["names"]["default"]
				break
			elif lang in application["names"]:
				application["name"] = application["names"][lang]
				break

		if not application["name"]: application["name"] = application["names"]["default"]

		# Check the environment:
		if application["environments"] and application["visible"]:
			application["visible"] = False

			for environment in application["environments"]:
				if environment in environments:
					application["visible"] = True

		# Set the icon:
		# For snaps:
		match = re.compile(r'(\/snap\/.+\/current)\/meta\/gui\/.+\.desktop').search(file)
		if match:
			application["icon"]["name"] = application["icon"]["name"].replace("${SNAP}", match.group(1))

		# Get the icon file paths
		setIcon(application)
		
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

if "sorting" in config["global"] and config["global"]["sorting"] == "ascending".lower():
	sort = True
elif "sorting" in config["global"] and config["global"]["sorting"] == "descending".lower():
	sort = True
	reverse = True

output = '<?xml version="1.0" encoding="UTF-8" ?>\n<openbox_pipe_menu xmlns="http://openbox.org/"  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  xsi:schemaLocation="http://openbox.org/">\n\n'

if config["global"]["files"]["header"]:
	output += open(config["global"]["files"]["header"].strip().replace("~", home), "r").read()

if sort:
	for menu in sorted(menus, key=lambda menu: menu, reverse=reverse):
		if len(menus[menu]["applications"]) > 0:
			output +='<menu id="openbox-' + menu + '" label="' + menu + '" icon="' + menus[menu]["icon"]["selected"] + '">\n'

			for app in sorted(menus[menu]["applications"], key=lambda a: a["name"], reverse=reverse):
				output += '\t<item label="' + app["name"] + '" icon="' + app["icon"]["selected"] + '">\n'
				output += '\t\t<action name="Execute"><command><![CDATA[' + app["exec"] + ']]></command></action>\n'
				output += '\t</item>\n'

			output += '</menu>\n'
else:
	for menu in menus:
		if len(menus[menu]["applications"]) > 0:
			output +='<menu id="openbox-' + menu + '" label="' + menu + '" icon="' + menus[menu]["icon"]["selected"] + '">\n'

			for app in menus[menu]["applications"]:
				output += '\t<item label="' + app["name"] + '" icon="' + app["icon"]["selected"] + '">\n'
				output += '\t\t<action name="Execute"><command><![CDATA[' + app["exec"] + ']]></command></action>\n'
				output += '\t</item>\n'

			output += '</menu>\n'

if config["global"]["files"]["footer"]:
	output += open(config["global"]["files"]["footer"].strip().replace("~", home), "r").read()

output += '</openbox_pipe_menu>'

if config["global"]["files"]["output"]:
	open(config["global"]["files"]["output"].strip().replace("~", home), "w").write(output.replace("&", "&amp;"))

else:
	print(output)

if config["global"]["files"]["cache"] and update_cache:
	json.dump(applications, open(config["global"]["files"]["cache"].strip().replace("~", home), 'w'), indent="\t")