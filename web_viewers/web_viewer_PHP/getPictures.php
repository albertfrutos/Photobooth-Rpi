<?php

	ini_set('display_errors', 1);
	ini_set('display_startup_errors', 1);
	error_reporting(E_ALL);
	
	header('Access-Control-Allow-Origin: *');

	/*
	$fileList = glob('full/*');
	foreach($fileList as $filename){
	if(is_file($filename)){
	    echo $filename, '<br>'; 
	}   
	}
	*/
	
	
	$pictures = array();
	
	
	
	$mydir = 'full'; 
	
	$myfiles = array_diff(scandir($mydir), array('.', '..')); 
	
	foreach($myfiles as $file){
	  $fullPath = "photos_full/" . $file;
	  $thumbPath = "photos_thumb/" . $file;
	  //echo "<img src='{$fullPath}' />";
	  array_push($pictures,array("filename" => $file, "url" => $fullPath, "url_thumb" => $thumbPath));
	}
	
	$arrayToSend = array("pictures" => $pictures);
	
	echo json_encode($arrayToSend);
	






?>