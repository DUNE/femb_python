import pkg_resources
import os

PKGNAME="femb_python"
PKGCONFIGPREFIX = "configuration"
VARNAME="FEMB_CONFIG"

def get_env_config_file():
    if not VARNAME in os.environ:
        raise Exception("Environment variable '{}' not found. Standard options are: {}".format(VARNAME,get_standard_configurations()))
    config_name = os.environ[VARNAME]
    print("Using configuration environment var {}={}".format(VARNAME,config_name))
    return config_file_finder(config_name)

def config_file_finder(requestedFilename):
    file_exists = os.path.exists(requestedFilename)
    file_isfile = os.path.isfile(requestedFilename)
    if file_exists and file_isfile:
        return requestedFilename
    elif file_exists and not file_isfile:
        raise Exception("Configuration file points to directory. Requested config: {}".format(requestedFilename))
    pkgFileName = os.path.join(PKGCONFIGPREFIX,requestedFilename)
    res_exists = pkg_resources.resource_exists(PKGNAME,pkgFileName)
    res_isdir = pkg_resources.resource_isdir(PKGNAME,pkgFileName)
    if res_exists and not res_isdir:
        filename = pkg_resources.resource_filename(PKGNAME,pkgFileName)
        return filename
    elif res_exists and res_isdir:
        raise Exception("Configuration file points to directory. Requested config: {}, equivalent path: {}".format(requestedFilename,pkgFileName))
    else:
        raise Exception("Configuration file not found. Requested config: {}. Standard configurations are: {}".format(requestedFilename,get_standard_configurations()))

def get_standard_configurations():
    standard_file_list = pkg_resources.resource_listdir(PKGNAME,PKGCONFIGPREFIX)
    standard_file_list = [i for i in standard_file_list if os.path.splitext(i)[1]==".ini"]
    return standard_file_list
