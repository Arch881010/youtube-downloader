function clear() {
    localStorage.setItem("textpad", "");
    Cookies.set("where", "");
    Cookies.set("error", "");
}

function edit(what) {
    const element = document.getElementById('storage_data_results');
    const start = `<p id="storage_data_results">`;
    const end = `</p>`
    if(what == 0) { 
        element.innerText = "";
    } else if(what == 1) {
        element.innerHTML = (start + `Text: ${localStorage.getItem('textpad')}` + end);
    } else if(what == 2) {
        element.innerHTML = (start + `Where: ${Cookies.get('where')}` + end);
    } else if(what == 99) {
        element.innerHTML = (start + `Text [Textpad]: ${localStorage.getItem('textpad')}<br>
        Where [General]: ${Cookies.get('where')}<br>
        Last Error [General]: ${Cookies.get('error') ?? "N/A"}<br><button type="button" class="btn btn-danger" id="clrstrg">Clear storage?</button><br>
        <script>function clear() {
            clear()
        };
        document.getElementById('clrstrg').setAttribute('onclick', clear)</script>` + end);
    }
}

function doLogic() {
    var init = document.getElementById('btn-0')
    var a = document.getElementById('btn-1');
    var b = document.getElementById('btn-2');
    var z = document.getElementById('btn-99');

    init.addEventListener("click", (event) => {edit("0")});
    a.addEventListener("click", (event) => {edit("1")});
    b.addEventListener("click", (event) => {edit("2")});
    z.addEventListener("click", (event) => {edit("99")});


};
doLogic();