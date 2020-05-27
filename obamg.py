import glob
import json
import re
import os
from gi.repository import Gio
import sys

#initializations:
#where to write out the xml:
home = os.path.expanduser("~")
destination_filename = home + "/.config/openbox/apps.xml"

#the config file:
config_filename = sys.argv[1]
config = json.loads(open(config_filename, "r").read())

#where to read the .desktop files from:
dirs = config["global"]["directories"].split(",")

#icons parameters:
min = int(config["global"]["icons"]["minimum"])
max = int(config["global"]["icons"]["maximum"])
fixed_icon_size = re.compile(r'\/(.+)\/(\d+)(?:x\d+(?:@2x)?)?(?:\/(?:.*))*\/(.*)\.(.+)')
scalable_icon_size = re.compile(r'\/(.+)\/scalable\/(.*)\.(.+)')
extensions = [".png", ".svg", ".xpm"] # filename extensions for icon files

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

	# Set the menu icon:
	if os.path.isfile(menus[menu]["icon"]["name"]):
		menus[menu]["icon"]["selected"] = menus[menu]["icon"]["name"]
	else:
		regex = re.compile(r'Inherits\s*=\s*(.+,(?:.+))')
		themes = [os.path.join(value.replace("~", home), config["global"]["theme"]) for value in config["global"]["icons"]["themes"].split(",") if value]
		while len(themes) > 0:
			theme = themes.pop(0)

			extensions = [".png", ".svg", ".xpm"]
			menus[menu]["icon"]["files"] = [os.path.join(dp, f) for dp, dn, filenames in os.walk(theme) for f in filenames if os.path.splitext(f)[0] == menus[menu]["icon"]["name"] and os.path.splitext(f)[1] in extensions]

			if menus[menu]["icon"]["files"]: break

			for line in open(theme + "/index.theme", "r").read().splitlines():
				match = regex.search(line.rstrip())

				if (match):
					themes += [os.path.join(os.path.dirname(theme), t.strip()) for t in match.group(1).split(",")]
					break
		
		if not menus[menu]["icon"]["files"]:
			for folder in config["global"]["icons"]["folders"]:
				files = glob.glob(folder + "*")

				if files:
					for file in files:
						if os.path.isfile(file) and os.path.basename(file) == menus[menu]["icon"]["name"] or (os.path.splitext(os.path.basename(file))[0] == menus[menu]["icon"]["name"] and os.path.splitext(os.path.basename(file))[1] in extensions):
							menus[menu]["icon"]["selected"] = file
							break
		
		# Select the icon file to use:
		menus[menu]["icon"]["scalable"] = [file for file in menus[menu]["icon"]["files"] if scalable_icon_size.search(file)]
		menus[menu]["icon"]["files"] = [file for file in menus[menu]["icon"]["files"] if fixed_icon_size.search(file)]

		reverse = False
		if config["global"]["icons"]["preference"] == "bigger": reverse = True

		menus[menu]["icon"]["files"] = sorted(menus[menu]["icon"]["files"], key=(lambda file: int(fixed_icon_size.search(file).group(2))), reverse=reverse)
		
		temp = None
		
		for file in menus[menu]["icon"]["files"]:
			if not reverse:
				if int(fixed_icon_size.search(file).group(2)) >= int(config["global"]["icons"]["minimum"]):
					menus[menu]["icon"]["selected"] = file
					break
				else:
					temp = file
			elif reverse:
				if int(fixed_icon_size.search(file).group(2)) <= int(config["global"]["icons"]["maximum"]):
					menus[menu]["icon"]["selected"] = file
					break
				else:
					temp = file
		if not menus[menu]["icon"]["selected"] and temp:
			menus[menu]["icon"]["selected"] = temp

		elif not menus[menu]["icon"]["selected"] and menus[menu]["icon"]["scalable"]: menus[menu]["icon"]["selected"] = menus[menu]["icon"]["scalable"][0]
		
#getting all the .desktop files:
files = []

for dir in dirs:
	dir = dir.strip().rstrip("/")
	files += glob.glob(dir + "/**/*.desktop", recursive=True)

