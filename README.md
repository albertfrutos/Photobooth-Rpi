# Photobooth

This project is a photobooth for Raspberry Pi, originally deeloped for RPi 4B, which uses raspicam (or clone/equivalent) and uploads the pictures to a server so they can be seen via a web viewer.

The Photobooth is written in Python for the Photobooth itself, and HTML, Javascript and PHP for the uploaders and viewers.

## Parts of the project

The Photobooth is compound by the RPi+software themselves, but also by a small custom home-made electronic board.

Power source for powering the RPi with 5V (12V power for flash and button light, is optional) is required.

### Electronics

Components:

* 1x Perforated board for PCB prototyping
* 1x ULN2003A Integrated circuit (flash control)
* 1x 4 watts, 12 volts MR16 LED bulb
* 1x arcade puch button (the one used included a built-in 12V LED)
* 1x 40-pin header for soldering into the board
* 1x 40-pin ribbon cable to connect the RPi header with the board header
* 1x micro switch (allows disabling the falsh via hardware without the need to restart the RPi and all the Photobooth)
* 1x jack barrel connector for the 12V source power
* 1x USB-C mount adapter
* 2x resistor (330 Ohm used)
* 2x LED (monitor upload and photobooth readiness)
* 1x SSD1036 OLED I2C screen

Components are assembled using the perforated board for PCB prototyping, according to the following schema (JST conenctors where used during the final board assembling).

![Electornics circuitry image](/readme_assets/electronic_board.jpg)

The board is connected to the RPi through a 40-pin ribbon cable, and enables connectivity with all the external components.

The barrel connector is used to connect the 12V power source that powers the ULN2003A integrated circuit, responsible for driving the flash and the button LED.

**NOTE:** If no 12V power source is plugged in, the photobooth can operate normally but the button LED and the flash will not work.

### <a id="configuration-files"></a>Configuration files

There are several configuration files that you will need to adapt and modify in order to make the Photobooth work properly:

* **config.json**: (rename the config_example.json file to config.json)this file configures the Photobooth itself. You can set up the pin numbers where you have connected each component, the directory names, enable frames in the picture, etc. An important part of this file to configure is the "upload", where the "upload_mode" (PHP and/or GDrive) can be selected and the application will directly handle the upload modes (one or both):

  * **PHP**: when "upload_mode" is configured as "PHP", then the pictures are uploaded to a web server. You need to place the *web_viewer_PHP* folder in a PHP web server and enter the url to the *multiple-upload.php* endpoint in "upload_PHP_endPoint". To view the pictures uploaded in this mode, the viewer in *web_viewers/web_viewer_PHP/index.html* must be used. You will need to put the URL endpoint for the *getPictures.php* file in  *js/gallery-scripts.js*.

  * **GDrive**: when "upload_mode" is configured as "GDrive", then the pictures are uploaded to a Google Drive Folder. In order to do this, you will need to get a token for Google Drive and complete the information in the *credentials_gdrive_example.json* with the credentials from Google and rename the file to *credentials.json*. You will also need to create Google Drive folders for the original and the thumbnail images and put their IDs in *upload_pictures_endPoint_full_resolution* and *upload_pictures_endPoint_thumbnail*. This mode takes a picture and uploads them to these folders and the connects to *jsonbin.io* to update a json file with the pictures' URLs. To view the pictures uploaded in this mode, the viewer in *web_viewers/web_viewer_GDrive/index.html* must be used but the BIN-ID and the APIKEY from jsonbin.io need to be obtained and introduced manually in *js/gallery-scripts.js*.

  * **GDrive/PHP or PHP/GDrive**: Pictures are uploaded to both places, in the order it has been configured.
  
  **NOTE**: *gallery-scripts-example.js* need to be renamed to *gallery-scripts.js* in both viewers.

### Misc parameters in config.json

* "upload_interval_check_connection_seconds" sets the number of seconds between internet connectivity checks. If there is no internet connection or it goes down, the Photobooth does not upload any pictures (as long as the check has been done between the connection being dropped and starting the upload). Once the connection is up again, then the upload is resumed.
* "pictures_upload_pictures": sets whether if the pictures have to be uploaded or not.

### Photobooth status during run and threading

While you are using the Photobooth, the OLED screen shows the local RPi IP (useful if you need to connect to it - i.e. via SSH or VNC - to fix something), the internet connection (online or offline) and the items waiting in the upload queue.

![Electornics circuitry image](/readme_assets/oled_screen_status.jpg)

The filenames of the pictures to upload are queued and uploaded by an independent thread, as well as the internet status and screen updating, which also has its own and independent thread.

## Viewers

The Photobooth can use the GDrive Viewer or the PHP Viewer (refer to [configuration files](#configuration-files)). They are themed with a polaroid-like aspect that show the thumbnails in the polaroid frames and once clicked load the full resolution image.

Both modes are webpages that once loaded in the web browser, make a query (each one to different endpoints) and load the images by themselves. The JSON file received by both viewers is the same:

```
{
  "pictures": [
    {
      "filename": "<filename>.<extension>",
      "url": "<url_to_original_full_resolution_image>",
      "url_thumb": "url_to_thumbnail_resolution_image"
    },
    ...
  ]
}
```

The viewers use this JSON's content to fetch the pictures from the client (your) side.

* **PHP mode** allows a much faster upload speed (as just uploads the file and it's done) but requires a web server supporting PHP. This mode just has an endpoint returning a JSON file.

* **GDrive mode** is a quite slower method, but allows hosting the viewer in a serverless system where the code must be static (such as GitHub pages). This mode has apikeys and unique endpoints in the javascript file, so the client side can get full (read and write) access to the jsonbin.io content.

## Logging

The code creates logs in the file *debug.log* and also shows them on the screen.
