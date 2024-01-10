/*
Hints:
Creating a new ejs file with its own route.

Steal the code from post.js into a new file.
Edit 'post.ejs' to your new .ejs file.
Return here, find "//Routers"
require your new route.
go towards bottom with other "app.use(...)"
app.use('/<where?>, route); //Route being your newly required route and where being /x. eg: /x, x
------------------------------

*/

var express = require('express');

const app = express(); //Create app
const cors = require('cors') //Allow Cors
require('dotenv').config()

var url = process.env['url'] ?? "http://127.0.0.1:3056/" 

app.use(cors()) //Enable Cors
const cookieParser = require('cookie-parser');
app.use(cookieParser()); //Enable Cookies

app.set('view engine', 'ejs'); //Render EJS

var path = require('path'); //Create ways to send files/

var config = {
    "PORT":3055,
    "DEV":false,
}

const PORT = config.PORT; //Init PORT
const dev = config.DEV; // Init DEV mode
const home_file = "index.ejs"; //home_file to dev/active in dev mode.
 
//app.use(express.static(path.join(__dirname, 'files/js'))); TODO: Make sure this gets pushed to the API section.


//Routers.
const about = require('./routes/about.js');
const download = require('./routes/download.js')
const fourofour = require('./routes/404.js');

app.all("*", async function (req, res, next) {
    return res.send("a")

    var uri = req.originalUrl;
    var cookies = req.cookies;
    if(uri != "favicon.ico" ) req.appendData = {
        "where":uri //res.cookie("where", uri)
    }

    next(); //Else, continue on.
})


app.get('/', function (req, res, next) { //Main, does not need router.
    try {
        var query = req.query;
        if (query.github == "true") {
            return res.send("Err 404, query not found. Please clear after ? in URL ")
            res.redirect("https://github.com/Arch881010/cmb-web");
        }
    } catch(err) {/* Do nothing */} //TODO: Check err against 'params are missing' vs req error itself. [Optional]
    var cookies = req.cookies;
    var cookieOK = 0;
    try {
        cookieOK = cookies.cookieOK;
    } catch(err) {}
    if (cookieOK == undefined || cookieOK == null) {
        cookieOK = 0;
        res.cookie("cookieOK", 0);
    }
    return res.cookie("where", "undefined").render(home_file, {x: cookieOK});
})

app.get('/url', (req, res) => {
    res.send(url);
})

app.get("/favicon.ico", (req, res, next) => {
    return res.send(""); //Missing asset.
})

app.use('/css', express.static('css'))
app.use('/about', about);
app.use('/videos', express.static('downloads'))
app.use('/download', download);

app.use('*', fourofour); //404 handeler.

app.listen(PORT, function (err) { //Launch server.
    if (err) console.log(err);
    console.log("Server listening on PORT", PORT);
});
