<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

if(empty($_FILES["myfile"]["name"])){
	echo "ERROR. No files present";
	return;
}	

processPicture($_FILES["myfile"],0,"full");
processPicture($_FILES["myfile"],1,"thumb");

function processPicture($myFile, $position, $type)
{		
	$error = $myFile["error"][$position]; 
	
    if ($error == UPLOAD_ERR_OK) {
    	
		$name = basename($myFile["name"][$position]);
		$target_file = "$type/$name";
		
		if ($myFile["size"][$position] > 10000000) { // limit size of 10MB
			echo "error: {$name} is too large. \n";
		}
		if (!move_uploaded_file($myFile["tmp_name"][$position], $target_file)){
			echo 'error:'.$myFile["error"][$position].' see /var/log/apache2/error.log for permission reason';
		}
	}
}

?>