const express = require('express');

const index = express.Router();

const testCookies = require('../src/helpers/testCookies.js');

index.get('/', (req, res, next) => { //This becomes /about
    var cookieOK = testCookies(req, res);

    return res.cookie("where", "download").render("download.ejs", {x: cookieOK});
})

index.post('/', async (req, res, next) => {
    //exmp vid https://youtu.be/pCeVD_jhKlw?si=55biMjAQf69-Iph_ || https://www.youtube.com/watch?v=pCeVD_jhKlw
    var query = req.query.url;
    console.log(`Downloading ${query}.`);
    if(!query.includes("https://")) return res.status(400).send("Missing \"https://\" in URL.")
    if(!query.includes(".com") && !query.includes(".be")) return res.status(400).send("Missing \".com\"/\".be\" in URL.");
    if(!query.includes("youtube") && !query.includes("youtu.be")) return res.status(400).send("Missing the whole \"youtube\"/\"youtu.be\" in the URL.")
    var brkURL = query.split("/");
    console.log(brkURL);
    var inf = brkURL[3];
    var act = "";
    if (query.includes('youtube')) {
        var ext = inf.split("?v=");
        act = ext[1];
    } else {
        act = inf;
    }
    //return res.status(200).send("Check console.")
    var url = `https://www.youtube.com/embed/${act}`;
    var data = await fetch(url);
    var text = await data.text();
    if(query.includes('youtube')) {
        //<video tabindex="-1" class="video-stream html5-main-video" style="width: 932px; height: 524px; left: 0px; top: 0px;" controlslist="nodownload" src="blob:https://www.youtube.com/7718a0da-481f-4065-9302-ca99389ece72"></video>
        //console.log(elements);
    }
    res.status(200).send(text);
})


module.exports = index;