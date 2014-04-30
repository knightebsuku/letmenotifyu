import imp
import os
import logging
plugin_folder = os.environ['HOME']+'/.local/share/letmenotifyu/plugins/'
plugin_module = "__init__"

def get_plugins():
    plugins =[]
    list_of_plugins = os.listdir(plugin_folder)
    for i in list_of_plugins:
        location = os.path.join(plugin_folder,i)
        if not os.path.isdir(location) or not plugin_module+ ".py" in os.listdir(location):
            logging.warn("Incorrect module")
            continue
        info = imp.find_module(plugin_module,[location])
        plugins.append({"name":i,"info":info})
        logging.info(plugins)
    return plugins
