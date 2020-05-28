# Openbox Menu Generator
Generate applications pipemenu for Openbox

The script takes 2 parameters:
* A json config file. A sample json config file is provided.
* The destination files= where the output will be written (optional). If this parameter is not provided, the output will be written to standard output.
Since it can take a few seconds, it is recommended not to execute the script each time the menu is openend. Instead, you can have the menu refresh when you log in, periodically with a cron job, or you can refresh it manually whenever you install or uninstall an application.

For example, launch with:
python obamg.py menus.json menu.xml

This script hasn't been thoroughly tested and there are many improvements that can be made.

Explanation of the config file:
* global - the variables affecting the the script as a whole.
  * directories - a comma-separated list of where to look for .desktop files
  * language - a comma-separated list of languages to use for the menu, in descending order of preference. Can be either language_country, or just language. Examples: es_cl, en_ca, he, ru
  * environments - a comma-separated list of the values that appear in ShowOnlyIn fields of .desktop files. Leave empty to ignore ShowOnlyIn. Otherwise, put in the values of the environements you want to impersonate so that hidden launchers that only show in a specific environment will appear. However, if you specify even one environment then only the environments you specify will have their exclusive launchers show.
  * sorting - The direction in which to sort the menus and launchers. can be ascending or descending. Leave empty to not sort.
  * theme - the icon theme you want to use for the icons.
  * icons - the parameters for the icons
    * minimum - smallest icon size. Only has an effect when preference is smallest.
    * maximum - biggest icon size. Only has an effect when preference is biggest.
      preference - whether icons will be as big as possible with maximum as the largest size or as small as possible with minimum as the smallest size. If no icon is found within the parameters then the closest size to the preferred size will be used.
    * themes - a comma-separated list of the the base directories for the icon themes. For example: ~/.icons,/usr/share/icons
    * folders - folders where icons can be found. These folders will be searched non-recursively, and only if an icon hasn't been found in the theme.
* menus - a list of submenus of the applicaitons menu
  * [name] - the name of the menu
    * icon - the name of the icon to be used from the theme
    * categories - each .desktop file has categories. This lists which categories will have their launchers included in this menu
    * exclude - which categories will not have their applications included in this menu, even if those launchers should be otherwise be included.
