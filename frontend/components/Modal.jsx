import React,{useEffect,useRef} from 'react';
import {X} from 'lucide-react';
export function Modal({title,onClose,children}) {
 const ref=useRef(null);
 useEffect(()=>{const d=ref.current;d.showModal();return ()=>{d.close();};},[]);
 return <dialog ref={ref} className="modal" aria-labelledby="modal-title" onCancel={onClose} onClick={e=>{if(e.target===e.currentTarget)onClose();}}><button type="button" className="icon-button close" aria-label="Close dialog" onClick={onClose}><X size={20}/></button><h2 id="modal-title">{title}</h2>{children}</dialog>;
}
