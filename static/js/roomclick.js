function selectedType() {

    var typeValue = document.getElementById('type').value;

     // Get the image source
    var imageSrc = document.getElementById('image').getAttribute('src');


    document.getElementById("selectRoom").innerHTML=typeValue;
    
}