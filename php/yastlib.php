<?php
/**
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

Yast PHP LIB

Version:
0.8 - First release

0.9 - Bugfixes++
 * Improved error detection in XML parse
 * Added option for connecting to Yast using HTTPS

*/

/** Status messages returned from Yast API. Return-value from last API call can
 *  be read through $yast->getStatus() given $yast = Yast() */
class YastStatus {
  const SUCCESS = 0;
  const UNKNOWN = 1;
  const ACCESS_DENIED = 3;
  const NOT_LOGGED_IN = 4;
  const LOGIN_FAILURE = 5;
  const INVALID_INPUT = 6;
  const SUBSCRIPTION_REQUIRED = 7;
  const DATA_FORMAT_ERROR = 8;
  const NO_REQUEST = 9;
  const INVALID_REQUEST = 10;
  const MISSING_FIELDS = 11;
  const REQUEST_TOO_LARGE = 12;
  const SERVER_MAINTENANCE = 13;
  
  const DUPLICATE_ITEM = 100;
  const INSUFFICIENT_PRIVILEGES = 101;
  const UNKNOWN_RECORDTYPE = 200;
  const UNKNOWN_PROJECT = 201;
  const UNKNOWN_FOLDER = 202;
  const UNKNOWN_RECORD = 203;
  const PARENT_IS_SELF = 204;
  const VARIABLETYPE_MISMATCH = 205;
  const UNKNOWN_SETTING = 300;
  const INVALID_SETTING_VALUE = 301;
  const PASSWORD_FORMAT_INVALID = 800;
  const UNKNOWN_REPORT_FORMAT = 801;
  const UNKNOWN_GROUPBY_VALUE = 802;

  //Reserved for client side
  const XML_PARSE_ERROR = 40;
  const LIB_NOT_LOGGED_IN = 41;
  const LIB_EXCEPTION = 41;

  const CLI_ARGUMENT_ERROR = 60;
  const CLI_LOGIN_REQUIRED = 61;
  const CLI_EXCEPTION = 62;
}

/** Generic yast record */
class YastRecord {
  public $id = -1;
  public $typeId = -1;
  public $timeCreated = -1;
  public $timeUpdated = -1;
  public $project = -1;
  public $variables = null;
  public $creator = -1;
  public $flags = 0;

  /** User data. Will not be synchronized to Yast. You can
   *  fill this with whatever you like */
  public $userData = null;

  /** Construct a generic yast record */
  public function __construct($typeId, $project, $variables) {
    $this->typeId = $typeId;
    $this->project = $project;
    $this->variables = $variables;
  }
  
  /** Returns XML description of record*/
  public function toXml($includeId=true, $includeData=true) {
    return '<record>' .
      ($includeId ? '<id>' . $this->id . '</id>' : '') .
      ($includeData ? 
       '<typeId>' . $this->typeId . '</typeId>' .
       '<project>' . $this->project . '</project>' : '') .
      '</record>';
  }
}

/** Yast Work record */
class YastRecordWork extends YastRecord {
  public $typeName = "work";

  /** Construct a work record */
  public function __construct($project, $startTime, $endTime, $comment, $isRunning) {
    parent::__construct(1, (int) $project, array('startTime' => (int) $startTime,
						 'endTime' => (int) $endTime,
						 'comment' => $comment,
						 'isRunning' => (int) $isRunning));
  }

  /** Returns XML description of record*/
  public function toXml($includeId=true, $includeData=true) {
    return '<record>' .
      ($includeId ? '<id>' . $this->id . '</id>' : '') .
      ($includeData ? 
       '<typeId>1</typeId>' .
       '<project>' . $this->project . '</project>' .
       '<variables><v>' . $this->variables['startTime'] . '</v><v>' . $this->variables['endTime'] . '</v>' .
       '<v><![CDATA[' . $this->variables['comment'] . ']]></v><v>' . $this->variables['isRunning'] . '</v></variables>' : '') .
      '</record>';
  }
}

/** Yast Phonecall record */
class YastRecordPhonecall extends YastRecord {
  public $typeName = "phonecall";

