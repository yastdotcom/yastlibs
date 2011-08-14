#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
# SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
# FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
# Yast Python LIB
#
# Version:
# 0.8 - First release
#

import os,sys
if sys.version_info[0] == 3:
  from urllib.parse import urlencode
  from http.client import HTTPConnection
else:
  from urllib import urlencode
  from httplib import HTTPConnection
from xml.etree import ElementTree


# Status messages returned from Yast API. Return-value from last API call can
# be read through yast.getStatus() given yast = Yast()
class YastStatus:
  SUCCESS = 0
  UNKNOWN = 1
  ACCESS_DENIED = 3
  NOT_LOGGED_IN = 4
  LOGIN_FAILURE = 5
  INVALID_INPUT = 6
  SUBSCRIPTION_REQUIRED = 7
  DATA_FORMAT_ERROR = 8
  NO_REQUEST = 9
  INVALID_REQUEST = 10
  MISSING_FIELDS = 11
  REQUEST_TOO_LARGE = 12
  SERVER_MAINTENANCE = 13
  
  DUPLICATE_ITEM = 100
  INSUFFICIENT_PRIVILEGES = 101
  UNKNOWN_RECORDTYPE = 200
  UNKNOWN_PROJECT = 201
  UNKNOWN_FOLDER = 202
  UNKNOWN_RECORD = 203
  PARENT_IS_SELF = 204
  VARIABLETYPE_MISMATCH = 205
  UNKNOWN_SETTING = 300
  INVALID_SETTING_VALUE = 301
  PASSWORD_FORMAT_INVALID = 800
  UNKNOWN_REPORT_FORMAT = 801
  UNKNOWN_GROUPBY_VALUE = 802

  # Reserved for client side
  LIB_XML_PARSE_ERROR = 40
  LIB_NOT_LOGGED_IN = 41
  LIB_EXCEPTION = 42

  CLI_ARGUMENT_ERROR = 60
  CLI_LOGIN_REQUIRED = 61
  CLI_EXCEPTION = 62
  

# Generic yast record
class YastRecord(object):
  id = -1
  typeId = -1
  timeCreated = -1
  timeUpdated = -1
  project = -1
  variables = None
  creator = -1
  flags = 0

  # User data. Will not be synchronized to Yast. You can
  # fill this with whatever you like
  userData = None

  # Construct a generic yast record
  def __init__(self, typeId, project, variables):
    self.typeId = typeId
    self.project = project
    self.variables = variables

  # Returns XML description of record
  def toXml(self, includeId=True, includeData=True):
    return '<record>' + \
        ('<id>' + str(self.id) + '</id>' if includeId else '') + \
        ('<typeId>' + str(self.typeId) + '</typeId>' + \
           '<project>' + str(self.project) + '</project>' \
           if includeData else '') + \
           '</record>'


# Yast Work record
class YastRecordWork(YastRecord):
  typeName = "work"

  # Construct a work record
  def __init__(self, project, startTime, endTime, comment, isRunning):
    super(YastRecordWork, self).__init__(1, int(project), {'startTime': int(startTime),
                                                           'endTime': int(endTime),
                                                           'comment': comment if comment != None else "",
                                                           'isRunning': int(isRunning)})
  

  # Returns XML description of record
  def toXml(self, includeId=True, includeData=True):
    return '<record>' + \
        ('<id>' + str(self.id) + '</id>' if includeId else '') + \
        ('<typeId>1</typeId>' + \
           '<project>' + str(self.project) + '</project>' + \
           '<variables><v>' + str(self.variables['startTime']) + '</v><v>' + str(self.variables['endTime']) + '</v>' + \
           '<v><![CDATA[' + self.variables['comment'] + ']]></v><v>' + str(self.variables['isRunning']) + '</v></variables>' \
           if includeData else '') + \
           '</record>'
  


