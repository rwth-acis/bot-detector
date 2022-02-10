
$(document).ready(function(){
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