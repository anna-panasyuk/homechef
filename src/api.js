// Browser stand-in for the Express /api routes in backend/routes/catalog.js (no server on Lovable).
import {catalogRepository} from '../backend/repositories/catalogRepository.js';
import {searchLocations} from '../backend/services/locationSearch.js';
const nativeFetch=window.fetch.bind(window);
const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}});
window.fetch=async(input,init)=>{
 const url=new URL(typeof input==='string'?input:input.url,window.location.origin);
 if(url.origin!==window.location.origin||!url.pathname.startsWith('/api/'))return nativeFetch(input,init);
 if(url.pathname==='/api/catalog'){try{return json(await catalogRepository.getCatalog());}catch{return json({error:'Unable to load meals. Please try again.'},500);}}
 if(url.pathname==='/api/health')return json({status:'ok',mode:'demo'});
 if(url.pathname==='/api/locations'){
  const query=(url.searchParams.get('q')||'').trim();
  if(query.length<2||query.length>160)return json({error:'Enter a street, postcode, or city in Poland (2–160 characters).'},400);
  // Browsers can't set User-Agent, so call Nominatim without custom headers.
  try{return json({results:await searchLocations(query,(u,o)=>nativeFetch(u,{signal:init?.signal||o.signal}))});}
  catch(e){if(e.name==='AbortError')throw e;return json({error:e.status?e.message:'Address search is unavailable right now. Please try again.'},e.status||503);}
 }
 return json({error:'Endpoint not found'},404);
};
