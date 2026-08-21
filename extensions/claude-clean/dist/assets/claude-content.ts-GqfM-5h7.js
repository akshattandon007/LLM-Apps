import{t as p}from"./local-transform-_g-oIdXz.js";const r="claude-clean-btn",c="claude-clean-toast";function u(n){if(n.querySelector(`#${r}`))return;const t=document.createElement("button");t.id=r,t.textContent="Clean with Claude Clean",t.style.cssText=`
    position: absolute;
    bottom: 8px;
    right: 8px;
    z-index: 9999;
    background: #4F46E5;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    cursor: pointer;
    opacity: 0.9;
    transition: opacity 0.2s;
  `,t.addEventListener("mouseenter",()=>{t.style.opacity="1"}),t.addEventListener("mouseleave",()=>{t.style.opacity="0.9"}),t.addEventListener("click",()=>{const e=n.closest('[class*="font-claude"]')||n.closest('[class*="message"]')||n.closest('[class*="conversation-turn"]'),o=(e==null?void 0:e.querySelector('[class*="font-claude"]'))||(e==null?void 0:e.querySelector('[class*="whitespace-pre-wrap"]'));let s="";if(o!=null&&o.textContent?s=o.textContent:s=n.textContent||"",s.trim()){const i=p(s);x(i.transformed)}}),n.style.position="relative",n.appendChild(t)}function x(n){const t=document.getElementById(c);t&&t.remove();const e=document.createElement("div");e.id=c,e.style.cssText=`
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 99999;
    max-width: 380px;
    max-height: 300px;
    overflow-y: auto;
    background: #1F2937;
    color: #F3F4F6;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 13px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.5;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
  `;const o=document.createElement("button");o.textContent="Copy",o.style.cssText=`
    background: #4F46E5;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    cursor: pointer;
    margin-bottom: 8px;
  `,o.addEventListener("click",()=>{navigator.clipboard.writeText(n),o.textContent="Copied!",setTimeout(()=>o.remove(),1500)});const s=document.createElement("button");s.innerHTML="&times;",s.style.cssText=`
    background: transparent;
    color: #9CA3AF;
    border: none;
    font-size: 18px;
    cursor: pointer;
    float: right;
    line-height: 1;
  `,s.addEventListener("click",()=>e.remove());const i=document.createElement("div");i.textContent="Claude Clean",i.style.cssText=`
    font-weight: 600;
    color: #818CF8;
    margin-bottom: 6px;
  `;const d=document.createElement("div");d.textContent=n,e.appendChild(s),e.appendChild(i),e.appendChild(o),e.appendChild(d),document.body.appendChild(e),setTimeout(()=>{var a;document.getElementById(c)&&((a=document.getElementById(c))==null||a.remove())},3e4)}function l(){new MutationObserver(()=>{document.querySelectorAll('[class*="font-claude"], [class*="whitespace-pre-wrap"], [class*="prose"]').forEach(e=>{e instanceof HTMLElement&&!e.querySelector(`#${r}`)&&(e.textContent||"").length>80&&u(e)})}).observe(document.body,{childList:!0,subtree:!0})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",l):l();
