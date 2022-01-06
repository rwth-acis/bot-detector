function valueCheck() {
    if (document.getElementById('time-period').checked) {
        document.getElementById('time-periods').style.display = 'block';
    } 
    else {
        document.getElementById('time-periods').style.display = 'none';
   }
}