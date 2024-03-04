const express = require('express');

const index = express.Router();

require('dotenv').config()

var guiurl = process.env['guiurl'] ?? "http://127.0.0.1:3055/"
var apiurl = process.env['apiurl'] ?? "http://127.0.0.1:3056/" 
var urls = {
    'guiurl': guiurl,
    'apiurl': apiurl
};

const testCookies = require('../src/helpers/testCookies.js');

index.get('/', async (req, res, next) => { //This becomes /login

    var {user, password} = req.query;

    if(user && password && (user != undefined && password != null) && (password != undefined && password != null)) {

        var data = await fetch(`${urls.apiurl}/user/retrive`);
        res.send(await data.text())
        return; res.cookie("user", user);

    }

    var cookieOK = testCookies(req, res);

    return res.cookie("where", "about").render("login.ejs", {x: cookieOK});
})



module.exports = index;