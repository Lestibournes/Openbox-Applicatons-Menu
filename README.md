# Openbox Applications Menu
Generate applications pipemenu for Openbox

You can choose whether to execute the script each time the menu is openend, when you log in, periodically with a cron job, or you manually whenever you install or uninstall an application, change the config file, or install or uninstall a theme.

Install with:
make install

Launch with:
obam

To use it as your menu make your root-menu execute obam, or copy menu.xml to ~/.config/openbox.

Requires pyxdg.
Some icon themes may only work with Python 2.7.

Explanation of the config file:

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

If you wish to add custom menu entries befor or after the applications menu, you can do so by editing the files "header" and "footer" in the config folder, which by default should be ~/.config/obam.

The XML pipemenu will be printed to standard output. A config file is not necessary, but if you with to customize the menu you may do so by editing config.json in the config folder.