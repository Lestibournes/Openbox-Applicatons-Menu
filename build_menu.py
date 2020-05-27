import glob
import json
import re
import os
from gi.repository import Gio
from os.path import expanduser, isdir

def getEnvironments(file):
	regex = re.compile(r'OnlyShowIn\s*=\s*(.+;(?:.+))')
	environments = []

	for line in open(file, "r").read().splitlines():
		match = regex.search(line.rstrip())

		if (match):
			environments = match.group(1).split(";")

			for i in range(len(environments)):
				environments[i] = environments[i].lower().strip()
			
			break
			
	environments = [value for value in environments if value]
	return environments

def isShown(file, environments):
	for line in open(file, "r").read().splitlines():
		if line == "NoDisplay=true":
			return False
	
	envs = getEnvironments(file)

	if len(envs) == 0:
		return True
	
	for env in envs:
		if env in environments:
			return True
	
	return False

def matchLanguage(language, country, langs):
	if language is not None:
		if country is not None and language + "_" + country in langs:
			return language + "_" + country
		elif language in langs:
			return language
		for lang in langs:
			if lang.startswith(language):
				return language
	return None

def getName(file, langs):
	regex = re.compile(r'^Name(?:\[([a-zA-Z][a-zA-Z])(?:_([a-zA-Z][a-zA-Z]))?\])?=(.*)')
	names = {}
	default = ""
	reading = False
	
	for line in open(file, "r").read().splitlines():
		if line == "[Desktop Entry]":
			reading = True
		elif re.match(r'\[.+\]', line) is not None:
			reading = False
		
		if reading:
			match = regex.search(line.rstrip())
			if (match):
				language = None
				country = None
				name = None

				if (match.group(1) is not None): language = match.group(1).lower()
				if (match.group(2) is not None): country = match.group(2).lower()
				if (match.group(3) is not None): name = match.group(3)
				
				matched_language = matchLanguage(language, country, name)

				if language is None:
					default = name
				elif matched_language is not None:
					names[matched_language] = name

	for lang in langs:
		if lang in names:
			return names[lang]
	return default

def getIcon(file):
	regex = re.compile(r'Icon=(.+)')

	for line in open(file, "r").read().splitlines():
		match = regex.search(line.rstrip())

		if (match):
			return match.group(1)

def getExec(file):
	regex = re.compile(r'Exec=(.*)')

	for line in open(file, "r").read().splitlines():
		match = regex.search(line.rstrip())

		if (match):
			return match.group(1)

def getCategories(file):
	regex = re.compile(r'Categories\s*=\s*(.+;(?:.+))')
	categories = []

	for line in open(file, "r").read().splitlines():
		match = regex.search(line.rstrip())

		if (match):
			categories = match.group(1).split(";")

			for i in range(len(categories)):
				categories[i] = categories[i].lower().strip()

	return [value for value in categories if value]

def getMenus(appCategories, menuConfigs):
	results = []
	for menu in menuConfigs:
		categories = menuConfigs[menu]["categories"].split(",")
		categories = [value.lower().strip() for value in categories if value]

		exclusions = menuConfigs[menu]["exclude"].split(",")
		exclusions = [value.lower().strip() for value in exclusions if value]

		add_menu = False
		
		for category in appCategories:
			if category in exclusions:
				add_menu = False
				break
			if category in categories:
				add_menu = True

		if add_menu:
			results.append(menu)
	return results

def printMenus(menus, config):
	sort = False
	method = lambda menu: menu
	reverse = False

	if config["global"]["sorting"] == "ascending".lower():
		sort = True
	elif config["global"]["sorting"] == "descending".lower():
		sort = True
		reverse = True

	if sort:
		for menu in sorted(menus, key=method, reverse=reverse):
			if len(menus[menu]) > 0:
				print()
				print(menu + ":")

				for app in sorted(menus[menu], key=method, reverse=reverse):
					pass
					print(app + ": " + str(menus[menu][app]))
	else:
		for menu in menus:
			if len(menus[menu]) > 0:
				print()
				print(menu + ":")

				for app in menus[menu]:
					pass
					print(app + ": " + str(menus[menu][app]))

def getIconFromTheme(icon, theme):
	base = "/usr/share/icons/"

	extensions = [".png", ".svg", ".xpm"]
	files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(os.path.join(base, theme)) for f in filenames if os.path.splitext(f)[0] == icon and os.path.splitext(f)[1] in extensions]

	if not files:
		regex = re.compile(r'Inherits\s*=\s*(.+,(?:.+))')
		themes = []

		for line in open(base + theme + "/index.theme", "r").read().splitlines():
			match = regex.search(line.rstrip())

			if (match):
				themes = match.group(1).split(",")

				for i in range(len(themes)):
					themes[i] = themes[i].strip()

				break

		for t in themes:
			files = getIconFromTheme(icon, t)

			if files:
				return files
		
		return None

	return files

def getIconPaths(icon):
	theme = Gio.Settings.new("org.gnome.desktop.interface").get_string("icon-theme")
	return getIconFromTheme(icon, theme)

def getIconPathBySize(icon, icons, min, max, direction):
	if icons:
		if direction == "increasing":
			size = min
		else:
			size = max
		fixed = re.compile(r'\/usr\/share\/icons\/(.+)\/(\d+)(?:x\d+(?:@2x)?)?(?:\/(?:.*))*\/(.*)\.(.+)')

		for path in icons:
			fixed_match = fixed.search(path)

			if fixed_match and fixed_match.group(2) == str(size):
				return path
		
		scalable = re.compile(r'\/usr\/share\/icons\/(.+)\/scalable\/(.*)\.(.+)')
		
		for path in icons:
			scalable_match = scalable.search(path)
			if scalable_match:
				return path
		
		if min <= max:
			if direction == "increasing":
				min += 8
			else:
				max -= 8
			
			return getIconPathBySize(icon, icons, min, max, direction)
	
	return None

def getIconFromDirectory(icon, directory):
	extensions = [".png", ".svg", ".xpm"]

	files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(directory) for f in filenames if (os.path.splitext(f)[0] == icon and os.path.splitext(f)[1] in extensions) or f == icon]
	return files

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

#getting all the .desktop files:
apps = []

for dir in dirs:
	dir = dir.strip().rstrip("/")
	apps += glob.glob(dir + "/**/*.desktop", recursive=True)

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
	menus[menu] = {}

for app in apps:
	if not isdir(app) and isShown(app, environments):
		name = getName(app, langs)
		icon = getIcon(app)
		exec = getExec(app)
		categories = getCategories(app)
		appMenus = getMenus(categories, config["menus"])

		for menu in appMenus:
			icon_path = getIconPathBySize(icon, getIconPaths(icon), min, max, direction)

			if not icon_path:
				icon_path = getIconFromDirectory(icon, "/usr/share/pixmaps/")

			if not icon_path:
				icon_path = getIconFromDirectory(icon, "/usr/share/icons/")
				if icon_path:
					icon_path = icon_path[0]

			menus[menu][name] = {
				"icon": icon_path,
				"exec": exec
			}


printMenus(menus, config)
