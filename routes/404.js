const express = require('express');

const index = express.Router();

const testCookies = require('../src/helpers/testCookies.js');

index.get('/', async (req, res, next) => { //This becomes /*
    var cookieOK = testCookies(req, res);
    var data = await req.appendData;
    var uri = await data.where;
    return res.cookie("error", `Not Found - ${uri}`).render("404.ejs", {x: cookieOK});
})
module.exports = index;