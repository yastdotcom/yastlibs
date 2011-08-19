#!/usr/bin/python
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
# SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
# FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
# Yast Python CLI
#
# Version:
# 0.8 - First release
#
# 0.9 - Bugfixes
#  * Fixed issue with optional params not working properly for many commands
#  * Renamed --phoneNumber to --phone-number
#  * Added option for connecting to Yast using HTTPS
#

import argparse, time, re, datetime, io, sys

from yastlib import *

# Yast CLI
class YastCli(object):

  debug = False
  args = None
  yast = None

  # Parser 
  parsers = {}

  # Cache
  projects = None
  folders = None
  recordTypes = None

  # Runs Yast CLI
  def execute(self):
    # Parse command line arguments
    self._createParser()
    try:
      self.args = self.parsers['pars'].parse_args()
    except SystemExit as e:
      # Modify argparse return code on error
      sys.exit(YastStatus.CLI_ARGUMENT_ERROR if str(e) != '0' else 0)
      
    # Setup Yast
    self.yast = self._createYast()
    self.yast.propagateExceptions = True
    self.yast.host = self.args.host;
    self.yast.useHttps = self.args.https;

    # Execute command
    try:
      self.args.func()
    except Exception as e:
      if self.yast.getStatus() == 0:
        self.yast.status = YastStatus.CLI_EXCEPTION
      sys.stderr.write("ERROR [{0:04d}]: {1:s}\n".format(self.yast.getStatus(), e.__class__.__name__ + ": " + str(e)))
      if self.debug:
        raise
      sys.exit(self.yast.getStatus() if self.yast.getStatus() < 255 else 255)
    
  
  # Sets up and returns argument parser
  def _createParser(self):
    # Shorthand
    p = self.parsers
    p['pars'] = argparse.ArgumentParser(description="Yast Python CLI", add_help=True)
    p['cmds'] = p['pars'].add_subparsers()


    # Add standard arguments
    p['pars'].add_argument('-u', '--user', type=str, dest='user', help="Username for login")
    p['pars'].add_argument('-p', '--password', type=str, dest='password', metavar='PW',
                           help="Password for login. Supply this or hash along with username for authentication")
    p['pars'].add_argument('-x', '--hash', type=str, dest='hash', 
                           help="Hash from login. Supply this or password along with username for authentication")
    p['pars'].add_argument('-d', '--host', type=str, dest='host', default="www.yast.com",
                           help="Host to connect to. Defaults to www.yast.com")
    p['pars'].add_argument('-n', '--no-pretty', dest='pretty', action='store_false', default=True,
                           help="Disable pretty-printing of output")
    p['pars'].add_argument('-f', '--no-sort', dest='sort', action='store_false', default=True,
                           help="Disable sorting of output")
    p['pars'].add_argument('-s', '--silent', dest='silent', action='store_true', default=False,
                           help="Remove unnecessary output")
    p['pars'].add_argument('--http', dest='https', action='store_false', default=False,
                           help="Connect using http. Default")
    p['pars'].add_argument('--https', dest='https', action='store_true', default=False,
                           help="Connect using https")
    p['pars'].add_argument('-v', '--version', action='version', version="Yast Python CLI 0.8")
    p['pars'].add_argument('-a', '--all-info', dest='all_info', action='store_true', default=False,
                           help="Show all info about printed objects")
    p['pars'].add_argument('--seconds', dest='seconds', action='store_true', default=False,
                           help="Return time in seconds since 1.1.1900")
    p['pars'].add_argument('--csv', dest='csv', action='store_true', default=False,
                           help="Add comma between printed values")
    p['pars'].add_argument('--ids', dest='ids', action='store_true', default=False,
                           help="When printing parents, prefer ids over names")
    p['pars'].add_argument('--only-id', dest='only_id', action='store_true', default=False,
                           help="When printing projects/folders/records, only print their ids")
    p['pars'].add_argument('--limit', type=int, dest="limit", default=-1,
                           help="When printing projects/folders/records, limit number of printed elements to this value")
                           
        
    # login command
    p['parsLogin'] = p['cmds'].add_parser('login', help="Login and return hash that can be used with future commands")
    p['parsLogin'].set_defaults(func=self._reqLogin)


    ###
    # user command
    p['parsUser'] = p['cmds'].add_parser('user', help="Manage user(s)")
    p['subUser'] = p['parsUser'].add_subparsers()

    # userGetInfo command
    p['parsUserGetInfo'] = p['subUser'].add_parser('get-info', help="Get information about user")
    p['parsUserGetInfo'].set_defaults(func=self._reqUserGetInfo)

    # userGetSettings command
    p['parsUserGetSettings'] = p['subUser'].add_parser('get-settings', help="Get user settings")
    p['parsUserGetSettings'].set_defaults(func=self._reqUserGetSettings)

    # userSetSetting command
    p['parsUserSetSetting'] = p['subUser'].add_parser('set-setting', help="Set a user setting")
    p['parsUserSetSetting'].add_argument('key', help='Setting name')
    p['parsUserSetSetting'].add_argument('value', help='New setting value')
    p['parsUserSetSetting'].set_defaults(func=self._reqUserSetSetting)


    ###
    # add command
    p['parsAdd'] = p['cmds'].add_parser('add', help="Add data")
    p['subAdd'] = p['parsAdd'].add_subparsers()

    # Record id arguments. When specified, id is never optional and always positional
    p['argsRecordId'] = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    p['argsRecordId'].add_argument('id', help="Id of record")

    # Arguments for generic records
    p['argsRecordData'] = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    p['argsRecordData'].add_argument('project', nargs='?', help="Id or name of parent project")
    p['argsRecordData'].add_argument('--project', dest='project', help="Id or name of parent project")
    p['argsRecordData'].add_argument('startTime', nargs='?', help="Start time of record. See 'print time' command for help")
    p['argsRecordData'].add_argument('--start-time', '--from', dest='startTime', help="Start time of record. See 'print time' command for help")
    p['argsRecordData'].add_argument('endTime', nargs='?', help="End time of record. See 'print time' command for help")
    p['argsRecordData'].add_argument('--end-time', '--to', dest='endTime', help="End time of record. See 'print time' command for help")
    p['argsRecordData'].add_argument('comment', nargs='?', help="Comment associated with record")
    p['argsRecordData'].add_argument('--comment', help="Comment associated with record")
    p['argsRecordData'].add_argument('-r', '--running', dest='isRunning', action='store_true',
                                     help="Record is running")
    p['argsRecordData'].add_argument('--stopped', dest='isRunning', action='store_false',
                                     help="Record is not running")

    # Arguments for phonecall records [additional]
    p['argsRecordDataPhonecall'] = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    p['argsRecordDataPhonecall'].add_argument('phoneNumber', nargs='?', help="Phonenumber for phonecall")
    p['argsRecordDataPhonecall'].add_argument('--phone-number', dest='phoneNumber', help="Phonenumber for phonecall")
    p['argsRecordDataPhonecall'].add_argument('-o', '--outgoing', dest='outgoing', action='store_true',
                                         help="Phonecall is outgoing [default]")
    p['argsRecordDataPhonecall'].add_argument('--incoming', dest='outgoing', action='store_false',
                                         help="Phonecall is incoming")

    # Project/folder id arguments. When specified, id is never optional and always positional
    p['argsProjectId'] = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    p['argsProjectId'].add_argument('id', help="Id/name of item to remove")

    # Arguments for projects/folders
    p['argsProjectData'] = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    p['argsProjectData'].add_argument('name', nargs='?', help="Name of new one")
    p['argsProjectData'].add_argument('--name', dest='name', help="Name of new one")
    p['argsProjectData'].add_argument('description', nargs='?', help="Description")
    p['argsProjectData'].add_argument('--description', dest='description', help="Description")
    p['argsProjectData'].add_argument('color', nargs='?', help="Color as shown in web interface")
    p['argsProjectData'].add_argument('--color', dest='color', help="Color as shown in web interface")
    p['argsProjectData'].add_argument('parent', nargs='?', help="Folder to put it in. Default is no folder")
    p['argsProjectData'].add_argument('--parent', dest='parent',
                                      help="Folder to put it in. Default is no folder.  See 'print parent-id' command for help")
    
    
    # add record command
    p['parsAddRecord'] = p['subAdd'].add_parser('record', help="Add a record")
    p['subAddRecord'] = p['parsAddRecord'].add_subparsers()

    # add record work command
    p['parsAddRecordWork'] = p['subAddRecord'].add_parser('work', parents=[p['argsRecordData']], 
                                                          help="Add a Work record")
    p['parsAddRecordWork'].set_defaults(func=self._reqAddRecordWork)

    # add record phonecall command
    p['parsAddRecordPhonecall'] = p['subAddRecord'].add_parser('phonecall', parents=[p['argsRecordData'], p['argsRecordDataPhonecall']], 
                                                          help="Add a Phonecall record")
    p['parsAddRecordPhonecall'].set_defaults(func=self._reqAddRecordPhonecall)

    # add project command
    p['parsAddProject'] = p['subAdd'].add_parser('project', parents=[p['argsProjectData']], help="Add a project")
    p['parsAddProject'].set_defaults(func=self._reqAddProject)

    # add folder command
    p['parsAddFolder'] = p['subAdd'].add_parser('folder', parents=[p['argsProjectData']], help="Add a folder")
    p['parsAddFolder'].set_defaults(func=self._reqAddFolder)


    ###
    # change command
    p['parsChange'] = p['cmds'].add_parser('change', help="Change data")
    p['subChange'] = p['parsChange'].add_subparsers()

    # change record command
    p['parsChangeRecord'] = p['subChange'].add_parser('record', help="Change a record")
    p['subChangeRecord'] = p['parsChangeRecord'].add_subparsers()

    # change record any command
    p['parsChangeRecordAny'] = p['subChangeRecord'].add_parser('any', parents=[p['argsRecordId'], p['argsRecordData'], p['argsRecordDataPhonecall']], 
                                                               help="Change any record")
    p['parsChangeRecordAny'].set_defaults(func=lambda: self._reqChangeRecord(None))

    # change record work command
    p['parsChangeRecordWork'] = p['subChangeRecord'].add_parser('work', parents=[p['argsRecordId'], p['argsRecordData']], help="Change work record")
    p['parsChangeRecordWork'].set_defaults(func=lambda: self._reqChangeRecord(YastRecordWork))

    # change record phonecall command
    p['parsChangeRecordPhonecall'] = p['subChangeRecord'].add_parser('phonecall', parents=[p['argsRecordId'], p['argsRecordData'], p['argsRecordDataPhonecall']], 
                                                                help="Change phonecall record")
    p['parsChangeRecordPhonecall'].set_defaults(func=lambda: self._reqChangeRecord(YastRecordPhonecall))

    # change project command
    p['parsChangeProject'] = p['subChange'].add_parser('project', parents=[p['argsProjectId'], p['argsProjectData']], help="Change a project")
    p['parsChangeProject'].set_defaults(func=self._reqChangeProject)

    # change folder command
    p['parsChangeFolder'] = p['subChange'].add_parser('folder', parents=[p['argsProjectId'], p['argsProjectData']], help="Change a folder")
    p['parsChangeFolder'].set_defaults(func=self._reqChangeFolder)


    ###
    # delete command
    p['parsDelete'] = p['cmds'].add_parser('delete', help="Delete data")
    p['subDelete'] = p['parsDelete'].add_subparsers()

    # delete record command
    p['parsDeleteRecord'] = p['subDelete'].add_parser('record', help="Delete a record")
    p['subDeleteRecord'] = p['parsDeleteRecord'].add_subparsers()

    # delete record any command
    p['parsDeleteRecordAny'] = p['subDeleteRecord'].add_parser('any', parents=[p['argsRecordId']], help="Delete any record")
    p['parsDeleteRecordAny'].set_defaults(func=lambda: self._reqDeleteRecord(None))

    # delete record work command
    p['parsDeleteRecordWork'] = p['subDeleteRecord'].add_parser('work', parents=[p['argsRecordId']], help="Delete work record")
    p['parsDeleteRecordWork'].set_defaults(func=lambda: self._reqDeleteRecord(YastRecordWork))

    # delete record phonecall command
    p['parsDeleteRecordPhonecall'] = p['subDeleteRecord'].add_parser('phonecall', parents=[p['argsRecordId']], 
                                                                help="Delete phonecall record")
    p['parsDeleteRecordPhonecall'].set_defaults(func=lambda: self._reqDeleteRecord(YastRecordPhonecall))

    # delete project command
    p['parsDeleteProject'] = p['subDelete'].add_parser('project', parents=[p['argsProjectId']], help="Delete a project")
    p['parsDeleteProject'].set_defaults(func=self._reqDeleteProject)

    # delete folder command
    p['parsDeleteFolder'] = p['subDelete'].add_parser('folder', parents=[p['argsProjectId']], help="Delete a folder")
    p['parsDeleteFolder'].set_defaults(func=self._reqDeleteFolder)


    ###
    # get command
    p['parsGet'] = p['cmds'].add_parser('get', help="Get data")
    p['subGet'] = p['parsGet'].add_subparsers()

    # Arguments for record queries
    p['argsQueryRecords'] = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    p['argsQueryRecords'].add_argument('-f', '--from', dest='timeFrom', metavar="TF", help="Get records starting from this time")
    p['argsQueryRecords'].add_argument('-t', '--to', dest='timeTo', metavar="TT", help="Get records up till this time")
    p['argsQueryRecords'].add_argument('--type', dest='type', help="Id or name of type. Comma separated")
    p['argsQueryRecords'].add_argument('--parent', dest='parent', help="Id or name of parent project or folder. Comma separated. See 'print parent-id' command for help")
    
    # getRecords command
    p['parsGetRecords'] = p['subGet'].add_parser('records', parents=[p['argsQueryRecords']], help="Get records")
    p['parsGetRecords'].add_argument('--id', dest='id', help="Comma separated list of record ids")
    p['parsGetRecords'].set_defaults(func=self._reqGetRecords)

    # getProjects command
    p['parsGetProjects'] = p['subGet'].add_parser('projects', help="Get projects")
    p['parsGetProjects'].set_defaults(func=self._reqGetProjects)

    # getFolders command
    p['parsGetFolders'] = p['subGet'].add_parser('folders', help="Get folders")
    p['parsGetFolders'].set_defaults(func=self._reqGetFolders)

    
    ###
    # report command
    p['parsReport'] = p['cmds'].add_parser('report', parents=[p['argsQueryRecords']], help="Generate and download report")
    p['parsReport'].add_argument('format', choices=['pdf', 'html', 'xls', 'csv'], help="Report format")
    p['parsReport'].add_argument('--group-by', dest='groupBy', help="Values to group report by")
    p['parsReport'].add_argument('--constraints', dest='constraints', metavar="C", help="Additional constraints")
    p['parsReport'].set_defaults(func=self._reqReport)
    
    
    ###
    # print command
    p['parsPrint'] = p['cmds'].add_parser('print', help="Display information")
    p['subPrint'] = p['parsPrint'].add_subparsers()
    
    # print hier command
    p['parsPrintHier'] = p['subPrint'].add_parser('hier', parents=[p['argsQueryRecords']], 
                                                  help="Displays folder/project hierarcy from the given query. Optionally displays record info")
    p['parsPrintHier'].add_argument('--sum-time', dest='sum_time', action='store_true', default=False, help="Summarize record time in folder/projects")
    p['parsPrintHier'].add_argument('--no-empty', dest='no_empty', action='store_true', default=False, help="Only show folders/projects with records")
    p['parsPrintHier'].set_defaults(func=self._reqPrintHier)

    # print sum command
    p['parsPrintSum'] = p['subPrint'].add_parser('sum', parents=[p['argsQueryRecords']], 
                                                  help="Displays sum of record time")
    p['parsPrintSum'].add_argument( '--sum-total', dest='sum_total', action='store_true', default=False, 
                                    help="By default, sum is split into different record types. Set this to sum it all up, only displaying one number")
    p['parsPrintSum'].set_defaults(func=self._reqPrintSum)
    
    # print time command
    p['parsPrintTime'] = p['subPrint'].add_parser('time', help="Takes in a time description and shows resulting time", 
                                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                                 epilog=("Supported formatting:\n"
                                                         "  <date>_<time>+/-<offset>\n"
                                                         "  Either <date> or <time> must be present\n"
                                                         "  <offset>: [empty]     : No offset\n"
                                                         "             +/-IhJmKs  : I hours J minutes K seconds, all optional.\n"
                                                         "                          No letter defaults to hours\n"
                                                         "\n"
                                                         "  <time>: [empty]                         : Start of a day\n"
                                                         "          now/n                           : Now\n"
                                                         "          integer >= 1000000              : Seconds since 1.1.1900\n"
                                                         "          HH/HHMM/HHMMSS/HH:MM/HH:MM:SS   : Given time of day, 24hr format\n"
                                                         "          [all above]AM/PM                : Given time of day, 12hr format\n"
                                                         "\n"
                                                         "  <date>: [empty]/today/t                 : Today\n"
                                                         "          yesterday/y                     : Yesterday\n"
                                                         "          monday/tuesday/..               : Previous such day. Two letters required\n"
                                                         "          january/february/..             : Previous start of such month. Three letters required\n"
                                                         "          DD/MM / DD/MM/YYYY / YYYY/MM/DD : Specified date (delimiters: /,-,.)"))
    p['parsPrintTime'].add_argument('time', help="Time as described below")
    p['parsPrintTime'].set_defaults(func=self._reqPrintTime)

    # print parent-id
    p['parsPrintParentId'] = p['subPrint'].add_parser('parent-id', help="Takes in a project/folder name or path and prints the project/folder id",
                                                    formatter_class=argparse.RawDescriptionHelpFormatter,
                                                    epilog=("Supported formatting:\n"
                                                            "  [/]<name0>/<name1>/<name2>/...\n"
                                                            "\n"
                                                            "Examples:\n"
                                                            "  <name>                : Searches through all folders and projects\n"
                                                            "  <folder-name>/<name>  : Finds folder/project that is child of folder\n"
                                                            "                          with name <folder-name>\n"
                                                            "  /<name>               : Finds folder/project named <name> without parents\n"
                                                            "  /<folder-name>/<name> : Project/folder called <name> in top-level folder\n"
                                                            "                          with name <folder-name>\n"))
    p['parsPrintParentId'].add_argument('name', help="Name or description of parent as described below")
    p['parsPrintParentId'].add_argument( '--project', dest='project', action='store_true', default=False, 
                                       help="Limit lookup to projects")
    p['parsPrintParentId'].add_argument( '--folder', dest='folder', action='store_true', default=False, 
                                       help="Limit lookup to folders")
    p['parsPrintParentId'].set_defaults(func=self._reqPrintParentId)
    


  # Create Yast instance
  def _createYast(self):
    return Yast()


  # Handle login. Not required for all requests
  def _login(self, commandName):
    if self.args.user == None:
      self.yast.status = YastStatus.CLI_LOGIN_REQUIRED
      raise Exception("Username and either password or hash must be provided for command \"" + commandName + "\"")
    else:
      if self.args.hash == None:
        # No hash given, password required
        if self.args.password == None:
          self.yast.status = YastStatus.CLI_LOGIN_REQUIRED
          raise Exception("Username and either password or hash must be provided for command \"" + commandName + "\"")
        else:
          # Login
          self.yast.login(self.args.user, self.args.password)
      else:
        # Username and hash provided. Already logged in
        self.yast.user = self.args.user
        self.yast.hash = self.args.hash


  # Find longest string in array
  def _longest(self, arr):
    longest = 0
    for s in arr:
      l = len(s)
      if l > longest:
        longest = l
    return longest

  # Print object. Pretty or not defined by settings
  def _printMap(self, obj):
    l = self._longest(obj.keys()) if self.args.pretty else 0
    for key,value in obj.items():
      if value == None:
        value = ''
      print(key.ljust(l) + ": '" + value + "'")

  # Replace simple entries in propSel with lambda functions accessing the correct values in objMap
  def _preparePropSel(self, propSel, objMap):
    ret = []
    isMapArray = len(objMap) > 0 and any([isinstance(o, dict) for o in objMap])
    
    for sel in propSel:
      if isinstance(sel, str):
        if sel != "":
          if isMapArray:
            ret.append((sel, (lambda self,n: lambda self,obj: obj[n])(self,sel)))
          else:
            ret.append((sel, (lambda self,n: lambda self,obj: vars(obj)[n])(self,sel)))
      else:
        ret.append(sel)
    return ret

  def _printObjMap(self, objMap, propSel, sortOn = None):
    # Prepare data
    if not objMap and self.args.silent:
      return
    elif isinstance(objMap, dict):
      if sortOn != None and self.args.sort:
        objMap = [objMap[k] for k in sorted(objMap)]
      else:
        objMap = objMap.values()
    elif not isinstance(objMap, list):
      objMap = [objMap]

    if self.args.limit != -1:
      objMap = objMap[:self.args.limit]

    propSel = self._preparePropSel(propSel, objMap)

    # Create table of data
    cols = []
    for (propName,func) in propSel:
      col = []
      if not self.args.silent:
        col.append(propName)
      for obj in objMap:
        col.append(str(func(self, obj)))
      cols.append(col)

    colWidth = [len(max(l,key=len))+2 for l in cols] if self.args.pretty else [0]*len(cols)

    # Print table
    separator = "," if self.args.csv else ""
    for rowI in range(0, len(cols[0])):
      for colI in range(0, len(cols)):
        sys.stdout.write((cols[colI][rowI] + separator).ljust(colWidth[colI]))
      sys.stdout.write("\n")

  def _printRecords(self, objMap):
    calls = any([isinstance(o, YastRecordPhonecall) for o in objMap.values()]) \
        if isinstance(objMap, dict) else isinstance(objMap, YastRecordPhonecall)
    self._printObjMap(objMap, ["id"] if self.args.only_id else ["id", 
                               ("type", lambda self,obj: obj.typeName),
                               ("project", lambda self,obj: self._strProjectName(obj.project)),
                               ("startTime", lambda self,obj: self._strTime(obj.variables['startTime'])),
                               ("endTime", lambda self,obj: self._strTime(obj.variables['endTime'])),
                               ("comment", lambda self,obj: self._defaultMap(obj.variables, 'comment', "")),
                               ("isRunning", lambda self,obj: obj.variables['isRunning']),
                               ("phoneNumber", lambda self,obj: self._defaultMap(obj.variables, 'phoneNumber', "")) if calls else "",
                               ("outgoing", lambda self,obj: self._defaultMap(obj.variables, 'outgoing', "")) if calls else ""],
                      "id")

  def _printProjects(self, objMap):
    self._printObjMap(objMap, ["id"] if self.args.only_id else ["id", "name", 
                               ("description", lambda self,obj: self._default(obj.description, "")),
                               "primaryColor", 
                               ("parent", lambda self,obj: self._strFolderName(obj.parentId)),
                               "privileges" if self.args.all_info else "",
                               "timeCreated" if self.args.all_info else "",
                               "creator" if self.args.all_info else ""],
                      "id")
    
  # Get string representation of time
  def _strTime(self, t):
    if self.args.seconds:
      return str(int(t))
    else:
      return str(datetime.datetime.fromtimestamp(t).isoformat(' '))

  # Get string representation of duration
  def _strDuration(self, t):
    if self.args.seconds:
      return str(int(t))
    else:
      return "{0:d}:{1:02d}:{2:02d}".format(int(t) // 3600, (int(t) // 60) % 60, (int(t) % 60))
    

  # Get string representation of project. Name / id
  def _strProjectName(self, id):
    if self.args.ids:
      return str(id)
    if self.projects == None:
      self.projects = self.yast.getProjects()
    if id in self.projects:
      return self.projects[id].name
    else:
      return "unkown: " + str(id)

  # Get string representation of folder. Name / id
  def _strFolderName(self, id):
    if self.args.ids:
      return str(id)
    if self.folders == None:
      self.folders = self.yast.getFolders()
    if id == 0:
      return ""
    elif id in self.folders:
      return self.folders[id].name
    else:
      return "unkown: " + str(id)
      
  def _printOk(self):
    if not self.args.silent:
      print("OK")


  # Resolve project/folder uniquely
  # type is target and can be YastProject, YastFolder or None for both
  #  if type is given as project, the project will be selected if there
  #  are matches for both project and folders
  # parent is parent id or -1 if unknown
  def _resolveHierNode(self, text, type, parent):
    node = None

    if text.startswith("/"):
      # We are at root
      parent = 0
      text = text[1:]

    # Find name of node
    split = text.split("/", 1)
    name = split[0]
    
    # If / after name, we are looking for a folder now
    curType = YastFolder if len(split) > 1 else type

    # See if name can be uniquely resolved
    if curType == YastProject or curType == None:
      if self.projects == None:
        self.projects = self.yast.getProjects()
          
      for p in self.projects.values():
        if p.name == name and (parent == -1 or p.parentId == parent):
          if node == None:
            node = p.id
          else:
            raise Exception("Name \"" + name + "\"" + 
                            (" with parent folder \"" + self._strFolderName(parent) + "\"" if parent != 0 and parent != -1 else "") +
                            " does not uniquely identify a " +
                            ("project" if curType == YastFolder else "project/folder"))
      
    if curType == YastFolder or curType == None:
      if self.folders == None:
        self.folders = self.yast.getFolders()
          
      for p in self.folders.values():
        if p.name == name and (parent == -1 or p.parentId == parent):
          if node == None:
            node = p.id
          else:
            raise Exception("Name \"" + name + "\"" +
                            (" with parent folder \"" + self._strFolderName(parent) + "\"" if parent != 0 and parent != -1 else "") +
                            " does not uniquely identify a " +
                            ("folder" if curType == YastFolder else "project/folder"))

    if node == None:
      raise Exception("Name \"" + name + "\"" +
                      (" with parent folder \"" + self._strFolderName(parent) + "\"" if parent != 0 and parent != -1 else "") +
                      " does not identify a " +
                      ("folder" if curType == YastFolder else ("project" if curType == YastProject else "project/folder")))
      
    if len(split) > 1:
      # Continue with child
      return self._resolveHierNode(split[1], type, node)
    else:
      # We have our result
      return node
    

  # Resolve project from string. Can either be a project id or a name
  def _resolveProject(self, text):
    if text == None:
      raise Exception("No project specified")
    elif not text.isdigit():
      return self._resolveHierNode(text, YastProject, -1)
    else:
      return int(text)

  # Resolve folder from string. Can either be a folder id or a name
  def _resolveFolder(self, text):
    if text == None or text == "0":
      #Unspecified folder means top-level
      return 0
    elif not text.isdigit():
      return self._resolveHierNode(text, YastFolder, -1)
    else:
      return int(text)

  # Resolve parent list from string. Can be project id/name or folder id/name. Returns list
  def _resolveParents(self, text):
    oldList = text.split(",")
    newList = []
    for n in oldList:
      if not n.isdigit():
        newList.append(str(self._resolveHierNode(n, None, -1)))
      else:
        newList.append(n)
    return ",".join(newList)

  # Resolve record type list from string
  def _resolveRecordTypes(self, text):
    oldList = text.split(",")
    newList = []
    if self.recordTypes == None:
      self.recordTypes = self.yast.getRecordTypes()
    for n in oldList:
      if not n.isdigit():
        found = False
        for t in self.recordTypes.values():
          if t.name.lower() == n.lower():
            newList.append(str(t.id))
            found = True
            break
        if not found:
          raise Exception("No record type with name \"" + n + "\" found")
      else:
        newList.append(t)
    return ",".join(newList)    
    

  # Resolve time. Supported formatting is given by help for the "print time" command
  def _resolveTime(self, text):
    try:
      # Empty is now
      if text == "" or text == None:
        return time.time()

      # Parse input
      regex = '^(?:(?P<month>janu?a?r?y?|febr?u?a?r?y?|marc?h?|apri?l?|may|june?|july?|augu?s?t?|sept?e?m?b?e?r?|octo?b?e?r?|nove?m?b?e?r?|dece?m?b?e?r?)|' + \
          '(?P<day>mon?d?a?y?|tue?s?d?a?y?|wed?n?e?s?d?a?y?|thu?r?s?d?a?y?|fri?d?a?y?|sat?u?r?d?a?y?|sun?d?a?y?|to?d?a?y?|ye?s?t?e?r?d?a?y?)|' + \
          '(?:(?P<date_d>\d{1,4})[/.-](?P<date_m>\d{1,2})[/.-]?(?P<date_y>\d{1,4})?))?' + \
          '_?' + \
          '(?:(?P<time_n>no?w?)|(?:(?P<time_h>\d+):?(?P<time_m>\d{1,2})?:?(?P<time_s>\d{1,2})?(?P<time_ampm>am?|pm?)?))?' + \
          '(?:(?P<offset_op>\+|-)(?:(?P<offset_h>\d+)h?(?![ms]))?(?:(?P<offset_m>\d+)m?(?!s))?(?:(?P<offset_s>\d+)s?)?)?$'
        
      m = re.match(regex, text, re.IGNORECASE)
      if m == None or all([mv == None for mv in m.groups()]):
        raise Exception("Invalid time description: \"" + text + "\"")

      # Parse date
      ts = time.localtime(time.time())
      if m.group('month') != None:
        month = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}[m.group('month').lower()[0:3]]
        year = ts.tm_year if month <= ts.tm_mon else ts.tm_year -1
        t = time.mktime((year, month, 1, 0, 0, 0, -1, -1, -1))
      elif m.group('day') != None:
        dayStr = m.group('day').lower()
        weekMap = {'mo': 0, 'tu': 1, 'we': 2, 'th': 3, 'fr': 4, 'sa': 5, 'su': 6}
        if dayStr[0:2] in weekMap: # Weekday
          wd = weekMap[dayStr[0:2]]
          offset =  wd - ts.tm_wday if wd <= ts.tm_wday else  (wd - ts.tm_wday) - 7
        elif dayStr[0] == 't':     # Today
          offset = 0
        else:                      # Yesterday
          offset = -1
        t = time.mktime((ts.tm_year, ts.tm_mon, ts.tm_mday+offset, 0, 0, 0, -1, -1, -1))
      elif m.group('date_d') != None or m.group('date_m') != None:
        if m.group('date_d') != None and m.group('date_y') != None and len(m.group('date_d')) == 4: #YYYY/MM/DD
          t = time.mktime((int(m.group('date_d')), int(m.group('date_m')), int(m.group('date_y')), 
                           0, 0, 0, -1, -1, -1))
        else:
          t = time.mktime((int(m.group('date_y')) if m.group('date_y') != None else ts.tm_year, int(m.group('date_m')), int(m.group('date_d')), 
                           0, 0, 0, -1, -1, -1))
      else:
        t = time.mktime((ts.tm_year, ts.tm_mon, ts.tm_mday, 0, 0, 0, -1, -1, -1))

      # Parse time
      if m.group('time_n') != None: #Now
        t = int(time.time())
      elif m.group('time_h') != None:
        h = int(m.group('time_h'))
        if m.group('time_m') == None and m.group('time_s') == None:
          if h > 1000000: # Second definition. Invalidates any previous date
            t = h
            s = 0; mm = 0; h = 0
          elif h > 10000:
            s = h % 100
            mm = int(h / 100) % 100
            h = int(h / 10000) % 100
          elif h > 100:
            s = 0
            mm = h % 100
            h = int(h / 100) % 100
          else:
            s = 0; mm = 0
        else:
          mm = int(m.group('time_m'))
          s = int(m.group('time_s')) if m.group('time_s') != None else 0
        if m.group('time_ampm') != None:
          if h >= 12:
            h = 0
          if m.group('time_ampm').lower()[0] == 'p':
            h += 12
        t += h*3600 + mm*60 + s

      # Parse offset
      if m.group('offset_op') != None:
        offset = 0
        if m.group('offset_h') != None:
          offset = int(m.group('offset_h')) * 3600
        if m.group('offset_m') != None:
          offset += int(m.group('offset_m')) * 60
        if m.group('offset_s') != None:
          offset += int(m.group('offset_s'))
        t += offset if m.group('offset_op') == '+' else -offset
    
    except:
      raise Exception("Invalid time description \"" + text + "\"")

    return t

  def _default(self, val, default):
    return val if val != None else default

  def _defaultMap(self, map, name, default):
    return map[name] if name in map and map[name] != None else default

  # Returns options for record query
  def _optsQueryRecords(self):
    options = {}
    if 'timeFrom' in self.args: options['timeFrom'] = self._resolveTime(self.args.timeFrom)
    if 'timeTo' in self.args: options['timeTo'] = self._resolveTime(self.args.timeTo)
    if 'type' in self.args: options['typeId'] = self._resolveRecordTypes(self.args.type)
    if 'parent' in self.args: options['parentId'] = self._resolveParents(self.args.parent)
    return options    
        
  # Login comand
  def _reqLogin(self):
    self._login("login")
    print(self.yast.hash)

  # userGetInfo command
  def _reqUserGetInfo(self):
    self._login("user get-info")
    info = self.yast.userGetInfo()
    self._printMap(info)

  # userGetSettings command
  def _reqUserGetSettings(self):
    self._login("user get-settings")
    info = self.yast.userGetSettings()
    self._printMap(info)

  # userSetSetting command
  def _reqUserSetSetting(self):
    self._login("user set-setting")
    info = self.yast.userSetSetting(self.args.key, self.args.value)
    self._printOk()

  # add record work command
  def _reqAddRecordWork(self):
    self._login("add record work")
    self._printRecords(self.yast.add(YastRecordWork(self._resolveProject(self.args.project if 'project' in self.args else 0), 
                                                    self._resolveTime(self.args.startTime if 'startTime' in self.args else ''), 
                                                    self._resolveTime(self.args.endTime if 'endTime' in self.args else ''), 
                                                    self.args.comment if 'comment' in self.args else '',
                                                    0 if not 'isRunning' in self.args or not self.args.isRunning else 1)))

  # add record phonecall command
  def _reqAddRecordPhonecall(self):
    self._login("add record phonecall")
    self._printRecords(self.yast.add(YastRecordPhonecall(self._resolveProject(self.args.project if 'project' in self.args else 0), 
                                                         self._resolveTime(self.args.startTime if 'startTime' in self.args else ''), 
                                                         self._resolveTime(self.args.endTime if 'endTime' in self.args else ''), 
                                                         self.args.comment if 'comment' in self.args else '',
                                                         0 if not 'isRunning' in self.args or not self.args.isRunning else 1,
                                                         self.args.phoneNumber if 'phoneNumber' in self.args else '',
                                                         0 if not 'outgoing' in self.args or not self.args.outgoing else 1)))

  # add project command
  def _reqAddProject(self):
    self._login("add project")
    self._printProjects(self.yast.add(YastProject(self.args.name if 'name' in self.args else "", 
                                                  self.args.description if 'description' in self.args else "", 
                                                  self.args.color if 'color' in self.args else "blue",
                                                  self._resolveFolder(self.args.parent) if 'parent' in self.args else 0)))

  # add folder command
  def _reqAddFolder(self):
    self._login("add folder")
    self._printProjects(self.yast.add(YastFolder(self.args.name if 'name' in self.args else "", 
                                                 self.args.description if 'description' in self.args else "", 
                                                 self.args.color if 'color' in self.args else "blue",
                                                 self._resolveFolder(self.args.parent) if 'parent' in self.args else 0)))

  # change record command
  def _reqChangeRecord(self, type):
    self._login("change record")
    rec = self.yast.getRecords({'id': self.args.id})
    if len(rec) != 1:
      raise Exception("Invalid record id: " + str(self.args.id))
    rec = next(iter(rec.values()))
    if type != None and not isinstance(rec, type):
      raise Exception("Record is of type '{0}', not of requested type '{1}'".format(rec.typeName, type.typeName))
    if 'project' in self.args: rec.project = self._resolveProject(self.args.project)
    if 'startTime' in self.args: rec.variables['startTime'] = self._resolveTime(self.args.startTime)
    if 'endTime' in self.args: rec.variables['endTime'] = self._resolveTime(self.args.endTime)
    if 'comment' in self.args: rec.variables['comment'] = self.args.comment
    if 'isRunning' in self.args: rec.variables['isRunning'] = 1 if self.args.isRunning else 0
    if 'phoneNumber' in self.args: rec.variables['phoneNumber'] = self.args.phoneNumber
    if 'outgoing' in self.args: rec.variables['outgoing'] = 1 if self.args.outgoing else 0
    self._printRecords(self.yast.change(rec))

  # change project command
  def _reqChangeProject(self):
    self._login("change project")
    id = self._resolveProject(self.args.id)
    if self.projects == None:
      self.projects = self.yast.getProjects()
    if not id in self.projects:
      raise Exception("Invalid project id: " + str(id))
    proj = self.projects[id]
    if 'name' in self.args: proj.name = self.args.name
    if 'description' in self.args: proj.description = self.args.description
    if 'color' in self.args: proj.primaryColor = self.args.color
    if 'parent' in self.args: proj.parentId = self._resolveFolder(self.args.parent)
    self._printProjects(self.yast.change(proj))

  # change folder command
  def _reqChangeFolder(self):
    self._login("change folder")
    id = self._resolveFolder(self.args.id)
    if self.folders == None:
      self.folders = self.yast.getFolders()
    if not id in self.folders:
      raise Exception("Invalid folder id: " + str(id))
    folder = self.folders[id]
    if 'name' in self.args: folder.name = self.args.name
    if 'description' in self.args: folder.description = self.args.description
    if 'color' in self.args: folder.primaryColor = self.args.color
    if 'parent' in self.args: folder.parentId = self._resolveFolder(self.args.parent)
    self._printProjects(self.yast.change(folder))    


  # delete record command
  def _reqDeleteRecord(self, type):
    self._login("delete record")
    rec = None
    if type != None:
      rec = self.yast.getRecords({'id': self.args.id})
      if len(rec) != 1:
        raise Exception("Invalid record id")
      rec = next(iter(rec.values()))
      if not isinstance(rec, type):
        raise Exception("Record is of type '{0}', not of requested type '{1}'".format(rec.typeName, type.typeName))
    if rec == None:
      rec = YastRecord(-1, -1, None)
      rec.id = self.args.id
    self.yast.delete(rec)
    self._printOk()

  # delete project command
  def _reqDeleteProject(self):
    self._login("delete project")
    id = self._resolveProject(self.args.id)
    proj = YastProject("","","",0);
    proj.id = id
    self.yast.delete(proj)
    self._printOk()

  # delete folder command
  def _reqDeleteFolder(self):
    self._login("delete folder")
    id = self._resolveFolder(self.args.id)
    folder= YastFolder("","","",0);
    folder.id = id   
    self.yast.delete(folder)
    self._printOk()
    
  # getRecords command
  def _reqGetRecords(self):
    self._login("get records")
    options = self._optsQueryRecords()
    if self.args.id != None: options['id'] = self.args.id
    self._printRecords(self.yast.getRecords(options))
        

  # getProjects command
  def _reqGetProjects(self):
    self._login("get projects")
    self._printProjects(self.yast.getProjects())

  # getFolders command
  def _reqGetFolders(self):
    self._login("get folders")
    self._printProjects(self.yast.getFolders())

  # report command
  def _reqReport(self):
    self._login("report")
    options = self._optsQueryRecords()
    if self.args.groupBy != None: options['groupBy'] = self.args.groupBy
    if self.args.constraints != None: options['constraints'] = self.args.constraints
    report = self.yast.getReport(self.args.format, options)
    if sys.version_info[0] == 3:
      sys.stdout.buffer.write(report)
    else:
      sys.stdout.write(report)

    
  # print hier command
  def _reqPrintHier(self):
    self._login("print hier")

    # Folders and projects
    self.folders = self.yast.getFolders()
    self.projects = self.yast.getProjects()
    
    if sys.version_info[0] == 3:
      nodes = dict(self.folders.items() | self.projects.items())
      nodesSorted = sorted(nodes.items()) if self.args.sort else nodes.items()
    else:
      nodes = dict(self.folders.items() + self.projects.items())
      nodesSorted = sorted(nodes.iteritems()) if self.args.sort else nodes.iteritems()
    
    # Prepare userdata
    for k, n in nodesSorted:
      n.userData = {'children': [], 'records': [], 'parent': None, 'sum': {}}

    # Link parents and children
    disconnectPresent = False
    for k, n in nodesSorted:
      if n.parentId != 0:
        if n.parentId in nodes:
          parent = nodes[n.parentId]
          n.userData['parent'] = parent
          parent.userData['children'].append(n)    
        else:
          # No access to parent. Mark as disconnected
          n.parentId = -1
          disconnectPresent = True

    # Process based on records?
    if self.args.sum_time or self.args.no_empty:
      recs = self.yast.getRecords(self._optsQueryRecords())
      for r in recs.values():
        nodes[r.project].userData['records'].append(r)

      if self.args.sum_time or self.args.no_empty:
        # Summarize time spent
        for k, n in nodesSorted:
          for r in n.userData['records']:
            # Add to project and all parents
            dt = r.variables['endTime'] - r.variables['startTime']
            iterN = n
            while iterN != None:
              if not r.typeName in iterN.userData['sum']:
                iterN.userData['sum'][r.typeName] = dt
              else:
                iterN.userData['sum'][r.typeName] += dt
              iterN = iterN.userData['parent']
      
      if self.args.no_empty:
        # Unlink projects and groups with no time spent
        for k, n in nodesSorted:
          if all([v <= 0 for v in n.userData['sum'].values()]):
            if n.userData['parent'] != None:
              n.userData['parent'].userData['children'].remove(n)          

    # Recursively gather folder/project data
    def gatherFunc(n, depth, map, gatherFunc):
      if not self.args.no_empty or any([t > 0 for t in n.userData['sum'].values()]):
        map.append({'depth/name': ('-'*depth) + (n.name if not self.args.only_id else n.id),
                    'type':       'Project' if isinstance(n, YastProject) else 'Folder',
                    'time':       ", ".join([type + ": " + self._strDuration(duration) for (type, duration) in n.userData['sum'].items()]) \
                      if self.args.sum_time else ''})

        for n in n.userData['children']:
          gatherFunc(n, depth+1, map, gatherFunc)

    #Generate hierarcy 
    map = []
    for k, n in nodesSorted:
      # Only do the top nodes
      if n.parentId == 0:
        gatherFunc(n, 0, map, gatherFunc)
        
    #Nodes with missing parents
    if disconnectPresent:
      duration = sum([sum([t for t in n.userData['sum'].values()]) for k, n in nodesSorted if n.parentId == -1])
      if not self.args.no_empty or duration > 0:
        map.append({'depth/name': "__missing_parents__", 'type': "", 'time': ""})
        for k, n in nodesSorted:
          # Only do the top nodes
          if n.parentId == -1:
            gatherFunc(n, 1, map, gatherFunc)

    self._printObjMap(map, ["depth/name", "type", "time" if self.args.sum_time else ""])

  # print sum command
  def _reqPrintSum(self):
    self._login("print sum")

    # Records
    recs = self.yast.getRecords(self._optsQueryRecords())
    total = {}
    for r in recs.values():
      dt = r.variables['endTime'] - r.variables['startTime']
      if not r.typeName in total:
        total[r.typeName] = dt
      else:
        total[r.typeName] += dt
      
    if self.args.sum_total:
      print(self._strDuration(sum([duration for duration in total.values()])))
    else:
      print(", ".join([type + ": " + self._strDuration(duration) for (type, duration) in total.items()]))
                         
  # print time command
  def _reqPrintTime(self):
    print(self._strTime(self._resolveTime(self.args.time)))

  # print parent-id command
  def _reqPrintParentId(self):
    self._login("print parent-id")

    type = YastFolder if self.args.folder else (YastProject if self.args.project else None)
    print(self._resolveHierNode(self.args.name, type, -1))
    

# Yast CLI entrypoint
if __name__ == '__main__':
  # Run CLI
  cli = YastCli()
  cli.execute()

  # If we get here, command was successful
  sys.exit(0)