  /** Construct a work record */
  public function __construct($project, $startTime, $endTime, $comment, $isRunning, $phoneNumber, $outgoing) {
    parent::__construct(3, (int) $project, array('startTime' => (int) $startTime,
						 'endTime' => (int) $endTime,
						 'comment' => $comment,
						 'isRunning' => (int) $isRunning,
						 'phoneNumber' => $phoneNumber,
						 'outgoing' => (int) $outgoing));
  }

  /** Returns XML description of record */
  public function toXml($includeId=true, $includeData=true) {
    return '<record>' .
      ($includeId ? '<id>' . $this->id . '</id>' : '') .
      ($includeData ? 
       '<typeId>3</typeId>' .
       '<project>' . $this->project . '</project>' .
       '<variables><v>' . $this->variables['startTime'] . '</v><v>' . $this->variables['endTime'] . '</v>' .
       '<v><![CDATA[' . $this->variables['comment'] . ']]></v><v>' . $this->variables['isRunning'] . '</v>' .
       '<v><![CDATA[' . $this->variables['phoneNumber'] . ']]></v><v>' . $this->variables['outgoing'] . '</v></variables>' : '') .
      '</record>';
  }
}

/** Yast project */
class YastProject {
  public $id = -1;
  public $name = "";
  public $description = "";
  public $primaryColor = "";
  public $parentId = -1;
  public $privileges = 0;
  public $timeCreated = -1;
  public $creator = -1;

  /** User data. Will not be synchronized to Yast */
  public $userData = null;

  /** Construct a yast project */
  public function __construct($name, $description, $primaryColor, $parentId=0) {
    $this->name = $name;
    $this->description = $description;
    $this->primaryColor = $primaryColor;
    $this->parentId = (int) $parentId;
  }  
  
  /** Returns XML description of project */
  public function toXml($includeId=true, $includeData=true) {
    return '<project>' .
      ($includeId ? '<id>' . $this->id . '</id>' : '') .
      ($includeData ? 
       '<name><![CDATA[' . $this->name . ']]></name>' .
       '<description><![CDATA[' . $this->description . ']]></description>' .
       '<primaryColor><![CDATA[' . $this->primaryColor . ']]></primaryColor>' .
       '<parentId>' . $this->parentId . '</parentId>' .
       '<flags>0</flags>' : '') .
      '</project>';
  }

}
/** Yast folder */
class YastFolder {
  public $id = -1;
  public $name = "";
  public $description = "";
  public $primaryColor = "";
  public $parentId = -1;
  public $privileges = 0;
  public $timeCreated = -1;
  public $creator = -1;

  /** User data. Will not be synchronized to Yast */
  public $userData;

  /** Construct a yast folder */
  public function __construct($name, $description, $primaryColor, $parentId=0) {
    $this->name = $name;
    $this->description = $description;
    $this->primaryColor = $primaryColor;
    $this->parentId = (int) $parentId;
  }    
  
  /** Returns XML description of folder */
  public function toXml($includeId=true, $includeData=true) {
    return '<folder>' .
      ($includeId ? '<id>' . $this->id . '</id>' : '') .
      ($includeData ? 
       '<name><![CDATA[' . $this->name . ']]></name>' .
       '<description><![CDATA[' . $this->description . ']]></description>' .
       '<primaryColor><![CDATA[' . $this->primaryColor . ']]></primaryColor>' .
       '<parentId>' . $this->parentId . '</parentId>' .
       '<flags>0</flags>' : '') .
      '</folder>';
  }
}

/** Yast Record Type */
class YastRecordType {
  public $id = -1;
  public $name = "";
  public $variableTypes = null;

  public function __construct($name, $variableTypes) {
    $this->name = $name;
    $this->variableTypes = $variableTypes;
  }
}

/** Yast Variable Type */
class YastVariableType {
  public $id = -1;
  public $name = "";
  public $valType = -1;
  
  public function __construct($name, $valType) {
    $this->name = $name;
    $this->valType = (int) $valType;
  }
}


/** Yast API */
class Yast {
  
