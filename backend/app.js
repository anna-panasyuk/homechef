import express from 'express';
import {catalogRouter} from './routes/catalog.js';
export const app = express();
app.disable('x-powered-by');
app.use(express.json({limit:'16kb'}));
app.use('/api',catalogRouter);
app.use('/api',(_req,res)=>res.status(404).json({error:'Endpoint not found'}));
app.use((err,_req,res,_next)=>{console.error(err);res.status(500).json({error:'Unable to load meals. Please try again.'});});
