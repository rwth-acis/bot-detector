
$(document).ready(function(){
        $('[data-toggle="tooltip"]').tooltip();

        var today = new Date();
        var dd = today.getDate();
        var mm = today.getMonth() + 1; //January is 0!
        var yyyy = today.getFullYear();

        if (dd < 10) {
           dd = '0' + dd;
        }

        if (mm < 10) {
           mm = '0' + mm;
        }

        today = yyyy + '-' + mm + '-' + dd;
        document.getElementById("start-date").setAttribute("max", today);
        document.getElementById("end-date").setAttribute("max", today);
        var week = new Date();
        week.setDate(week.getDate() - 7);
        var dd = week.getDate();
        var mm = week.getMonth() + 1; //January is 0!
        var yyyy = week.getFullYear();

        if (dd < 10) {
            dd = '0' + dd;
        }

        if (mm < 10) {
            mm = '0' + mm;
        }

        week = yyyy + '-' + mm + '-' + dd;
        document.getElementById("start-date").setAttribute("min", week);
        document.getElementById("end-date").setAttribute("min", week);
});

function valueCheckMedia() {
    if (($('input[name="areaParameters2"]')[1].checked)&&($('input[name="areaParameters3"]')[0].checked)) {
        $('input[name="areaParameters2"]')[2].checked = true;

    }

}

function valueCheckLinks() {
    if (($('input[name="areaParameters2"]')[1].checked)&&($('input[name="areaParameters3"]')[0].checked)) {
        $('input[name="areaParameters3"]')[2].checked = true;

    }

}

function hideBasic() {
    var elementsHide = document.getElementsByClassName("hide-basic");
    var elementsDisplay = document.getElementsByClassName("hide-advanced");

    for (var i = 0; i < elementsHide.length; i++){
        elementsHide[i].style.display = "none";
    }

    for (var i = 0; i < elementsDisplay.length; i++){
        elementsDisplay[i].style.display = "block";
    }

    var elementsDisplay = document.getElementsByClassName("hide-real-time-span");
    for (var i = 0; i < elementsDisplay.length; i++){
        elementsDisplay[i].style.display = "inline";
    }


}

function hideAdvanced() {
    var elementsHide = document.getElementsByClassName("hide-advanced");
    var elementsDisplay = document.getElementsByClassName("hide-basic");

    for (var i = 0; i < elementsHide.length; i++){
        elementsHide[i].style.display = "none";
    }

    for (var i = 0; i < elementsDisplay.length; i++){
        elementsDisplay[i].style.display = "block";
    }

    searchOptionCheck();

}


function searchOptionCheck() {
    if (document.getElementById('real-time').checked) {
        var elementsHide = document.getElementsByClassName("hide-real-time");
        for (var i = 0; i < elementsHide.length; i++){
                elementsHide[i].style.display = "none";
        }
        var elementsDisplay = document.getElementsByClassName("show-real-time-span");
        for (var i = 0; i < elementsDisplay.length; i++){
            elementsDisplay[i].style.display = "inline";
        }
        var elementsHide = document.getElementsByClassName("hide-real-time-span");
        for (var i = 0; i < elementsHide.length; i++){
            elementsHide[i].style.display = "none";
        }

    }
    else {
        var elementsDisplay = document.getElementsByClassName("hide-real-time");
        for (var i = 0; i < elementsDisplay.length; i++){
            elementsDisplay[i].style.display = "block";
        }
        var elementsDisplay = document.getElementsByClassName("hide-real-time-span");
        for (var i = 0; i < elementsDisplay.length; i++){
            elementsDisplay[i].style.display = "inline";
        }
        var elementsHide = document.getElementsByClassName("show-real-time-span");
        for (var i = 0; i < elementsHide.length; i++){
            elementsHide[i].style.display = "none";
        }


   }
}