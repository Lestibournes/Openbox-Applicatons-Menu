# Openbox Applications Menu
Generate applications pipemenu for Openbox

The script takes a json config file. A sample json config file is provided.

You can choose whether to execute the script each time the menu is openend, when you log in, periodically with a cron job, or you manually whenever you install or uninstall an application, change the config file, or install or uninstall a theme.

For example, launch with:
python obamg.py menus.json

Requires pyxdg.
Some icon themes may only work with Python 2.7.

Explanation of the config file:

* static - leave out or specify it with the value of false for pipemenu. Specify it with the value of true to generate a static menu.
* id - the id of the static menu. If the manu is a pipemenu then this value is ignored. If it is missing then it will default to "root-menu".
* files - the various files to be used for input output, etc.
  * header - menus to be inserted before the applications menus.
  * footer - menus to be inserted after the applications menus.
  * output - where the output will be written (optional). If this parameter is not provided, the output will be written to standard output.
  * cache - the location of the cache file. If not specified then ~/.config/obam/cache.json will be used.
* sources - the various sources of .desktop files.
  * snap - the root directory for snap application installs.
  * flatpak - the root directory for flatpak files. This will also be used for icons for flatpak applications.
  * launchers - an array of folders containing .desktop files in a flat structure.
* environments - an array of the values that appear in ShowOnlyIn fields of .desktop files.
* sorting - The direction in which to sort the menus and launchers. can be ascending or descending. Leave empty to not sort.
* icons - an array of the icon themes you want to use for the icons, in decending order of preference. If this value is missing, it will use the GNOME icon theme.
* terminal - the command to use to launch terminal applications.
    
* menus - a list of submenus of the applicaitons menu
  * [name] - the name of the menu
    * icon - the name of the icon to be used from the theme
    * categories - an array of the categories who's applications will be included in this menu.
    * exclude - (optional) an array of categories who's applications will be excluded from this menu. This overrides inclusion.
