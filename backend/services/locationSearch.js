// Explicit searches only; no autocomplete. Low-volume demo, switch provider here for scale.
const cache=new Map();let nextRequestAt=0;
export function mapPlace(item){
 const a=item.address||{},lat=Number(item.lat),lon=Number(item.lon);
 if(a.country_code!=='pl'||!Number.isFinite(lat)||!Number.isFinite(lon))return null;
 const city=a.city||a.town||a.village||a.municipality||a.county||'',street=a.road||a.pedestrian||a.residential||'',postcode=a.postcode||'';
 const label=[street?`${street}${a.house_number?' '+a.house_number:''}`:item.name||city,city].filter((v,i,arr)=>v&&arr.indexOf(v)===i).join(', ')||item.display_name;
 return {id:String(item.place_id),label,city,postcode,lat,lon,detail:[postcode,a.state,'Poland'].filter(Boolean).join(' · ')};
}
export async function searchLocations(query,fetcher=fetch){
 const key=query.trim().toLocaleLowerCase('pl');const previous=cache.get(key);
 if(previous&&previous.expires>Date.now())return previous.results;
 if(Date.now()<nextRequestAt){const e=new Error('Please wait a moment before searching again.');e.status=429;throw e;}
 nextRequestAt=Date.now()+1100;
 const url=new URL('https://nominatim.openstreetmap.org/search');
 url.search=new URLSearchParams({format:'jsonv2',countrycodes:'pl',addressdetails:'1',limit:'6','accept-language':'en,pl'}).toString();
 if(/^\d{2}-?\d{3}$/.test(key))url.searchParams.set('postalcode',key.replace(/^(\d{2})(\d{3})$/,'$1-$2'));
 else url.searchParams.set('q',query.trim());
 const response=await fetcher(url,{headers:{'User-Agent':'HomeChef-Demo/1.0 (https://homechef-india.testhelper4521.chatgpt.site)','Accept':'application/json'},signal:AbortSignal.timeout(12000)});
 if(!response.ok){const e=new Error('Address search is unavailable right now. Please try again.');e.status=503;throw e;}
 const body=await response.json();if(!Array.isArray(body))throw Error('Invalid address response');
 const results=body.map(mapPlace).filter(Boolean);
 if(cache.size>=200)cache.delete(cache.keys().next().value);
 cache.set(key,{results,expires:Date.now()+86400000});return results;
}
