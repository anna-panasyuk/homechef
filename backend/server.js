import express from 'express';
import { app } from './app.js';
app.use(express.static('dist/client'));
app.get(['/', '/how-it-works', '/our-mission', '/become-a-cook'], (_req,res)=>res.sendFile('index.html',{root:'dist/client'}));
app.listen(Number(process.env.PORT)||4173,'0.0.0.0',()=>console.log('HomeChef server ready'));
