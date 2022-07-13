let req = new XMLHttpRequest();

req.open("GET", "<URL-TO-getPictures.php>", true);
req.send();

// Placing of images into HTML
function galleryTemplate(picture) {
    return `
    <div hidden class="gallery">
        <figure class="polaroid">
            <img src="${picture.url_thumb}" data-full-image="${picture.url}">
            <figcaption> </figcaption>
        </figure>
    </div>
  `;
}


$(document).ready(function() {
    var options = {
        theme: "custom",
        // If theme == "custom" , the content option will be available to customize the logo
        content: '<img style="width:120px;" src="img/image_camera_SMALL.png" class="center-block">',
        message: '</br></br>Una mica de paciència, he anat a buscar les fotos...',
        backgroundColor: "#ffffff",
        textColor: "black"
    };
    HoldOn.open(options);
});

req.onreadystatechange = () => {
    if (req.readyState == XMLHttpRequest.DONE) {
        console.log(req.responseText);
        jsonResponse = JSON.parse(req.responseText);
        document.getElementById("app").innerHTML = jsonResponse.pictures.map(galleryTemplate).join("")

        // Randomize polaroid images
        $('.polaroid').each(function() {
            const depth = Math.floor(Math.random() * 100);
            const rotate = Math.random() * 41 - 15;

            $(this).css({
                'z-index': depth,
                'transform': 'rotateZ(' + rotate + 'deg)'
            });
        });

        $(".gallery").click(function() {
            var options = {
                theme: "custom",
                // If theme == "custom" , the content option will be available to customize the logo
                content: '<img style="width:120px;" src="img/image_camera_SMALL.png" class="center-block">',
                message: '<p style="text-align: center;"></br></br>&nbsp;Espera mentre et porto la foto en gran!</p>',
                backgroundColor: "#ffffff",
                textColor: "black"
            };
            HoldOn.open(options);

            $(".modal-content").hide()
            var a = $(this).find('img').attr('data-full-image')
            $("#imgModal").attr('src', $(this).find('img').attr('data-full-image'))
            $("#myModal").modal();
            $('#imgModal').on('load', function(event) {
                HoldOn.close();
                $(".modal-content").fadeIn(1000);

            });

        });

        $('div#app img').on('load', function(event) {
            HoldOn.close()
            $("#mainDiv").removeAttr("hidden").fadeIn(2000);
            $(event.currentTarget).parent().parent().removeAttr("hidden");
            $("header").html("<b>Els Mombitos... fem un any!</b><img src='img/party_flags.png' width='100%' height='auto' />");
        });
    }
};