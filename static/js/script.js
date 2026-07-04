console.log("Blood Bank Management System Loaded Successfully");

// Back to Top Button

let mybutton = document.getElementById("topBtn");

window.onscroll = function () {

    if(document.body.scrollTop > 300 || document.documentElement.scrollTop > 300){

        mybutton.style.display="block";

    }

    else{

        mybutton.style.display="none";

    }

}

function topFunction(){

    window.scrollTo({

        top:0,

        behavior:"smooth"

    });

}