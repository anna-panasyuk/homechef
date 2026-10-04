import {searchLocations} from '../services/locationSearch.js';
import { Router } from 'express';
import { catalogRepository } from '../repositories/catalogRepository.js';
export const catalogRouter = Router();
catalogRouter.get('/catalog', async (_req,res,next) => { try {res.json(await catalogRepository.getCatalog());} catch (e) {next(e);} });
catalogRouter.get('/health', (_req,res) => res.json({status:'ok',mode:'demo'}));
catalogRouter.get('/locations', async (req,res) => {
 const query=typeof req.query.q==='string'?req.query.q.trim():'';
 if(query.length<2||query.length>160)return res.status(400).json({error:'Enter a street, postcode, or city in Poland (2–160 characters).'});
 try{res.json({results:await searchLocations(query)});}catch(e){res.status(e.status||503).json({error:e.status?e.message:'Address search is unavailable right now. Please try again.'});}
});
