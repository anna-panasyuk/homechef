export const todayInPoland = () => new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Warsaw',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
export function addDays(date,count){const d=new Date(`${date}T12:00:00Z`);d.setUTCDate(d.getUTCDate()+count);return d.toISOString().slice(0,10);}
export function dateLabel(date){if(!date)return 'Any date';if(date===todayInPoland())return 'Today';if(date===addDays(todayInPoland(),1))return 'Tomorrow';return new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(`${date}T12:00:00Z`));}
export function hourLabel(hour){return `${hour===12?12:hour%12} ${hour<12?'AM':'PM'}`;}