# Reading all the .desktop files into memory:
for file in files:
	if not os.path.isdir(file):
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
			if lang.startswith("en"):
				application["name"] = application["names"]["default"]
				break
			elif lang in application["names"]:
				application["name"] = application["names"][lang]
				break

		if not application["name"]: application["name"] = application["names"]["default"]

		# Check the environment:
		if application["environments"]:
			application["visible"] = False

			for environment in application["environments"]:
				if environment in environments:
					application["visible"] = True

		if not application["visible"]: continue

		# Set the icon:
		# Get the icon file paths
		if os.path.isfile(application["icon"]["name"]):
			application["icon"]["selected"] = application["icon"]["name"]
		else:
			regex = re.compile(r'Inherits\s*=\s*(.+,(?:.+))')
			themes = [os.path.join(value.replace("~", home), config["global"]["theme"]) for value in config["global"]["icons"]["themes"].split(",") if value]
			
			while len(themes) > 0:
				theme = themes.pop(0)

				extensions = [".png", ".svg", ".xpm"]
				application["icon"]["files"] = [os.path.join(dp, f) for dp, dn, filenames in os.walk(theme) for f in filenames if os.path.splitext(f)[0] == application["icon"]["name"] and os.path.splitext(f)[1] in extensions]

				if application["icon"]["files"]: break

				for line in open(os.path.join(theme, "index.theme"), "r").read().splitlines():
					match = regex.search(line.rstrip())

					if (match):
						themes += [os.path.join(os.path.dirname(theme), t.strip()) for t in match.group(1).split(",")]
						break
			
			if not application["icon"]["files"]:
				for folder in config["global"]["icons"]["folders"]:
					files = glob.glob(folder + "*")

					if files:
						for file in files:
							if os.path.isfile(file) and os.path.basename(file) == application["icon"]["name"] or (os.path.splitext(os.path.basename(file))[0] == application["icon"]["name"] and os.path.splitext(os.path.basename(file))[1] in extensions):
								application["icon"]["selected"] = file
								break
			
			# Select the icon file to use:

			application["icon"]["scalable"] = [file for file in application["icon"]["files"] if scalable_icon_size.search(file)]
			application["icon"]["files"] = [file for file in application["icon"]["files"] if fixed_icon_size.search(file)]

			reverse = False
			if config["global"]["icons"]["preference"] == "bigger": reverse = True

			application["icon"]["files"] = sorted(application["icon"]["files"], key=(lambda file: int(fixed_icon_size.search(file).group(2))), reverse=reverse)
			
			temp = None
			
			for file in application["icon"]["files"]:
				if not reverse:
					if int(fixed_icon_size.search(file).group(2)) >= int(config["global"]["icons"]["minimum"]):
						application["icon"]["selected"] = file
						break
					else:
						temp = file
				elif reverse:
					if int(fixed_icon_size.search(file).group(2)) <= int(config["global"]["icons"]["maximum"]):
						application["icon"]["selected"] = file
						break
					else:
						temp = file
			if not application["icon"]["selected"] and temp:
				application["icon"]["selected"] = temp

			elif not application["icon"]["selected"] and application["icon"]["scalable"]: application["icon"]["selected"] = application["icon"]["scalable"][0]

		# Add to menus:
		for menu in config["menus"]:
			for category in application["categories"]:
				if category in menus[menu]["exclusions"]: break
				if category in menus[menu]["categories"]:
					menus[menu]["applications"].append(application)
					application["menus"].append(menu)

output = '<?xml version="1.0" encoding="UTF-8" ?>\n<openbox_pipe_menu xmlns="http://openbox.org/"  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  xsi:schemaLocation="http://openbox.org/" >\n\n'

for menu in menus:
	output +='<menu id="openbox-' + menu + '" label="' + menu + '" icon="' + menus[menu]["icon"]["selected"] + '">\n'

	for app in menus[menu]["applications"]:
		output += '\t<item label="' + app["name"] + '" icon="' + app["icon"]["selected"] + '">\n'
		output += '\t\t<action name="Execute"><command><![CDATA[' + app["exec"] + ']]></command></action>\n'
		output += '\t</item>\n'

	output += '</menu>\n'
output += '</openbox_pipe_menu>'

print(output)