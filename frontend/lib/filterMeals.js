import {listingDistance,SEARCH_RADIUS_KM} from './location.js';
export function filterMeals(meals,search,filters,sort) {
 const term=search.term.trim().toLowerCase();
 const result=meals.filter(m=>(!term || [m.name,m.cuisine,m.kitchen].some(v=>v.toLowerCase().includes(term))) && listingDistance(m,search)<=SEARCH_RADIUS_KM && (!search.date || m.availableDates.includes(search.date)) && (search.time==='any' || (Number(search.time)*60>=m.start && Number(search.time)*60<=m.end)) && (!filters.includes('Vegetarian')||m.vegetarian) && (!filters.includes('Under 30 zł')||m.price<30) && (!filters.includes('Top rated')||m.rating>=4.9) && (!filters.includes('Pickup')||m.pickup));
 return result.sort(sort==='price'?(a,b)=>a.price-b.price:sort==='rating'?(a,b)=>b.rating-a.rating:sort==='distance'?(a,b)=>listingDistance(a,search)-listingDistance(b,search):(a,b)=>meals.indexOf(a)-meals.indexOf(b));
}