  /** Host */
  public $host = 'www.yast.com';
  /** API path */
  public $apiPath = '/1.0/';
  /** Download path */
  public $dlPath = '/file.php';
  /** Request method. True for GET, false for POST */
  public $requestMethodGet = FALSE;
  /** Use https instead of http */
  public $useHttps = FALSE;
  /** Request timeout in seconds */
  public $requestTimeout = 300;

  /** Previous error code */
  public $status = YastStatus::SUCCESS;

  /** Propagate exceptions out of Yast class */
  public $propagateExceptions = FALSE;

  /** Username from last login */
  public $user = null;
  /** Hash from last login */
  public $hash = null;

  /**
   * Login as a given user.
   * @param user username 
   * @param password password for given user
   * @return hash hash to use for further requests on this user
   */
  public function login($user, $password) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $resp = $this->request('<request req="auth.login" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<password><![CDATA[' . $password . ']]></password>' .
			     '</request>');

      $this->verifyStatus($resp);
      $this->hash = $this->getXmlField($resp, 'hash');
      $this->user = $user;
      return $this->hash;
    }
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }
  
  /**
   * Forget about previous login
   */
  public function clearLogin() {
    $this->hash = null;
    $this->user = null;
    return TRUE;
  }

  /**
   * Get user info
   * @param user username
   * @param hash user hash
   * @return map of user info
   */
  public function userGetInfo($user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);

      $resp = $this->request('<request req="user.getInfo" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '</request>');

      $this->verifyStatus($resp);
      return $this->getXmlFields($resp);
    }
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }

  /**
   * Get all user settings
   * @param user username
   * @param hash user hash
   * @return map of settings or FALSE on failure
   */
  public function userGetSettings($user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);
      
      $resp = $this->request('<request req="user.getSettings" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '</request>');
      
      $this->verifyStatus($resp);

      //Create and return map of settings
      $map = array();
      $keys = $resp->getElementsByTagName('keys')->item(0)->childNodes;
      $vals = $resp->getElementsByTagName('values')->item(0)->childNodes;
      for ($i=0; $i < $keys->length; $i++) {
	if ($keys->item($i)->nodeName == 'v' && $vals->item($i)->nodeName == 'v') {
	  $map[$keys->item($i)->nodeValue] = $vals->item($i)->nodeValue;
	}
      }
      return $map;
    }
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }    
  }

  /**
   * Set a user setting
   * @param user username
   * @param hash user hash
   * @param key setting key
   * @param value new value
   * @return TRUE on success, FALSE on error
   */
  public function userSetSetting($key, $value, $user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);
      
      $resp = $this->request('<request req="user.setSetting" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '<key><![CDATA[' . $key . ']]></key>' .
			     '<value><![CDATA[' . $value . ']]></value>' .
			     '</request>');
      
      $this->verifyStatus($resp);
      return TRUE;
    }
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }  
   

  /** 
   * Add records, projects and folders to Yast
   * @param user username
   * @param hash user hash
   * @param objects Single object or array of objects to add. Objects are updated
   *                with id, etc. The same objects are given as return value
   * @return FALSE on error, $objects array if successful
   */
  public function add($objects, $user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);

      //Accumulate XML description of objects
      $xmlObj = '';
      if (is_array($objects)) {
	foreach ($objects as $o) {
	  $xmlObj .= $o->toXml(false, true);
	}
      }
      else {
	$xmlObj = $objects->toXml(false, true);
      }
      
      //Transmit request
      $resp = $this->request('<request req="data.add" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '<objects>' . $xmlObj . '</objects>' .
			     '</request>');
      
      $this->verifyStatus($resp);    
      $struct = $this->xmlDataToStruct($resp, false);

      //Apply new information to objects. Objects are added in sequence,
      //so the first object added will be the first in its respective list
      $this->updateObjects(is_array($objects) ? $objects : array($objects), $struct);
      return $objects;
    }  
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }

  /** 
   * Change records, projects and folders in Yast
   * @param user username
   * @param hash user hash
   * @param objects Single object or array of objects to change. 
   *                The same objects are given as return value
   * @return FALSE on error, $objects array if successful
   */
  public function change($objects, $user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);
      
      //Accumulate XML description of objects
      $xmlObj = '';
      if (is_array($objects)) {
	foreach ($objects as $o) {
	  $xmlObj .= $o->toXml(true, true);
	}
      }
      else {
	$xmlObj = $objects->toXml(true, true);
      }

      //Transmit request
      $resp = $this->request('<request req="data.change" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '<objects>' . $xmlObj . '</objects>' .
			     '</request>');

      $this->verifyStatus($resp);    
      $struct = $this->xmlDataToStruct($resp, false);

      //Apply new information to objects. Objects are added in sequence,
      //so the first object added will be the first in its respective list
      $this->updateObjects(is_array($objects) ? $objects : array($objects), $struct);
      return $objects;
    }
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }


  /** 
   * Delete records, projects and folders in Yast
   * @param user username
   * @param hash user hash
   * @param objects Single object or array of objects to delete
   * @return FALSE on error, TRUE if successful
   */
  public function delete($objects, $user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);

      //Accumulate XML description of objects
      $xmlObj = '';
      if (is_array($objects)) {
	foreach ($objects as $o) {
	  $xmlObj .= $o->toXml(true, false);
	}
      }
      else {
	$xmlObj = $objects->toXml(true, false);
      }

      //Transmit request
      $resp = $this->request('<request req="data.delete" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '<objects>' . $xmlObj . '</objects>' .
			     '</request>');
      
      $this->verifyStatus($resp);    
      return TRUE;
    }  
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }
  

  /**
   * Returns records of a given user
   * @param user username
   * @param hash user hash
   * @param options associative array of options
   * @return array of records
   */
  public function getRecords($options=null, $user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);

      $resp = $this->request('<request req="data.getRecords" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     (!isset($options) ? '' :
			      (array_key_exists('timeFrom', $options) ? '<timeFrom>' . $options['timeFrom'] . '</timeFrom>' : '') .
			      (array_key_exists('timeTo', $options) ? '<timeTo>' . $options['timeTo'] . '</timeTo>' : '') .
			      (array_key_exists('typeId', $options) ? '<typeId>' . $options['typeId'] . '</typeId>' : '') .
			      (array_key_exists('parentId', $options) ? '<parentId>' . $options['parentId'] . '</parentId>' : '') .
			      (array_key_exists('id', $options) ? '<id>' . $options['id'] . '</id>' : '')) .
			     '</request>');

      $this->verifyStatus($resp);    
      $struct = $this->xmlDataToStruct($resp);
      return $struct['records'];
    }  
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }


  /**
   * Returns projects of a given user
   * @param user username
   * @param hash user hash
   * @return array of projects
   */
  public function getProjects($user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);

      $resp = $this->request('<request req="data.getProjects" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '</request>');

      $this->verifyStatus($resp);    
      $struct = $this->xmlDataToStruct($resp);
      return $struct['projects'];
    }  
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }
  
  /**
   * Returns folders of a given user
   * @param user username
   * @param hash user hash
   * @return array of folders
   */
  public function getFolders($user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);

      $resp = $this->request('<request req="data.getFolders" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '</request>');
      
      $this->verifyStatus($resp);    

      $struct = $this->xmlDataToStruct($resp);
      return $struct['folders'];
    }  
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    } 
  }

  /**
   * Returns record types
   * @param user username
   * @param hash user hash
   * @return array of record types
   */
  public function getRecordTypes($user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);

      $resp = $this->request('<request req="meta.getRecordTypes" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '</request>');
      
      $this->verifyStatus($resp);    

      $struct = $this->xmlDataToStruct($resp);
      return $struct['recordTypes'];
    }  
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    } 
  }

  /**
   * Returns report data
   * @param user username
   * @param hash user hash
   * @param reportFormat format of report
   * @param options
   * @return raw report data or FALSE on failure
   */
  public function getReport($reportFormat, $options=null, $user=null, $hash=null) {
    $this->m_status = YastStatus::SUCCESS;
    try {
      $this->verifyLogin($user, $hash);

      //Request report
      $resp = $this->request('<request req="report.getReport" id="133">' .
			     '<user><![CDATA[' . $user . ']]></user>' .
			     '<hash><![CDATA[' . $hash . ']]></hash>' .
			     '<reportFormat>' . $reportFormat . '</reportFormat>' .
			     (!isset($options) ? '' :
			      (array_key_exists('timeFrom', $options) ? '<timeFrom>' . $options['timeFrom'] . '</timeFrom>' : '') .
			      (array_key_exists('timeTo', $options) ? '<timeTo>' . $options['timeTo'] . '</timeTo>' : '') .
			      (array_key_exists('typeId', $options) ? '<typeId>' . $options['typeId'] . '</typeId>' : '') .
			      (array_key_exists('parentId', $options) ? '<parentId>' . $options['parentId'] . '</parentId>' : '') .
			      (array_key_exists('groupBy', $options) ? '<groupBy><![CDATA[' . $options['groupBy'] . ']]></groupBy>' : '') .
			      (array_key_exists('constraints', $options) ? '<constraints><![CDATA[' . $options['constraints'] . ']]></constraints>' : '')) .
			     '</request>');

      $this->verifyStatus($resp);
      $fields = $this->getXmlFields($resp);

      //Download
      $file = file_get_contents(($this->useHttps ? 'https://' : 'http://') . $this->host . $this->dlPath . '?' . 
				implode('&', array('type=report',
						   'id=' . $fields['reportId'],
						   'hash=' . $fields['reportHash'],
						   'user=' . urlencode($user),
						   'userhash=' . $hash)));
      return $file;
    }  
    catch (Exception $e) {
      if ($this->status == YastStatus::SUCCESS) {
	$this->status = YastStatus::LIB_EXCEPTION;
      }
      if ($this->propagateExceptions) {
	throw $e;
      }
      return FALSE;
    }
  }   

  /** Returns status of prevous access */
  public function getStatus() {
    return $this->status;
  }

  /**
   * If $user and $hash are not specified, require that 
   * $this->user and $this->hash are specified, and
   * set $user and $hash to them
   */
  private function verifyLogin(&$user, &$hash) {
    if ($user === null || $hash === null) {
      //Require previous login
      if ($this->user !== null && $this->hash !== null) {
	$user = $this->user;
	$hash = $this->hash;
      }
      else {
	$this->status = YastStatus::LIB_NOT_LOGGED_IN;
	throw new Exception("Library function called without user/hash without prior login");
      }
    }
  }
	

  /**
   * Verify that return value of a request is SUCCESS
   */
  private function verifyStatus($xml) {
    $this->status = $this->getXmlAttribute($xml, 'status');
    if ($this->status != YastStatus::SUCCESS) {
      throw new Exception("Non-success return-value from Yast: " . $this->status);
    }
  }

  /**
   * Converts XML data response to arrays of elements, projects and folders
   * @param xml should be the response-node of a data response
   * @param group group records, projects and folders. Will also make them
   *              indexable by their respective ids
   */
  private function xmlDataToStruct($xml, $group=true) {
    try {
      if ($group) {
	$resp = array('records' => array(), 'projects' => array(), 'folders' => array(), 'recordTypes' => array());
      }
      else {
	$resp = array();
      }

      $nodes = $xml->getElementsByTagName('objects')->item(0)->childNodes;
      for ($i=0; $i < $nodes->length; $i++) {
	$item = $nodes->item($i);
	switch ($item->nodeName) {
	case 'record':
	  $typeId = $this->getField('typeId', $item);
	  $variables = $this->getNodeArray('variables', $item);
	  	  
	  //Create record
	  switch ($typeId) {
	  case 1: //Work record
	    $record = new YastRecordWork($this->getField('project', $item),
					 $variables[0], $variables[1], $variables[2], $variables[3]);
	    break;
	  case 3: //Phonecall record
	    $record = new YastRecordPhonecall($this->getField('project', $item),
					 $variables[0], $variables[1], $variables[2], $variables[3], 
					 $variables[4], $variables[5]);
	    break;
	  default: //Unknown record
	    throw new Exception('Unknown record type');	    
	  }
	  
	  //Add remaining data
	  $record->id = (int) $this->getField('id', $item);
	  $record->timeCreated = (int) $this->getField('timeCreated', $item);
	  $record->timeUpdated = (int) $this->getField('timeUpdated', $item);
	  $record->creator = (int) $this->getField('creator', $item);
	  $record->flags = (int) $this->getField('flags', $item);

	  if ($group) {
	    $resp['records'][$record->id] = $record;
	  }
	  else {
	    $resp[] = $record;
	  }
	  break;

	case 'project':
	  $project = new YastProject($this->getField('name', $item),
				     $this->getField('description', $item),
				     $this->getField('primaryColor', $item),
				     $this->getField('parentId', $item));

	  //Add remaining data
	  $project->id = (int) $this->getField('id', $item);
	  $project->privileges = (int) $this->getField('privileges', $item);
	  $project->timeCreated = (int) $this->getField('timeCreated', $item);
	  $project->creator = (int) $this->getField('creator', $item);

	  if ($group) {
	    $resp['projects'][$project->id] = $project;
	  }
	  else {
	    $resp[] = $project;
	  }
       	  break;

	case 'folder':
	  $folder = new YastFolder($this->getField('name', $item),
				   $this->getField('description', $item),
				   $this->getField('primaryColor', $item),
				   $this->getField('parentId', $item));

	  //Add remaining data
	  $folder->id = (int) $this->getField('id', $item);
	  $folder->privileges = (int) $this->getField('privileges', $item);
	  $folder->timeCreated = (int) $this->getField('timeCreated', $item);
	  $folder->creator = (int) $this->getField('creator', $item);

	  if ($group) {
	    $resp['folders'][$folder->id] = $folder;
	  }
	  else {
	    $resp[] = $folder;
	  }
       	  break;

	case 'recordType':
	  $varTypeNodes = $this->getNodeArrayNodes('variableTypes', $item, 'variableType');
	  $variableTypes = array();
	  foreach ($varTypeNodes as $vtNode) {
	    $variableType = new YastVariableType($this->getField('name', $vtNode),
						 $this->getField('valType', $vtNode));
	    $variableType->id = (int) $this->getField('id', $vtNode);
	    $variableTypes[] = $variableType;
	  }
	  
	  $recordType = new YastRecordType($this->getField('name', $item),
					   $variableTypes);
	  $recordType->id = (int) $this->getField('id', $item);

	  if ($group) {
	    $resp['recordTypes'][$recordType->id] = $recordType;
	  }
	  else {
	    $resp[] = $recordType;
	  }
	}
      }
      return $resp;
      
    }
    catch (Exception $e) {
      $this->status = YastStatus::LIB_XML_PARSE_ERROR;
      //Propagate exception
      throw $e;
    }
  } 
    

  /**
   * Execute an API request using POST/GET
   * @param request full XML request in text format
   * @return Parsed XML object
   */
  private function request($request) {
    if ($this->requestMethodGet) {
      //Request using GET
      $responseBody = file_get_contents(($this->useHttps ? 'https://' : 'http://') . $this->host . $this->apiPath . "?request=" . urlencode($request), false,
					stream_context_create(array('http' => array('timeout' => $this->requestTimeout))));
    }
    else {
      //Request using POST
      $data = http_build_query(array('request' => $request));
      $response = file_get_contents(($this->useHttps ? 'https://' : 'http://') . $this->host . $this->apiPath, false, 
				    stream_context_create(array('http' => array('method' => 'POST', 
										'header' => "Content-type: application/x-www-form-urlencoded\r\n" .
										            "Accept: text/xml\r\n", 
										'timeout' => $this->requestTimeout,
										'content' => $data))));
    }
    
    $xmlDoc = new DOMDocument();
    if ($xmlDoc->loadxml(trim($response), LIBXML_NOERROR | LIBXML_NOWARNING) !== TRUE) {
      $this->status = YastStatus::LIB_XML_PARSE_ERROR;
      throw new Exception("Error parsing response from Yast:\n" . $response);
    }
    return $xmlDoc->documentElement;
  }

  /**
   * Returns a structure of all XML nodes
   * @param xml XML node to convert to structure
   * @return a filled version of the $fields structure. All null-elements
   *         will have values
   */
  private function getXmlFields($xml) {
    //Collect data in associative array
    $fields = array();
    $childNodes = $xml->childNodes;
    $childCount = $childNodes->length;
    for ($i=0; $i<$childCount; $i++) {
      $node = $childNodes->item($i);
      if ($node->nodeName != '#text') {
	//Add node
	$fields[$node->nodeName] = utf8_decode($node->nodeValue);
      }
    }
    return $fields;
  }


  /**
   * Updates an object array with data from Yast
   */
  private function updateObjects($original, $new) {
    $oArr = new ArrayObject($original);
    $nArr = new ArrayObject($new);
    $oIter = $oArr->getIterator();
    $nIter = $nArr->getIterator();
    
    while ($oIter->valid() && $nIter->valid()) {
      $o = $oIter->current();
      $n = $nIter->current();
      if ($o instanceof YastProject || $o instanceof YastFolder) {
	$o->id = $n->id;
	$o->name = $n->name;
	$o->description= $n->description;
	$o->primaryColor = $n->primaryColor;
	$o->parentId = $n->parentId;
	$o->privileges = $n->privileges;
	$o->timeCreated = $n->timeCreated;
	$o->creator = $n->creator;
      }
      else if ($o instanceof YastRecord) {
	$o->id = $n->id;
	$o->typeId = $n->typeId;
	$o->timeCreated= $n->timeCreated;
	$o->timeUpdated = $n->timeUpdated;
	$o->project = $n->project;
	$o->variables = $n->variables;
	$o->creator = $n->creator;
	$o->flags = $n->flags;
      }
      $oIter->next();
      $nIter->next();
    }	
  }


  /**
   * Returns the value of an XML node field
   * @param xml XML node to check
   * @param field name of field in node
   * @return field value or FALSE on error
   */
  private function getXmlField($xml, $field) {
    $items = $xml->getElementsByTagName($field);
    if ($items->length == 1) {
      return $items->item(0)->nodeValue;
    }
    else {
      throw new Exception("Could not find expected XML tag " . $field);
    }
  }

  /**
   * Returns the value of an xml attribute. 
   * @param xml XML node 
   * @param attribute name of attribute in node
   * @return attribute value on success, FALSE on error
   */
  private function getXmlAttribute($xml, $attribute) {
    $node = $xml->attributes->getNamedItem($attribute);
    if ($node !== null) {
      return $node->nodeValue;
    }
    else {
      throw new Exception("Could not find expected XML attribure " . $field);
    }
  }

  /** Returns the value of a field */
  private function getField($tag, $xml) {
    $items = $xml->getElementsByTagName($tag);
    return $items->item(0)->nodeValue;
  }

  /** 
   * Returns an array in a field, e.g. for a field named xyz,
   * an array is <xyz><v>1</v><v>2</v></xyz>. The values would
   * be 1,2
   */
  private function getNodeArray($tag, $xml, $arrName='v') {
    $items = $xml->getElementsByTagName($tag)->item(0)->childNodes;
    $arr = array();
    for ($i=0; $i < $items->length; $i++) {
      if ($items->item($i)->nodeName == $arrName) {
	$arr[] = $items->item($i)->nodeValue;
      }
    }
    return $arr;
  } 
 
  /** 
   * Returns an array in a field, e.g. for a field named xyz,
   * an array is <xyz><v>1</v><v>2</v></xyz>. Returned as nodes
   */
  private function getNodeArrayNodes($tag, $xml, $arrName='v') {
    $items = $xml->getElementsByTagName($tag)->item(0)->childNodes;
    $arr = array();
    for ($i=0; $i < $items->length; $i++) {
      if ($items->item($i)->nodeName == $arrName) {
	$arr[] = $items->item($i);
      }
    }
    return $arr;
  }
}

?>
