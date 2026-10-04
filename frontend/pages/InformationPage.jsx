import React from 'react';
const pages={
 '/how-it-works':{title:'How it works',intro:'A homemade meal, close to you.',body:'Find meals in your area, get to know the cook, and choose a pickup time that suits you.'},
 '/our-mission':{title:'Our mission',intro:'Every kitchen holds a possibility.',body:'We connect customers directly with women who cook from home, helping everyday cooking skills become a source of independent income.'},
 '/become-a-cook':{title:'Become a cook',intro:'Your cooking. Your opportunity.',body:'Share the food you love to cook, reach customers in your community, and earn from your home kitchen.'}
};
export function InformationPage({path}){const page=pages[path];return <main className="information-page container"><a className="back-home" href="/">Back to HomeChef</a><p className="page-eyebrow">{page.title}</p><h1>{page.intro}</h1><p className="page-intro">{page.body}</p>{path==='/become-a-cook'&&<p className="page-note">Partner registration is coming soon.</p>}</main>;}
export const informationPaths=Object.keys(pages);