# Yast Phonecall record
class YastRecordPhonecall(YastRecord):
  typeName = "phonecall"

  # Construct a work record
  def __init__(self, project, startTime, endTime, comment, isRunning, phoneNumber, outgoing):
    super(YastRecordPhonecall, self).__init__(3, int(project), {'startTime': int(startTime),
                                                           'endTime': int(endTime),
                                                           'comment': comment if comment != None else "",
                                                           'isRunning': int(isRunning),
                                                           'phoneNumber': phoneNumber,
                                                           'outgoing': int(outgoing)})
    

  # Returns XML description of record
  def toXml(self, includeId=True, includeData=True):
    return '<record>' + \
        ('<id>' + str(self.id) + '</id>' if includeId else '') + \
        ('<typeId>3</typeId>' + \
           '<project>' + str(self.project) + '</project>' + \
           '<variables><v>' + str(self.variables['startTime']) + '</v><v>' + str(self.variables['endTime']) + '</v>' + \
           '<v><![CDATA[' + self.variables['comment'] + ']]></v><v>' + str(self.variables['isRunning']) + '</v>' + \
           '<v><![CDATA[' + str(self.variables['phoneNumber']) + ']]></v><v>' + str(self.variables['outgoing']) + '</v></variables>' \
           if includeData else '') + \
           '</record>'
  


# Yast project
class YastProject(object):
  id = -1
  name = ""
  description = ""
  primaryColor = ""
  parentId = -1
  privileges = 0
  timeCreated = -1
  creator = -1

  # User data. Will not be synchronized to Yast
  userData = None

  # Construct a yast project
  def __init__(self, name, description, primaryColor, parentId=0):
    self.name = name
    self.description = description if description != None else ""
    self.primaryColor = primaryColor
    self.parentId = int(parentId)
    
  
  # Returns XML description of project
  def toXml(self, includeId=True, includeData=True):
    return '<project>' + \
        ('<id>' + str(self.id) + '</id>' if includeId else '') + \
        ('<name><![CDATA[' + self.name + ']]></name>' + \
           '<description><![CDATA[' + self.description + ']]></description>' + \
           '<primaryColor><![CDATA[' + self.primaryColor + ']]></primaryColor>' + \
           '<parentId>' + str(self.parentId) + '</parentId>' + \
           '<flags>0</flags>' if includeData else '') + \
           '</project>'
  


# Yast folder
class YastFolder(object):
  id = -1
  name = ""
  description = ""
  primaryColor = ""
  parentId = -1
  privileges = 0
  timeCreated = -1
  creator = -1

  # User data. Will not be synchronized to Yast
  userData = None

  # Construct a yast folder
  def __init__(self, name, description, primaryColor, parentId=0):
    self.name = name
    self.description = description if description != None else ""
    self.primaryColor = primaryColor
    self.parentId = int(parentId)
  
  # Returns XML description of folder
  def toXml(self, includeId=True, includeData=True):
    return '<folder>' + \
        ('<id>' + str(self.id) + '</id>' if includeId else '') + \
        ('<name><![CDATA[' + self.name + ']]></name>' + \
           '<description><![CDATA[' + self.description + ']]></description>' + \
           '<primaryColor><![CDATA[' + self.primaryColor + ']]></primaryColor>' + \
           '<parentId>' + str(self.parentId) + '</parentId>' + \
           '<flags>0</flags>' if includeData else '') + \
           '</folder>'
  


# Yast Record Type
class YastRecordType(object):
  id = -1
  name = ""
  variableTypes = None

  def __init__(self, name, variableTypes):
    self.name = name
    self.variableTypes = variableTypes
  

# Yast Variable Type
class YastVariableType(object):
  id = -1
  name = ""
  valType = -1
  
  def __init__(self, name, valType):
    self.name = name
    self.valType = int(valType)
  


