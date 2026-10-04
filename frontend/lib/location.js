export const SEARCH_RADIUS_KM=15;
export function distanceKm(a,b){if(!a||!b)return Infinity;const rad=x=>x*Math.PI/180;const dlat=rad(b.lat-a.lat),dlon=rad(b.lon-a.lon);const n=Math.sin(dlat/2)**2+Math.cos(rad(a.lat))*Math.cos(rad(b.lat))*Math.sin(dlon/2)**2;return 6371*2*Math.atan2(Math.sqrt(n),Math.sqrt(Math.max(0,1-n)));}
export function listingDistance(listing,search){return search.coordinates?distanceKm(search.coordinates,listing.coordinates):listing.distances[search.location]??Infinity;}
export function distanceLabel(listing,search){const km=listingDistance(listing,search);return Number.isFinite(km)?`${km.toFixed(1)} km`:listing.area;}
