import React from 'react';
import {dateLabel,todayInPoland} from '../../shared/dates.js';
import {distanceLabel} from '../lib/location.js';
import {Heart,Clock,Star} from 'lucide-react';
export function MealCard({meal,date,search,location,saved,onSave,onOpen}) {
 return <article className="meal-card"><div className="meal-photo"><button className="photo-open" aria-label={`View ${meal.name}`} onClick={onOpen}><img src={meal.image} alt={meal.name} loading="lazy"/></button><span className="veg-mark" aria-label="Vegetarian"><i/></span><button className={`heart ${saved?'saved':''}`} aria-label={`${saved?'Remove':'Save'} ${meal.name} ${saved?'from':'to'} favourites`} aria-pressed={saved} onClick={onSave}><Heart size={20} fill={saved?'currentColor':'none'}/></button></div><div className="meal-body"><div className="meal-title"><button onClick={onOpen}>{meal.name}</button><strong>{meal.price} zł</strong></div><p className="kitchen"><img className="cook-avatar" src={meal.cookImage} alt={meal.cook} loading="lazy"/>{meal.kitchen}</p><p className="rating"><Star size={14} fill="currentColor"/><strong>{meal.rating}</strong><span>({meal.reviews})</span></p><div className="pickup"><p><Clock size={13}/>{dateLabel(date||meal.availableDates.find(d=>d>todayInPoland())||meal.availableDates[0])} · {meal.time}</p><span>Pickup · {distanceLabel(meal,search)}</span></div></div></article>;
}