class Yast(object):
  
  # Host
  host = 'www.yast.com'
  # API URL
  apiPath = '/1.0/'
  # Download URL
  dlPath = '/file.php'
  # Request method. True for GET, False for POST 
  requestMethodGet = False
  # Request timeout in seconds
  requestTimeout = 300

  # Previous error code 
  status = YastStatus.SUCCESS

  # Propagate exceptions out of Yast class
  propagateExceptions = False

  # Username from last login
  user = None
  # Hash from last login
  hash = None
  
  # Login as a given user.
  # @param user username 
  # @param password password for given user
  # @return hash hash to use for further requests on this user
  def login(self, user, password):
    self.status = YastStatus.SUCCESS
    try:
      resp = self._request('<request req="auth.login">' +
                           '<user>' + user + '</user>'+
                           '<password>' + password + '</password>' +
                           '</request>')
      
      self._verifyStatus(resp)
      self.hash = resp.find('hash').text
      self.user = user
      return self.hash
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
    
    
    

  # Forget about previous login
  def clearLogin(self):
    self.hash = None
    self.user = None
    return True
  


  # Get user info
  # @param user username
  # @param hash user hash
  # @return map of user info
  def userGetInfo(self, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)

      resp = self._request('<request req="user.getInfo">' +
                           '<user><![CDATA[' + user + ']]></user>' +
                           '<hash><![CDATA[' + hash + ']]></hash>' +
                           '</request>')

      self._verifyStatus(resp)
      return self._getXmlFields(resp)
    
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
    

  # Get all user settings
  # @param user username
  # @param hash user hash
  # @return map of settings or False on failure
  def userGetSettings(self, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)
      
      resp = self._request('<request req="user.getSettings">' +
                           '<user><![CDATA[' + user + ']]></user>' +
                           '<hash><![CDATA[' + hash + ']]></hash>' +
                           '</request>')
      
      self._verifyStatus(resp)

      # Create and return map of settings
      map = {}
      for key, value in zip(list(resp.find('keys')), list(resp.find('values'))):
        if key.tag == 'v' and value.tag == 'v':
          map[key.text] = value.text

      return map
    
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False


  # Set a user setting
  # @param user username
  # @param hash user hash
  # @param key setting key
  # @param value new value
  # @return TRUE on success, FALSE on error
  def userSetSetting(self, key, value, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)
      
      resp = self._request('<request req="user.setSetting">' +
                           '<user><![CDATA[' + user + ']]></user>' +
                           '<hash><![CDATA[' + hash + ']]></hash>' +
                           '<key><![CDATA[' + key + ']]></key>' +
                           '<value><![CDATA[' + value + ']]></value>' +
                           '</request>')
      
      self._verifyStatus(resp)
      return True
    
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False

    
  # Add records, projects and folders to Yast
  # @param user username
  # @param hash user hash
  # @param objects Single object or array of objects to add. Objects are updated
  #                with id, etc. The same objects are given as return value
  # @return False on error, objects array if successful
  def add(self, objects, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)

      # Accumulate XML description of objects
      xmlObj = ''
      if isinstance(objects, list):
        for o in objects:
          xmlObj += o.toXml(False, True)
      else:
        xmlObj = objects.toXml(False, True)
      
      # Transmit request
      resp = self._request('<request req="data.add">' +
                           '<user><![CDATA[' + user + ']]></user>' +
                           '<hash><![CDATA[' + hash + ']]></hash>' +
                           '<objects>' + xmlObj + '</objects>' +
                           '</request>')
      
      self._verifyStatus(resp)    
      struct = self._xmlDataToStruct(resp, False)

      # Apply new information to objects. Objects are added in sequence,
      # so the first object added will be the first in its respective list
      self._updateObjects(objects if isinstance(objects, list) else [objects], struct)
      return objects
    
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
    
  

    
  # Change records, projects and folders in Yast
  # @param user username
  # @param hash user hash
  # @param objects Single object or array of objects to change. 
  #                The same objects are given as return value
  # @return False on error, objects array if successful
    
  def change(self, objects, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)
      
      # Accumulate XML description of objects
      xmlObj = ''
      if isinstance(objects, list):
        for o in objects:
          xmlObj += o.toXml(True, True)
      else:
        xmlObj = objects.toXml(True, True)

      # Transmit request
      resp = self._request('<request req="data.change">' +
                           '<user><![CDATA[' + user + ']]></user>' +
                           '<hash><![CDATA[' + hash + ']]></hash>' +
                           '<objects>' + xmlObj + '</objects>' +
                           '</request>')

      self._verifyStatus(resp)    
      struct = self._xmlDataToStruct(resp, False)

      # Apply new information to objects. Objects are added in sequence,
      # so the first object added will be the first in its respective list
      self._updateObjects(objects if isinstance(objects, list) else [objects], struct)
      return objects
    
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
    
  


    
  # Delete records, projects and folders in Yast
  # @param user username
  # @param hash user hash
  # @param objects Single object or array of objects to delete
  # @return False on error, True if successful
  def delete(self, objects, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)

      # Accumulate XML description of objects
      xmlObj = ''
      if isinstance(objects, list):
        for o in objects:
          xmlObj += o.toXml(True, False)
      else:
        xmlObj = objects.toXml(True, False)

      # Transmit request
      resp = self._request('<request req="data.delete">' +
                           '<user><![CDATA[' + user + ']]></user>' +
                           '<hash><![CDATA[' + hash + ']]></hash>' +
                           '<objects>' + xmlObj + '</objects>' +
                           '</request>')
      
      self._verifyStatus(resp)    
      return True
    
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
    
  
  


  # Returns records of a given user
  # @param user username
  # @param hash user hash
  # @param options associative array of options
  # @return array of records
  def getRecords(self, options=None, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)

      resp = self._request('<request req="data.getRecords">' +
			     '<user><![CDATA[' + user + ']]></user>' +
			     '<hash><![CDATA[' + hash + ']]></hash>' +
			     ('' if options == None else
			      ('<timeFrom>' + str(options['timeFrom']) + '</timeFrom>' if 'timeFrom' in options else '') +
			      ('<timeTo>' + str(options['timeTo']) + '</timeTo>' if 'timeTo' in options else '') +
			      ('<typeId>' + str(options['typeId']) + '</typeId>' if 'typeId' in options else '') +
			      ('<parentId>' + str(options['parentId']) + '</parentId>' if 'parentId' in options else '') +
			      ('<id>' + str(options['id']) + '</id>' if 'id' in options else '')) +
			     '</request>')

      self._verifyStatus(resp)    
      struct = self._xmlDataToStruct(resp)
      return struct['records']
      
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
    
  



  # Returns projects of a given user
  # @param user username
  # @param hash user hash
  # @return array of projects
  def getProjects(self, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)

      resp = self._request('<request req="data.getProjects">' +
			     '<user><![CDATA[' + user + ']]></user>' +
			     '<hash><![CDATA[' + hash + ']]></hash>' +
			     '</request>')

      self._verifyStatus(resp)    
      struct = self._xmlDataToStruct(resp)
      return struct['projects']
      
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
    
  
  

  # Returns folders of a given user
  # @param user username
  # @param hash user hash
  # @return array of folders
  def getFolders(self, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)

      resp = self._request('<request req="data.getFolders">' +
			     '<user><![CDATA[' + user + ']]></user>' +
			     '<hash><![CDATA[' + hash + ']]></hash>' +
			     '</request>')

      self._verifyStatus(resp)    
      struct = self._xmlDataToStruct(resp)
      return struct['folders']
      
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
     
    
  # Returns record types
  # @param user username
  # @param hash user hash
  # @return array of record types
  def getRecordTypes(self, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)

      resp = self._request('<request req="meta.getRecordTypes">' +
			     '<user><![CDATA[' + user + ']]></user>' +
			     '<hash><![CDATA[' + hash + ']]></hash>' +
			     '</request>')

      self._verifyStatus(resp)    
      struct = self._xmlDataToStruct(resp)
      return struct['recordTypes']
      
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False

  


  # Returns report data
  # @param user username
  # @param hash user hash
  # @param reportFormat format of report
  # @param options
  # @return raw report data or False on failure
  def getReport(self, reportFormat, options=None, user=None, hash=None):
    self.status = YastStatus.SUCCESS
    try:
      user, hash = self._verifyLogin(user, hash)

      # Request report
      resp = self._request('<request req="report.getReport">' +
			     '<user><![CDATA[' + user + ']]></user>' +
			     '<hash><![CDATA[' + hash + ']]></hash>' +
			     '<reportFormat>' + reportFormat + '</reportFormat>' +
			     ('' if options == None else
			      ('<timeFrom>' + str(options['timeFrom']) + '</timeFrom>' if 'timeFrom' in options else '') +
			      ('<timeTo>' + str(options['timeTo']) + '</timeTo>' if 'timeTo' in options else '') +
			      ('<typeId>' + str(options['typeId']) + '</typeId>' if 'typeId' in options else '') +
			      ('<parentId>' + str(options['parentId']) + '</parentId>' if 'parentId' in options else '') +
			      ('<groupBy><![CDATA[' + options['groupBy'] + ']]></groupBy>' if 'groupBy' in options else '') +
			      ('<constraints><![CDATA[' + options['constraints'] + ']]></constraints>' if 'constraints' in options else '')) +
			     '</request>')

      self._verifyStatus(resp)
      fields = self._getXmlFields(resp)

      # Download
      conn = HTTPConnection(self.host)
      conn.request('GET', self.dlPath + "?" + urlencode({'type':     'report',
                                                                'id':       fields['reportId'],
                                                                'hash':     fields['reportHash'],
                                                                'user':     user,
                                                                'userhash': hash}))
      file = conn.getresponse().read()
      conn.close()
      return file
      
    except:
      if self.status == YastStatus.SUCCESS:
        self.status = YastStatus.LIB_EXCEPTION
      if self.propagateExceptions:
        raise
      return False
    
     

  #  Returns status of prevous access 
  def getStatus(self):
    return self.status


  # If user and hash are not specified, require that 
  # self.user and self.hash are specified, and
  # set user and hash to them
  def _verifyLogin(self, user, hash):
    if user == None or hash == None:
      # Require previous login
      if self.user != None and self.hash != None:
        return self.user, self.hash
      else:
        self.status = YastStatus.LIB_NOT_LOGGED_IN
        raise Exception("Library function called without user/hash without prior login")
    else:
      return user, hash
      

  # Verify that return value of a request is SUCCESS
   
  def _verifyStatus(self, xml):
    """Verify that return value of a request is SUCCESS"""
    self.status = int(xml.attrib['status'])
    if self.status != YastStatus.SUCCESS:
      raise Exception("Non-success return-value from Yast: " + str(self.status))


  # Converts XML data response to arrays of elements, projects and folders
  # @param xml should be the response-node of a data response
  # @param group group records, projects and folders. Will also make them
  #              indexable by their respective ids
  def _xmlDataToStruct(self, xml, group=True):
    try:
      if group:
        resp = {'records': {}, 'projects': {}, 'folders': {}, 'recordTypes': {}}
      else:
        resp = []

      nodes = list(xml.find('objects'))
      for item in nodes:
        if item.tag == 'record':
          typeId = int(item.find('typeId').text)
          variables = self._getNodeArray('variables', item)
	  	  
	  # Create record
          if typeId == 1: # Work record
            record = YastRecordWork(item.find('project').text,
                                    variables[0], variables[1], variables[2], variables[3])
          elif typeId == 3: # Phonecall record
            record = YastRecordPhonecall(item.find('project').text,
					 variables[0], variables[1], variables[2], variables[3], 
					 variables[4], variables[5])
          else: # Unknown record
            raise Exception('Unknown record type')	    
	  
	  # Add remaining data
          record.id = int(item.find('id').text)
          record.timeCreated = int(item.find('timeCreated').text)
          record.timeUpdated = int(item.find('timeUpdated').text)
          record.creator = int(item.find('creator').text)
          record.flags = int(item.find('flags').text)

          if group:
            resp['records'][record.id] = record
          else:
            resp.append(record)
	  
        elif item.tag == 'project':
          project = YastProject(item.find('name').text,
                                item.find('description').text,
                                item.find('primaryColor').text,
                                item.find('parentId').text)

	  # Add remaining data
          project.id = int(item.find('id').text)
          project.privileges = int(item.find('privileges').text)
          project.timeCreated = int(item.find('timeCreated').text)
          project.creator = int(item.find('creator').text)

          if group:
            resp['projects'][project.id] = project
          else:
            resp.append(project)
	  
        elif item.tag == 'folder':
          folder = YastFolder(item.find('name').text,
                              item.find('description').text,
                              item.find('primaryColor').text,
                              item.find('parentId').text)

	  # Add remaining data
          folder.id = int(item.find('id').text)
          folder.privileges = int(item.find('privileges').text)
          folder.timeCreated = int(item.find('timeCreated').text)
          folder.creator = int(item.find('creator').text)
          
          if group:
            resp['folders'][folder.id] = folder
          else:
            resp.append(folder)
	  
        elif item.tag == 'recordType':
          varTypeNodes = self._getNodeArrayNodes('variableTypes', item, 'variableType')
          variableTypes = []
          for vtNode in varTypeNodes:
            variableType = YastVariableType(vtNode.find('name').text,
                                            vtNode.find('valType').text)
            variableType.id = int(vtNode.find('id').text)
            variableTypes.append(variableType)
	  
	  
          recordType = YastRecordType(item.find('name').text,
					   variableTypes)
          recordType.id = int(item.find('id').text)

          if group:
            resp['recordTypes'][recordType.id] = recordType
          else:
            resp.append(recordType)
	  
      return resp
    
    except:
      self.status = YastStatus.LIB_XML_PARSE_ERROR
      # Propagate exception
      raise


  # Execute an API request using POST/GET
  # @param request full XML request in text format
  # @return Parsed XML object
  def _request(self, request):
    if self.requestMethodGet:
      conn = HTTPConnection(self.host, timeout=self.requestTimeout)
      conn.request('GET', self.apiPath + "?" + urlencode({'request': request}))
      response = conn.getresponse().read()
      conn.close()
    else:
      headers = {'Content-type': "application/x-www-form-urlencoded", 'Accept': "text/xml"}
      conn = HTTPConnection(self.host, timeout=self.requestTimeout)
      conn.request('POST', self.apiPath, urlencode({'request': request}), headers)
      response = conn.getresponse().read()
      conn.close()

      # Parse xml
      try:
        tree = ElementTree.fromstring(response)
      except:
        self.status = YastStatus.LIB_XML_PARSE_ERROR
        raise Exception("Error parsing response from Yast:\n" + response)

    return tree


  # Returns a structure of all XML nodes
  # @param xml XML node to convert to structure
  # @return a filled version of the fields structure. All None-elements
  #         will have values
  def _getXmlFields(self, xml):
    # Collect data in associative array
    fields = {}
    for node in list(xml):
      if node.tag != '#text':
	# Add node
        fields[node.tag] = node.text

    return fields
  



  # Updates an object array with data from Yast
  def _updateObjects(self, original, new):
    for o,n in zip(original, new):
      if isinstance(o, YastProject) or isinstance(o, YastFolder):
        o.id = n.id
        o.name = n.name
        o.description= n.description
        o.primaryColor = n.primaryColor
        o.parentId = n.parentId
        o.privileges = n.privileges
        o.timeCreated = n.timeCreated
        o.creator = n.creator
      
      elif isinstance(o, YastRecord):
        o.id = n.id
        o.typeId = n.typeId
        o.timeCreated= n.timeCreated
        o.timeUpdated = n.timeUpdated
        o.project = n.project
        o.variables = n.variables
        o.creator = n.creator
        o.flags = n.flags

 
  # Returns an array in a field, e.g. for a field named xyz,
  # an array is <xyz><v>1</v><v>2</v></xyz>. The values would
  # be 1,2
  def _getNodeArray(self, tag, xml, arrName='v'):
    items = list(xml.find(tag))
    arr = []
    for item in items:
      if item.tag == arrName:
        arr.append(item.text)

    return arr
   
 
 
  # Returns an array in a field, e.g. for a field named xyz,
  # an array is <xyz><v>1</v><v>2</v></xyz>. Returned as nodes
  def _getNodeArrayNodes(self, tag, xml, arrName='v'):
    items = list(xml.find(tag))
    arr = []
    for item in items:
      if item.tag == arrName:
        arr.append(item)
    
    return arr
  
