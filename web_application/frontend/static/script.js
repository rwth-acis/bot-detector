

function valueCheck() {
    if (document.getElementById('time-period').checked) {
        document.getElementById('time-periods').style.display = 'block';

    } 
    else {
        document.getElementById('time-periods').style.display = 'none';

   }
}

function displaymenu() {
        if ($("li").css('display') == 'none'){
        console.log("a");
            $("li").css('display', 'block');
        } else if ($("li").css('display') == 'block'){
            $("li").css('display', 'none');
        }

}


