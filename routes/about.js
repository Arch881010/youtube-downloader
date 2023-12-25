const express = require('express');

const index = express.Router();

const testCookies = require('../src/helpers/testCookies.js');

index.get('/', (req, res, next) => { //This becomes /about
    var cookieOK = testCookies(req, res);

    return res.cookie("where", "about").render("about.ejs", {x: cookieOK});
})

module.exports = index;