import glob
import json
import re
import os
from gi.repository import Gio
from os.path import expanduser, isdir

#initializations:
#where to write out the xml:
home = expanduser("~")
destination_filename = home + "/.config/openbox/apps.xml"

#the config file:
config_filename = "menus.json"
config = json.loads(open(config_filename, "r").read())

#where to read the .desktop files from:
dirs = config["global"]["directories"].split(",")

#icons parameters:
min = int(config["global"]["icons"]["minimum"])
max = int(config["global"]["icons"]["maximum"])
direction = config["global"]["icons"]["direction"]

#language preferences:
langs = config["global"]["language"].split(",")

for i in range(len(langs)):
	langs[i] = langs[i].lower().strip()

#which desktop environment-exlusives to include:
environments = config["global"]["environments"].split(",")

for i in range(len(environments)):
	environments[i] = environments[i].lower().strip()

#construct the menus:
menus = {}

for menu in config["menus"]:
	menus[menu] = {
		"applications": [],
		"categories": [],
		"exclusions": [],
		"icon": {
				"name": "", # the name of the icon
				"selected": "", # the path that will be used
				"files": {} # a dictionary mapping icon sizes to the paths where the icons can be found
			},
	}

#getting all the .desktop files:
files = []

for dir in dirs:
	dir = dir.strip().rstrip("/")
	files += glob.glob(dir + "/**/*.desktop", recursive=True)

# Reading all the .desktop files into memory:
for file in files:
	if not isdir(file):
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
			if not application["visible"]: break

			line = line.strip()

			if line == "[Desktop Entry]":
				reading_names = True
			elif re.match(r'\[.+\]', line) is not None:
				reading_names = False
			
			# Categories:
			match = re.compile(r'Categories\s*=\s*(.+;(?:.+))').search(line)
			if match: application["categories"] = [value.lower().strip() for value in match.group(1).split(";") if value]

			# Environments:
			match = re.compile(r'OnlyShowIn\s*=\s*(.+;(?:.+))').search(line)
			if match: application["environments"] = [value.lower().strip() for value in match.group(1).split(";") if value]

			# Excecutable:
			match = re.compile(r'Exec=(.*)').search(line)
			if match: application["exec"] = match.group(1)

			# Icon:
			match = re.compile(r'Icon=(.+)').search(line)
			if match: application["icon"]["name"] = match.group(1)

			# Names:
			if reading_names:
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
			# Hidden:
			if line == "NoDisplay=true":
				application["visible"] = False

		if not application["visible"]: continue

		# Select the name:
		for lang in langs:
			if lang in application["names"]:
				application["name"] = application["names"][lang]

		if not application["name"]: application["name"] = application["names"]["default"]

		# Check the environment:
		if application["environments"]:
			application["visible"] = False

			for environment in application["environments"]:
				if environment in environments:
					application["visible"] = True

		if not application["visible"]: continue

		# Get the icon paths:
		fixed_icon_size = re.compile(r'\/usr\/share\/icons\/(.+)\/(\d+)(?:x\d+(?:@2x)?)?(?:\/(?:.*))*\/(.*)\.(.+)')
		scalable_icon_size = re.compile(r'\/usr\/share\/icons\/(.+)\/scalable\/(.*)\.(.+)')

		# Get the icon file paths
		extensions = [".png", ".svg", ".xpm"]

		system_icon_themes = "/usr/share/icons/"
		icon_folders = ["/usr/share/icons/", "/usr/share/pixmaps/"]

		regex = re.compile(r'Inherits\s*=\s*(.+,(?:.+))')
		themes = [system_icon_themes + config["global"]["theme"]]
		
		while len(themes) > 0:
			theme = themes.pop(0)

			extensions = [".png", ".svg", ".xpm"]
			application["icon"]["files"] = [os.path.join(dp, f) for dp, dn, filenames in os.walk(theme) for f in filenames if os.path.splitext(f)[0] == application["icon"]["name"] and os.path.splitext(f)[1] in extensions]

			if application["icon"]["files"]: break

			for line in open(theme + "/index.theme", "r").read().splitlines():
				match = regex.search(line.rstrip())

				if (match):
					themes += [system_icon_themes + t.strip() for t in match.group(1).split(",")]
					break
		
		for folder in icon_folders:
			if not application["icon"]["files"]:
				files = glob.glob(folder + "*")
				
				if files:
					for file in files:
						if not isdir(file) and  os.path.splitext(file)[1] in extensions:
							application["icon"]["files"] = file
							break
		
		# Select the icon file to use:

		application["icon"]["scalable"] = [file for file in application["icon"]["files"] if scalable_icon_size.search(file)]
		application["icon"]["files"] = [file for file in application["icon"]["files"] if fixed_icon_size.search(file)]

		reverse = False
		if config["global"]["icons"]["preference"] == "bigger": reverse = True

		application["icon"]["files"] = sorted(application["icon"]["files"], key=(lambda file: int(fixed_icon_size.search(file).group(2))), reverse=reverse)
		
		for file in application["icon"]["files"]:
			if not reverse and int(fixed_icon_size.search(file).group(2)) >= int(config["global"]["icons"]["minimum"]):
				application["icon"]["selected"] = file
				break
			elif reverse and int(fixed_icon_size.search(file).group(2)) <= int(config["global"]["icons"]["maximum"]):
				application["icon"]["selected"] = file
				break
		
		if not application["icon"]["selected"]: application["icon"]["selected"] = application["icon"]["scalable"]

		# Add to menus:
		results = []
		for menu in config["menus"]:
			menus[menu]["categories"] = [value.lower().strip() for value in config["menus"][menu]["categories"].split(",") if value]
			menus[menu]["exclusions"] = [value.lower().strip() for value in config["menus"][menu]["exclude"].split(",") if value]
			
			for category in application["categories"]:
				if category in menus[menu]["exclusions"]: break
				if category in menus[menu]["categories"]:
					menus[menu]["applications"].append(application)
					application["menus"].append(menu)

output = '<?xml version="1.0" encoding="UTF-8" ?>\n<openbox_pipe_menu xmlns="http://openbox.org/"  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  xsi:schemaLocation="http://openbox.org/" >\n\n'

for menu in menus:
	output +='<menu id="openbox-' + menu + '" label="' + menu + '" icon="' + menus[menu]["icon"]["selected"] + '">\n'

	for app in menus[menu]:
		output += '\t<item label="Archive Manager" icon="/usr/share/icons/Faenza/apps/32/file-roller.png">\n'
		output += '\t\t<action name="Execute"><command><![CDATA[file-roller]]></command></action>\n'
		output += '\t</item>\n'

	output += '</menu>\n'
output += '</openbox_pipe_menu>'

print(output)