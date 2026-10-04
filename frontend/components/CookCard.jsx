import React from 'react';
import {distanceLabel} from '../lib/location.js';
import {Star,ChevronRight} from 'lucide-react';
export function CookCard({cook,search,location,onOpen}) {return <button className="cook-card" onClick={onOpen}><img src={cook.image} alt={`Cook at ${cook.name}`} loading="lazy"/><div><h3>{cook.name}</h3><p className="cook-speciality">{cook.speciality}</p><p className="cook-story">“{cook.story}”</p><span><Star size={13} fill="currentColor"/>{cook.rating}<b> · </b>{cook.area}<b> · </b>{distanceLabel(cook,search)}</span></div><ChevronRight size={18}/></button>;}
